from src.copybook.parser import parse_copybook


def test_parse_copybook_basic_patterns_and_occurs():
    text = """
    01 CUSTOMER-RECORD.
       05 CUSTOMER-ID        PIC X(10).
       05 ACCOUNT-BALANCE    PIC S9(13)V99 COMP-3.
       05 OPEN-DATE          PIC 9(8).
       05 ITEM-CODE          PIC X(2) OCCURS 3 TIMES.
    """
    result = parse_copybook(text)

    names = [f["field_name"] for f in result["fields"]]
    assert "CUSTOMER-ID" in names
    assert "ACCOUNT-BALANCE" in names
    assert "OPEN-DATE" in names
    assert "ITEM-CODE_1" in names
    assert "ITEM-CODE_3" in names

    account = next(f for f in result["fields"] if f["field_name"] == "ACCOUNT-BALANCE")
    assert account["type"] == "decimal"
    assert account["signed"] is True
    assert account["decimals"] == 2


def test_parse_copybook_skips_redefines_with_warning():
    text = """
    01 ROOT.
      05 FIELD-A PIC X(10).
      05 FIELD-B REDEFINES FIELD-A PIC 9(10).
    """
    result = parse_copybook(text)

    assert any("REDEFINES" in w for w in result["warnings"])
    assert all(f["field_name"] != "FIELD-B" for f in result["fields"])
