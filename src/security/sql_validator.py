import re

FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|MERGE|CALL|EXECUTE|COMMIT|ROLLBACK)\b",
    re.IGNORECASE,
)


def validate_where_clause(where_clause: str) -> None:
    if not where_clause:
        return

    if ";" in where_clause:
        raise ValueError("WHERE clause must not contain ';'.")
    if "--" in where_clause or "/*" in where_clause or "*/" in where_clause:
        raise ValueError("WHERE clause must not contain SQL comments.")
    if FORBIDDEN_SQL.search(where_clause):
        raise ValueError("WHERE clause contains forbidden SQL keyword.")
