from typing import Dict, Any, Optional, Tuple
import os
import time

from src.utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import jaydebeapi
except Exception:  # pragma: no cover
    jaydebeapi = None


def _sanitize_error_message(message: str, password: str) -> str:
    """Remove password from error message if present"""
    if password and password in message:
        message = message.replace(password, "***")
    return message


def build_jdbc_url(config: Dict[str, Any]) -> str:
    """Build JDBC URL for DB2 connection.
    
    Format: jdbc:db2://{host}:{port}/{database}
    With SSL, additional connection properties are added.
    """
    # Validate credentials are provided (check for None or empty string)
    username = config.get("username")
    password = config.get("password")
    if not username or not password:
        raise ValueError("Username and password are required for DB2 connection")
    
    host = config.get("hostname")
    port = config.get("port")
    database = config.get("database")
    ssl_enabled = config.get("ssl_enabled", False)
    
    # Build base JDBC URL
    jdbc_url = f"jdbc:db2://{host}:{port}/{database}"
    
    # Add SSL and other connection properties if needed
    properties = []
    if ssl_enabled:
        properties.append("sslConnection=true")
    
    # Add connection reliability properties
    # These help prevent idle connections from being dropped
    connect_timeout = config.get("connect_timeout", 30)
    keepalive = config.get("keepalive", True)
    
    if connect_timeout:
        properties.append(f"loginTimeout={connect_timeout}")
    if keepalive:
        properties.append("enableClientAffinitiesList=1")
        properties.append("clientRerouteAlternateServerName=")
    
    if properties:
        jdbc_url += ":" + ";".join(properties) + ";"
    
    return jdbc_url


def _get_jdbc_jars(config: Dict[str, Any]) -> list:
    """Get JDBC driver JAR file paths from config or environment variables."""
    jar_path = config.get("jdbc_jar_path") or os.getenv("DB2_JDBC_JAR_PATH")
    license_jar_path = config.get("license_jar_path") or os.getenv("DB2_LICENSE_JAR_PATH")
    
    jars = []
    if jar_path:
        jars.append(jar_path)
    if license_jar_path:
        jars.append(license_jar_path)
    
    if not jars:
        raise ValueError(
            "JDBC driver JAR paths not provided. Set jdbc_jar_path and license_jar_path in config "
            "or DB2_JDBC_JAR_PATH and DB2_LICENSE_JAR_PATH environment variables."
        )
    
    # Verify JAR files exist and validate paths
    for jar in jars:
        # Normalize and validate path to prevent path traversal attacks
        normalized_jar = os.path.normpath(jar)
        # Check for suspicious path components
        if ".." in normalized_jar.split(os.sep):
            raise ValueError(f"Invalid JAR file path (path traversal detected): {jar}")
        if not os.path.exists(normalized_jar):
            raise FileNotFoundError(f"JDBC driver JAR file not found: {normalized_jar}")
    
    return jars


def test_connection(config: Dict[str, Any], connector: Optional[Any] = None) -> Tuple[bool, str, Optional[Any]]:
    """Test DB2 connection using JDBC via jaydebeapi.
    
    Args:
        config: Configuration dictionary with connection parameters
        connector: Optional connector module (for testing). Defaults to jaydebeapi.
    
    Returns:
        Tuple of (success, message, connection)
    """
    connector = connector or jaydebeapi
    if connector is None:
        return False, "jaydebeapi is not installed or failed to load.", None

    # Get retry configuration
    max_retries = config.get("connection_retries", 3)
    retry_delay = config.get("retry_delay_seconds", 2)
    password = config.get("password", "")
    username = config.get("username", "")
    
    last_error = None
    last_error_sanitized = None
    
    for attempt in range(max_retries):
        if attempt > 0:
            LOGGER.info("DB connection retry attempt %d/%d", attempt + 1, max_retries)
            time.sleep(retry_delay)
        else:
            LOGGER.info("DB connection attempt")

        try:
            # Build JDBC URL
            jdbc_url = build_jdbc_url(config)
            
            # Get JDBC driver JARs
            jdbc_jars = _get_jdbc_jars(config)
            
            # DB2 JDBC driver class
            driver_class = "com.ibm.db2.jcc.DB2Driver"
            
            # Connect using jaydebeapi
            # jaydebeapi.connect(jclassname, url, driver_args, jars)
            # driver_args can be [username, password] or a dictionary of properties
            conn = connector.connect(
                driver_class,
                jdbc_url,
                [username, password],
                jdbc_jars
            )
            
            if attempt > 0:
                LOGGER.info("DB connection successful after %d attempts", attempt + 1)
            return True, "Connection successful", conn
        except Exception as exc:  # pragma: no cover
            last_error = exc
            error_str = str(exc)
            # Sanitize error message to remove any password that might be present
            safe_error_str = _sanitize_error_message(error_str, password)
            last_error_sanitized = safe_error_str
            
            # Check if this is a transient error that we should retry
            # SQL30081N with error code 104 (connection reset) is retryable
            # Also retry on other common transient network errors
            # Use lowercase comparison for consistency
            error_lower = error_str.lower()
            is_retryable = any(code.lower() in error_lower for code in [
                "SQL30081N",  # Communication error
                "SQL1042C",   # Unexpected system error
                "SQL30108N",  # Connection failed
                "*104*",      # Connection reset by peer
                "connection reset",  # Generic connection reset
                "connection refused",  # Connection refused
            ])
            
            if not is_retryable or attempt == max_retries - 1:
                # Don't retry if not a transient error or if this was the last attempt
                LOGGER.error("DB connection failed: %s", safe_error_str)
                break
            else:
                LOGGER.warning("DB connection failed with retryable error (attempt %d/%d): %s", attempt + 1, max_retries, safe_error_str)
    
    # Use sanitized error message in return value to avoid leaking password
    return False, f"Connection failed: {last_error_sanitized or last_error}", None
