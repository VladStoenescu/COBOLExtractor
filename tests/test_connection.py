import pytest
from unittest.mock import Mock, patch
import os

from src.db2.connection import build_jdbc_url, test_connection as verify_connection, _get_jdbc_jars


def test_build_jdbc_url_basic():
    """Test basic JDBC URL construction"""
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "ssl_enabled": False,
    }
    jdbc_url = build_jdbc_url(config)
    assert jdbc_url.startswith("jdbc:db2://localhost:50000/TESTDB")


def test_build_jdbc_url_with_ssl():
    """Test JDBC URL with SSL enabled"""
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "ssl_enabled": True,
    }
    jdbc_url = build_jdbc_url(config)
    assert "jdbc:db2://localhost:50000/TESTDB" in jdbc_url
    assert "sslConnection=true" in jdbc_url


def test_build_jdbc_url_with_custom_timeout():
    """Test JDBC URL with custom connect timeout"""
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "connect_timeout": 60,
    }
    jdbc_url = build_jdbc_url(config)
    assert "loginTimeout=60" in jdbc_url


def test_build_jdbc_url_with_keepalive_disabled():
    """Test JDBC URL with KeepAlive disabled"""
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "testpass",
        "keepalive": False,
    }
    jdbc_url = build_jdbc_url(config)
    assert "enableClientAffinitiesList" not in jdbc_url


def test_build_jdbc_url_rejects_missing_or_empty_credentials():
    """Missing or empty credentials should raise ValueError"""
    # Both missing
    config = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_jdbc_url(config)
    
    # Only username
    config_no_password = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_jdbc_url(config_no_password)
    
    # Only password
    config_no_username = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "password": "testpass",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_jdbc_url(config_no_username)
    
    # Empty username
    config_empty_username = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "",
        "password": "testpass",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_jdbc_url(config_empty_username)
    
    # Empty password
    config_empty_password = {
        "database": "TESTDB",
        "hostname": "localhost",
        "port": 50000,
        "username": "testuser",
        "password": "",
    }
    with pytest.raises(ValueError, match="Username and password are required"):
        build_jdbc_url(config_empty_password)


def test_get_jdbc_jars_from_config():
    """Test getting JDBC JAR paths from config"""
    with patch('os.path.isfile', return_value=True):
        config = {
            "jdbc_jar_path": "/path/to/db2jcc.jar",
            "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
        }
        jars = _get_jdbc_jars(config)
        assert len(jars) == 2
        assert "/path/to/db2jcc.jar" in jars
        assert "/path/to/db2jcc_license_cisuz.jar" in jars


def test_get_jdbc_jars_from_env():
    """Test getting JDBC JAR paths from environment variables"""
    with patch('os.path.isfile', return_value=True):
        with patch.dict(os.environ, {
            'DB2_JDBC_JAR_PATH': '/env/path/db2jcc.jar',
            'DB2_LICENSE_JAR_PATH': '/env/path/db2jcc_license_cisuz.jar'
        }):
            config = {}
            jars = _get_jdbc_jars(config)
            assert len(jars) == 2
            assert "/env/path/db2jcc.jar" in jars
            assert "/env/path/db2jcc_license_cisuz.jar" in jars


def test_get_jdbc_jars_config_overrides_env():
    """Test that config values override environment variables"""
    with patch('os.path.isfile', return_value=True):
        with patch.dict(os.environ, {
            'DB2_JDBC_JAR_PATH': '/env/path/db2jcc.jar',
            'DB2_LICENSE_JAR_PATH': '/env/path/db2jcc_license_cisuz.jar'
        }):
            config = {
                "jdbc_jar_path": "/config/path/db2jcc.jar",
                "license_jar_path": "/config/path/db2jcc_license_cisuz.jar",
            }
            jars = _get_jdbc_jars(config)
            assert "/config/path/db2jcc.jar" in jars
            assert "/config/path/db2jcc_license_cisuz.jar" in jars


def test_get_jdbc_jars_raises_when_not_provided():
    """Test that ValueError is raised when JAR paths are not provided"""
    config = {}
    with pytest.raises(ValueError, match="JDBC driver JAR paths not provided"):
        _get_jdbc_jars(config)


def test_get_jdbc_jars_raises_when_file_not_found():
    """Test that FileNotFoundError is raised when JAR file doesn't exist"""
    config = {
        "jdbc_jar_path": "/nonexistent/db2jcc.jar",
        "license_jar_path": "/nonexistent/db2jcc_license_cisuz.jar",
    }
    with pytest.raises(FileNotFoundError, match="JDBC driver JAR file not found"):
        _get_jdbc_jars(config)


def test_connection_uses_jaydebeapi():
    """Test that connection uses jaydebeapi.connect with correct parameters"""
    mock_connector = Mock()
    mock_connector.connect = Mock(return_value="mock_connection")
    
    with patch('os.path.isfile', return_value=True):
        config = {
            "database": "TESTDB",
            "hostname": "localhost",
            "port": 50000,
            "username": "testuser",
            "password": "testpass",
            "jdbc_jar_path": "/path/to/db2jcc.jar",
            "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
        }
        
        ok, message, conn = verify_connection(config, connector=mock_connector)
        
        assert ok is True
        assert message == "Connection successful"
        assert conn == "mock_connection"
        
        # Verify connect was called with correct parameters
        mock_connector.connect.assert_called_once()
        call_args = mock_connector.connect.call_args[0]
        call_kwargs = mock_connector.connect.call_args[1] if mock_connector.connect.call_args[1] else {}
        
        # First arg should be driver class
        assert call_args[0] == "com.ibm.db2.jcc.DB2Driver"
        # Second arg should be JDBC URL
        assert "jdbc:db2://localhost:50000/TESTDB" in call_args[1]
        # Third arg should be [username, password]
        assert call_args[2] == ["testuser", "testpass"]
        # Fourth arg should be list of JARs
        assert len(call_args[3]) == 2


def test_connection_handles_error():
    """Test that connection handles errors properly"""
    mock_connector = Mock()
    mock_connector.connect = Mock(side_effect=Exception("Connection error"))
    
    with patch('os.path.isfile', return_value=True):
        config = {
            "database": "TESTDB",
            "hostname": "localhost",
            "port": 50000,
            "username": "testuser",
            "password": "testpass",
            "jdbc_jar_path": "/path/to/db2jcc.jar",
            "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
        }
        
        ok, message, conn = verify_connection(config, connector=mock_connector)
        
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
    
    with patch('os.path.isfile', return_value=True):
        config = {
            "database": "TESTDB",
            "hostname": "localhost",
            "port": 50000,
            "username": "testuser",
            "password": "testpass",
            "jdbc_jar_path": "/path/to/db2jcc.jar",
            "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
            "connection_retries": 3,
            "retry_delay_seconds": 0.1,  # Short delay for testing
        }
        
        ok, message, conn = verify_connection(config, connector=mock_connector)
        
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
    
    with patch('os.path.isfile', return_value=True):
        config = {
            "database": "TESTDB",
            "hostname": "localhost",
            "port": 50000,
            "username": "testuser",
            "password": "wrongpass",
            "jdbc_jar_path": "/path/to/db2jcc.jar",
            "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
            "connection_retries": 3,
            "retry_delay_seconds": 0.1,
        }
        
        ok, message, conn = verify_connection(config, connector=mock_connector)
        
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
    
    with patch('os.path.isfile', return_value=True):
        config = {
            "database": "TESTDB",
            "hostname": "localhost",
            "port": 50000,
            "username": "testuser",
            "password": "testpass",
            "jdbc_jar_path": "/path/to/db2jcc.jar",
            "license_jar_path": "/path/to/db2jcc_license_cisuz.jar",
            "connection_retries": 2,
            "retry_delay_seconds": 0.1,
        }
        
        ok, message, conn = verify_connection(config, connector=mock_connector)
        
        assert ok is False
        assert "Connection failed:" in message
        assert conn is None
        # Verify connect was called exactly 2 times
        assert mock_connector.connect.call_count == 2
