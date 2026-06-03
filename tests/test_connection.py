import pytest
from unittest.mock import Mock

from src.db2.connection import build_connection_string, test_connection


def test_build_connection_string_includes_uid_and_pwd():
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "ssl_enabled": False,
    }
    conn_str = build_connection_string(config)
    assert "DATABASE=TESTDB;" in conn_str
    assert "HOSTNAME=localhost;" in conn_str
    assert "PORT=50000;" in conn_str
    assert "PROTOCOL=TCPIP;" in conn_str
    assert "UID=testuser;" in conn_str
    assert "PWD=testpass;" in conn_str
    assert "SECURITY=SSL;" not in conn_str


def test_build_connection_string_with_ssl():
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "ssl_enabled": True,
    }
    conn_str = build_connection_string(config)
    assert "SECURITY=SSL;" in conn_str


def test_build_connection_string_handles_empty_credentials():
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
    }
    conn_str = build_connection_string(config)
    assert "UID=;" in conn_str
    assert "PWD=;" in conn_str


def test_connection_passes_empty_strings_to_connector():
    """Test that credentials are in connection string, not passed separately"""
    mock_connector = Mock()
    mock_connector.connect = Mock(return_value="mock_connection")
    
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
    }
    
    ok, message, conn = test_connection(config, connector=mock_connector)
    
    assert ok is True
    assert message == "Connection successful"
    assert conn == "mock_connection"
    
    # Verify connect was called with connection string and empty strings
    mock_connector.connect.assert_called_once()
    call_args = mock_connector.connect.call_args[0]
    assert len(call_args) == 3
    assert "UID=testuser;" in call_args[0]
    assert "PWD=testpass;" in call_args[0]
    assert call_args[1] == ""
    assert call_args[2] == ""


def test_connection_handles_error():
    mock_connector = Mock()
    mock_connector.connect = Mock(side_effect=Exception("Connection error"))
    
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
    }
    
    ok, message, conn = test_connection(config, connector=mock_connector)
    
    assert ok is False
    assert "Connection failed:" in message
    assert conn is None
