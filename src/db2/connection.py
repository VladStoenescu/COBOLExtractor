from typing import Dict, Any, Optional, Tuple
import re
import time

from src.utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import ibm_db
except Exception:  # pragma: no cover
    ibm_db = None


def _sanitize_error_message(message: str, password: str) -> str:
    """Remove password from error message if present"""
    if password and password in message:
        message = message.replace(password, "***")
    return message


def build_connection_string(config: Dict[str, Any]) -> str:
    security = "SECURITY=SSL;" if config.get("ssl_enabled") else ""
    
    # Validate credentials are provided (check for None or empty string)
    username = config.get("username")
    password = config.get("password")
    if not username or not password:
        raise ValueError("Username and password are required for DB2 connection")
    
    # Get optional connection parameters with defaults
    # KeepAlive helps prevent idle connections from being dropped by firewalls
    # ConnectTimeout ensures connection attempts don't hang indefinitely
    connect_timeout = config.get("connect_timeout", 30)
    keepalive = config.get("keepalive", True)
    
    return (
        f"DATABASE={config['database']};"
        + f"HOSTNAME={config['hostname']};"
        + f"PORT={config['port']};"
        + "PROTOCOL=TCPIP;"
        + f"UID={username};"
        + f"PWD={password};"
        + f"ConnectTimeout={connect_timeout};"
        + ("KeepAlive=1;" if keepalive else "")
        + security
    )


def test_connection(config: Dict[str, Any], connector: Optional[Any] = None) -> Tuple[bool, str, Optional[Any]]:
    connector = connector or ibm_db
    if connector is None:
        return False, "ibm_db is not installed or failed to load.", None

    # Get retry configuration
    max_retries = config.get("connection_retries", 3)
    retry_delay = config.get("retry_delay_seconds", 2)
    password = config.get("password", "")
    
    last_error = None
    
    for attempt in range(max_retries):
        if attempt > 0:
            LOGGER.info(f"DB connection retry attempt {attempt + 1}/{max_retries}")
            time.sleep(retry_delay)
        else:
            LOGGER.info("DB connection attempt")

        try:
            conn = connector.connect(build_connection_string(config), "", "")
            if attempt > 0:
                LOGGER.info(f"DB connection successful after {attempt + 1} attempts")
            return True, "Connection successful", conn
        except Exception as exc:  # pragma: no cover
            last_error = exc
            error_str = str(exc)
            # Sanitize error message to remove any password that might be present
            safe_error_str = _sanitize_error_message(error_str, password)
            
            # Check if this is a transient error that we should retry
            # SQL30081N with error code 104 (connection reset) is retryable
            # Also retry on other common transient network errors
            is_retryable = any(code in error_str for code in [
                "SQL30081N",  # Communication error
                "SQL1042C",   # Unexpected system error
                "SQL30108N",  # Connection failed
                "*104*",      # Connection reset by peer
            ])
            
            if not is_retryable or attempt == max_retries - 1:
                # Don't retry if not a transient error or if this was the last attempt
                LOGGER.error("DB connection failed: %s", safe_error_str)
                break
            else:
                LOGGER.warning(f"DB connection failed with retryable error (attempt {attempt + 1}/{max_retries}): {safe_error_str}")
    
    return False, f"Connection failed: {last_error}", None
