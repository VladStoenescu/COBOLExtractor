from datetime import datetime

import pandas as pd

from src.export.csv_writer import default_filename, write_csv


def test_default_filename_contains_schema_table_timestamp():
    dt = datetime(2026, 6, 3, 9, 15, 0)
    assert default_filename("customer", "master", dt) == "CUSTOMER_MASTER_20260603_091500.csv"


def test_write_csv_creates_file(tmp_path):
    df = pd.DataFrame([{"A": 1, "B": "x"}])
    output = write_csv(df, output_dir=str(tmp_path), filename="out.csv")
    assert (tmp_path / "out.csv").exists()
    assert "A,B" in (tmp_path / "out.csv").read_text()
