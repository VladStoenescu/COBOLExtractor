import csv
import io
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from src.copybook.parser import parse_copybook
from src.copybook.validators import validate_parse_result
from src.db2.connection import test_connection
from src.db2.extractor import extract_data
from src.db2.metadata import get_schemas, get_tables, get_table_columns, preview_table
from src.export.csv_writer import default_filename
from src.mapping.mapper import auto_map_fields
from src.utils.logger import get_logger

LOGGER = get_logger(__name__)
SETTINGS = yaml.safe_load(Path("config/settings.yaml").read_text())
DEFAULT_FILENAME_SCHEMA = "TABLE"
DEFAULT_FILENAME_TABLE = "DATA"

st.set_page_config(page_title="COBOL Extractor", layout="wide")
st.title("COBOL Extractor")
st.caption("Extract DB2 table data using COBOL copybook definitions")

if "conn" not in st.session_state:
    st.session_state.conn = None
if "parse_result" not in st.session_state:
    st.session_state.parse_result = {"fields": [], "warnings": [], "errors": []}
if "mapping" not in st.session_state:
    st.session_state.mapping = {"mapped": [], "unmatched_db2": [], "unmatched_copybook": []}
if "extracted_df" not in st.session_state:
    st.session_state.extracted_df = pd.DataFrame()

steps = [
    "1. Connect to DB2",
    "2. Select Schema and Table",
    "3. Load Copybook",
    "4. Review Parsed Fields",
    "5. Map Fields",
    "6. Extract Data",
    "7. Download CSV",
]
st.sidebar.subheader("Workflow")
for step in steps:
    st.sidebar.write(f"- {step}")

with st.expander("1. Connect to DB2", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        hostname = st.text_input("Hostname")
        port = st.number_input("Port", min_value=1, max_value=65535, value=50000)
        database = st.text_input("Database name")
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        ssl_enabled = st.checkbox("SSL enabled", value=False)

    if st.button("Test connection"):
        ok, message, conn = test_connection(
            {
                "hostname": hostname,
                "port": port,
                "database": database,
                "username": username,
                "password": password,
                "ssl_enabled": ssl_enabled,
            }
        )
        if ok:
            st.session_state.conn = conn
            st.success(message)
            LOGGER.info("DB connection successful")
        else:
            st.error(message)

with st.expander("2. Select Schema and Table"):
    if st.session_state.conn is None:
        st.info("Connect to DB2 first.")
    else:
        schemas = get_schemas(st.session_state.conn)
        schema = st.selectbox("Schema", schemas) if schemas else None

        tables = get_tables(st.session_state.conn, schema) if schema else []
        table = st.selectbox("Table", tables) if tables else None

        if schema and table:
            metadata = get_table_columns(st.session_state.conn, schema, table)
            st.dataframe(pd.DataFrame(metadata), use_container_width=True)
            preview_limit = st.number_input("Preview rows", min_value=10, max_value=100, value=SETTINGS.get("preview_limit", 20))
            preview_data = preview_table(st.session_state.conn, schema, table, limit=preview_limit)
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

            st.session_state.schema = schema
            st.session_state.table = table
            st.session_state.table_columns = [m["column_name"] for m in metadata]

with st.expander("3. Load Copybook"):
    uploaded = st.file_uploader("Upload copybook", type=["cpy", "copybook", "txt"])
    pasted = st.text_area("Or paste copybook text")

    options = []
    copybook_folder = Path(SETTINGS.get("copybook_folder", "sample/copybooks"))
    if copybook_folder.exists():
        options = sorted([p.name for p in copybook_folder.glob("*") if p.is_file()])
    selected_file = st.selectbox("Or select from configured folder", [""] + options)

    if st.button("Parse copybook"):
        text = ""
        if uploaded is not None:
            text = uploaded.getvalue().decode("utf-8", errors="replace")
        elif pasted.strip():
            text = pasted
        elif selected_file:
            text = (copybook_folder / selected_file).read_text(encoding="utf-8", errors="replace")

        result = parse_copybook(text)
        issues = validate_parse_result(result)
        st.session_state.parse_result = result

        if issues:
            for issue in issues:
                st.error(issue)
        if result["warnings"]:
            for warning in result["warnings"]:
                st.warning(warning)
        if result["fields"]:
            st.success(f"Parsed {len(result['fields'])} fields")

with st.expander("4. Review Parsed Fields"):
    st.dataframe(pd.DataFrame(st.session_state.parse_result.get("fields", [])), use_container_width=True)
    if st.session_state.parse_result.get("fields"):
        st.download_button(
            "Download parser JSON",
            data=io.StringIO(pd.DataFrame(st.session_state.parse_result["fields"]).to_json(orient="records", indent=2)).getvalue(),
            file_name="parsed_copybook.json",
            mime="application/json",
        )

with st.expander("5. Map Fields"):
    copy_fields = st.session_state.parse_result.get("fields", [])
    table_columns = st.session_state.get("table_columns", [])

    if st.button("Auto-map fields") and copy_fields and table_columns:
        st.session_state.mapping = auto_map_fields(table_columns, copy_fields)

    mapping = st.session_state.mapping
    st.write("Mapped")
    st.dataframe(pd.DataFrame(mapping.get("mapped", [])), use_container_width=True)
    st.write("Unmatched DB2 columns", mapping.get("unmatched_db2", []))
    st.write("Unmatched copybook fields", mapping.get("unmatched_copybook", []))

with st.expander("6. Extract Data"):
    if st.session_state.conn is None or "schema" not in st.session_state or "table" not in st.session_state:
        st.info("Connect and select a table first.")
    else:
        limit = st.number_input("Row limit (0 = full)", min_value=0, value=1000)
        where_clause = st.text_input("Optional WHERE filter")
        batch_size = st.number_input("Batch size", min_value=100, max_value=50000, value=SETTINGS.get("default_batch_size", 1000))

        if st.button("Extract"):
            mapped_columns = [m["db2_column"] for m in st.session_state.mapping.get("mapped", [])]
            selected_columns = mapped_columns if mapped_columns else st.session_state.table_columns
            df = extract_data(
                st.session_state.conn,
                st.session_state.schema,
                st.session_state.table,
                columns=selected_columns,
                where_clause=where_clause,
                limit=None if limit == 0 else int(limit),
                batch_size=int(batch_size),
            )
            st.session_state.extracted_df = df
            st.success(f"Extracted {len(df)} rows")
            st.dataframe(df.head(100), use_container_width=True)

with st.expander("7. Download CSV"):
    df = st.session_state.extracted_df
    if df.empty:
        st.info("No extracted data yet.")
    else:
        separator = st.selectbox("Separator", [",", ";", "\t"])
        include_header = st.checkbox("Include header", value=True)
        quote_all = st.checkbox("Quote all fields", value=False)
        default_name = default_filename(
            st.session_state.get("schema", DEFAULT_FILENAME_SCHEMA),
            st.session_state.get("table", DEFAULT_FILENAME_TABLE),
        )
        file_name = st.text_input("File name", value=default_name)

        quoting = csv.QUOTE_ALL if quote_all else csv.QUOTE_MINIMAL
        csv_data = df.to_csv(index=False, sep=separator, header=include_header, quoting=quoting).encode("utf-8")
        st.download_button("Download CSV", data=csv_data, file_name=file_name, mime="text/csv")
