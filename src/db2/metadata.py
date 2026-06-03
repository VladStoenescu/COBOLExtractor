from typing import Any, Dict, List


def _fetch_rows(conn: Any, query: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def get_schemas(conn: Any) -> List[str]:
    rows = _fetch_rows(conn, "SELECT RTRIM(SCHEMANAME) AS SCHEMA_NAME FROM SYSCAT.SCHEMATA ORDER BY SCHEMA_NAME")
    return [r["SCHEMA_NAME"] for r in rows]


def get_tables(conn: Any, schema: str) -> List[str]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT RTRIM(TABNAME) AS TABLE_NAME FROM SYSCAT.TABLES WHERE TABSCHEMA = ? AND TYPE = 'T' ORDER BY TABLE_NAME",
        (schema.upper(),),
    )
    return [r[0] for r in cursor.fetchall()]


def get_table_columns(conn: Any, schema: str, table: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT RTRIM(COLNAME) AS COLUMN_NAME, TYPENAME, LENGTH, SCALE, NULLS
        FROM SYSCAT.COLUMNS
        WHERE TABSCHEMA = ? AND TABNAME = ?
        ORDER BY COLNO
        """,
        (schema.upper(), table.upper()),
    )
    out = []
    for row in cursor.fetchall():
        out.append(
            {
                "column_name": row[0],
                "data_type": row[1],
                "length": row[2],
                "decimals": row[3],
                "nullable": row[4] == "Y",
            }
        )
    return out


def preview_table(conn: Any, schema: str, table: str, limit: int = 100) -> List[Dict[str, Any]]:
    return _fetch_rows(conn, f'SELECT * FROM "{schema.upper()}"."{table.upper()}" FETCH FIRST {int(limit)} ROWS ONLY')
