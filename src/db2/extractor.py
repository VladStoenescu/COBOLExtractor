from typing import Any, Iterable, List, Optional

import pandas as pd

from src.security.sql_validator import validate_where_clause


def extract_data(
    conn: Any,
    schema: str,
    table: str,
    columns: Optional[List[str]] = None,
    where_clause: str = "",
    limit: Optional[int] = None,
    batch_size: int = 1000,
) -> pd.DataFrame:
    validate_where_clause(where_clause)

    projected = ", ".join([f'"{c}"' for c in columns]) if columns else "*"
    query = f'SELECT {projected} FROM "{schema.upper()}"."{table.upper()}"'
    if where_clause:
        query += f" WHERE {where_clause}"
    if limit:
        query += f" FETCH FIRST {int(limit)} ROWS ONLY"

    cursor = conn.cursor()
    cursor.execute(query)

    column_names = [col[0] for col in cursor.description]
    chunks: List[pd.DataFrame] = []

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        chunks.append(pd.DataFrame(rows, columns=column_names))

    if not chunks:
        return pd.DataFrame(columns=column_names)
    return pd.concat(chunks, ignore_index=True)


def iter_batches(df: pd.DataFrame, batch_size: int) -> Iterable[pd.DataFrame]:
    for i in range(0, len(df), batch_size):
        yield df.iloc[i : i + batch_size]
