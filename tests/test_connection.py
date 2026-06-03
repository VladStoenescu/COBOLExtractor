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
    assert "******;" in conn_str
    assert "SECURITY=SSL;" not in conn_str
    # Verify default connection reliability parameters are included
    assert "ConnectTimeout=30;" in conn_str
    assert "KeepAlive=1;" in conn_str


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


def test_build_connection_string_with_custom_timeout():
    """Test custom connect timeout"""
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "connect_timeout": 60,
    }
    conn_str = build_connection_string(config)
    assert "ConnectTimeout=60;" in conn_str


def test_build_connection_string_with_keepalive_disabled():
    """Test with KeepAlive disabled"""
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "keepalive": False,
    }
    conn_str = build_connection_string(config)
    assert "KeepAlive=1;" not in conn_str


def test_build_connection_string_rejects_missing_or_empty_credentials():
    """Missing or empty credentials should raise ValueError"""
    # Both missing
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_connection_string(config)
    
    # Only username
    config_no_password = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_connection_string(config_no_password)
    
    # Only password
    config_no_username = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "password": "testpass",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_connection_string(config_no_username)
    
    # Empty username
    config_empty_username = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "",
        "password": "testpass",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_connection_string(config_empty_username)
    
    # Empty password
    config_empty_password = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_connection_string(config_empty_password)


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
    assert "******;" in call_args[0]
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


def test_connection_retries_on_transient_errors():
    """Test that connection retries on transient errors like SQL30081N"""
    mock_connector = Mock()
    # First two attempts fail with SQL30081N, third succeeds
    mock_connector.connect = Mock(
        side_effect=[
            Exception("SQL30081N A communication error has been detected. ... *104*"),
            Exception("SQL30081N A communication error has been detected. ... *104*"),
            "mock_connection"
        ]
    )
    
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "connection_retries": 3,
        "retry_delay_seconds": 0.1,  # Short delay for testing
    }
    
    ok, message, conn = test_connection(config, connector=mock_connector)
    
    assert ok is True
    assert message == "Connection successful"
    assert conn == "mock_connection"
    # Verify connect was called 3 times (2 failures + 1 success)
    assert mock_connector.connect.call_count == 3


def test_connection_does_not_retry_non_transient_errors():
    """Test that connection does not retry on non-transient errors"""
    mock_connector = Mock()
    # Authentication error - should not retry
    mock_connector.connect = Mock(
        side_effect=Exception("SQL30082N Security processing failed")
    )
    
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "wrongpass",
        "connection_retries": 3,
        "retry_delay_seconds": 0.1,
    }
    
    ok, message, conn = test_connection(config, connector=mock_connector)
    
    assert ok is False
    assert "Connection failed:" in message
    assert conn is None
    # Verify connect was only called once (no retries)
    assert mock_connector.connect.call_count == 1


def test_connection_respects_max_retries():
    """Test that connection respects max_retries limit"""
    mock_connector = Mock()
    # Always fail with transient error
    mock_connector.connect = Mock(
        side_effect=Exception("SQL30081N A communication error has been detected. ... *104*")
    )
    
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "connection_retries": 2,
        "retry_delay_seconds": 0.1,
    }
    
    ok, message, conn = test_connection(config, connector=mock_connector)
    
    assert ok is False
    assert "Connection failed:" in message
    assert conn is None
    # Verify connect was called exactly 2 times
    assert mock_connector.connect.call_count == 2
