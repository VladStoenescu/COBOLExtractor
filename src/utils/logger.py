import logging
from pathlib import Path
from typing import Dict, Any


def get_logger(name: str = "cobol_extractor") -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler("logs/app.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def sanitize_connection_config(config: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = dict(config)
    if "password" in sanitized:
        sanitized["password"] = "***"
    return sanitized
