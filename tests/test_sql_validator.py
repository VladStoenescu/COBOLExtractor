import pytest

from src.security.sql_validator import validate_identifier, validate_where_clause


def test_validate_where_clause_allows_safe_expression():
    validate_where_clause("STATUS = 'A' AND ID > 10")


@pytest.mark.parametrize("clause", ["1=1; DROP TABLE X", "A=1 -- comment", "A=1 /*x*/", "DELETE FROM X"])
def test_validate_where_clause_rejects_unsafe_expression(clause):
    with pytest.raises(ValueError):
        validate_where_clause(clause)


def test_validate_identifier_allows_safe_names():
    validate_identifier("CUSTOMER_MASTER", "table")


@pytest.mark.parametrize("name", ["", "123TABLE", "TAB-NAME", "TABLE;DROP", "TAB NAME"])
def test_validate_identifier_rejects_invalid_names(name):
    with pytest.raises(ValueError):
        validate_identifier(name, "table")
