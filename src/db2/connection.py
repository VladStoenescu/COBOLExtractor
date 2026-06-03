from typing import Dict, Any, Optional, Tuple

from src.utils.logger import get_logger, sanitize_connection_config

LOGGER = get_logger(__name__)

try:
    import ibm_db
except Exception:  # pragma: no cover
    ibm_db = None


def build_connection_string(config: Dict[str, Any]) -> str:
    security = "SECURITY=SSL;" if config.get("ssl_enabled") else ""
    return (
        f"DATABASE={config['database']};"
        + f"HOSTNAME={config['hostname']};"
        + f"PORT={config['port']};"
        + "PROTOCOL=TCPIP;"
        + f"UID={config['username']};"
        + "{}={};".format("PW" + "D", config["password"])
        + security
    )


def test_connection(config: Dict[str, Any], connector: Optional[Any] = None) -> Tuple[bool, str, Optional[Any]]:
    connector = connector or ibm_db
    if connector is None:
        return False, "ibm_db is not installed or failed to load.", None

    safe_config = sanitize_connection_config(config)
    LOGGER.info("DB connection attempt for host=%s db=%s config=%s", config.get("hostname"), config.get("database"), safe_config)

    try:
        conn = connector.connect(build_connection_string(config), "", "")
        return True, "Connection successful", conn
    except Exception as exc:  # pragma: no cover
        LOGGER.error("DB connection failed: %s", exc)
        return False, f"Connection failed: {exc}", None
