from typing import Dict, Any, Optional, Tuple

from src.utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import ibm_db
except Exception:  # pragma: no cover
    ibm_db = None


def build_connection_string(config: Dict[str, Any]) -> str:
    security = "SECURITY=SSL;" if config.get("ssl_enabled") else ""
    username = config.get("username", "")
    password = config.get("password", "")
    
    # Validate credentials are provided
    if not username or not password:
        raise ValueError("Username and password are required for DB2 connection")
    
    return (
        f"DATABASE={config['database']};"
        + f"HOSTNAME={config['hostname']};"
        + f"PORT={config['port']};"
        + "PROTOCOL=TCPIP;"
        + f"UID={username};"
        + f"PWD={password};"
        + security
    )


def test_connection(config: Dict[str, Any], connector: Optional[Any] = None) -> Tuple[bool, str, Optional[Any]]:
    connector = connector or ibm_db
    if connector is None:
        return False, "ibm_db is not installed or failed to load.", None

    LOGGER.info("DB connection attempt")

    try:
        conn = connector.connect(build_connection_string(config), "", "")
        return True, "Connection successful", conn
    except Exception as exc:  # pragma: no cover
        # Log error with exception details but without connection string
        LOGGER.error("DB connection failed: %s", str(exc))
        return False, f"Connection failed: {exc}", None
