from src.mapping.mapper import auto_map_fields


def test_auto_map_fields_normalized():
    db2_columns = ["CUSTOMER_ID", "ACCOUNT_BALANCE", "EXTRA_COL"]
    copybook_fields = [
        {"field_name": "CUSTOMER-ID"},
        {"field_name": "ACCOUNT-BALANCE"},
        {"field_name": "UNMAPPED-FIELD"},
    ]

    result = auto_map_fields(db2_columns, copybook_fields)

    assert len(result["mapped"]) == 2
    assert "EXTRA_COL" in result["unmatched_db2"]
    assert "UNMAPPED-FIELD" in result["unmatched_copybook"]
