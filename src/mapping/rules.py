import re


def normalize_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())
