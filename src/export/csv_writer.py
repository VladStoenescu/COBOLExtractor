from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


def default_filename(schema: str, table: str, dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now()
    return f"{schema.upper()}_{table.upper()}_{dt.strftime('%Y%m%d_%H%M%S')}.csv"


def write_csv(
    df: pd.DataFrame,
    output_dir: str = "exports",
    filename: Optional[str] = None,
    separator: str = ",",
    encoding: str = "utf-8",
    include_header: bool = True,
    quote_all_fields: bool = False,
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = filename or default_filename("EXTRACT", "RESULT")
    output_path = Path(output_dir) / filename

    quoting = 1 if quote_all_fields else 0
    df.to_csv(output_path, sep=separator, encoding=encoding, index=False, header=include_header, quoting=quoting)
    return str(output_path)
