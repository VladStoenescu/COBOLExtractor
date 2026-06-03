from typing import Dict, List

from src.mapping.rules import normalize_name


def auto_map_fields(db2_columns: List[str], copybook_fields: List[Dict]) -> Dict:
    normalized_db = {normalize_name(col): col for col in db2_columns}
    normalized_copy = {normalize_name(f["field_name"]): f["field_name"] for f in copybook_fields}

    mapped = []
    unmatched_db = list(db2_columns)
    unmatched_copy = [f["field_name"] for f in copybook_fields]

    for key, db_col in normalized_db.items():
        copy_field = normalized_copy.get(key)
        if not copy_field:
            continue
        mapped.append(
            {
                "db2_column": db_col,
                "copybook_field": copy_field,
                "match_type": "auto",
                "excluded": False,
            }
        )
        unmatched_db.remove(db_col)
        if copy_field in unmatched_copy:
            unmatched_copy.remove(copy_field)

    return {"mapped": mapped, "unmatched_db2": unmatched_db, "unmatched_copybook": unmatched_copy}
