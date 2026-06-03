import re
from typing import Dict, List, Tuple

from src.copybook.models import CopybookField

LINE_RE = re.compile(
    r"^\s*(\d{2})\s+([A-Z0-9-]+)(?:\s+REDEFINES\s+([A-Z0-9-]+))?(?:\s+PIC\s+([SX9V\(\)0-9]+))?(?:\s+(COMP-3|COMP|BINARY|DISPLAY))?(?:\s+OCCURS\s+(\d+)\s+TIMES)?\.?\s*$",
    re.IGNORECASE,
)


def _parse_pic(pic: str, usage: str) -> Tuple[str, int, int, bool]:
    normalized = pic.upper().replace("PIC", "").strip()
    signed = normalized.startswith("S")
    normalized = normalized[1:] if signed else normalized

    parts = normalized.split("V")
    int_part = parts[0]
    dec_part = parts[1] if len(parts) > 1 else ""

    def count_digits(part: str) -> int:
        total = 0
        for token in re.findall(r"9\((\d+)\)|9|X\((\d+)\)|X", part):
            n9, nx = token
            if n9:
                total += int(n9)
            elif nx:
                total += int(nx)
            else:
                total += 1
        return total

    length = count_digits(int_part) + count_digits(dec_part)
    decimals = count_digits(dec_part)

    if "X" in normalized:
        dtype = "alphanumeric"
    elif usage in {"COMP-3", "COMP", "BINARY"} or decimals:
        dtype = "decimal"
    else:
        dtype = "integer"

    return dtype, length, decimals, signed


def parse_copybook(text: str) -> Dict[str, List[Dict]]:
    fields: List[Dict] = []
    warnings: List[str] = []
    errors: List[str] = []

    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("*") or stripped.startswith("*>"):
            continue

        m = LINE_RE.match(stripped)
        if not m:
            warnings.append(f"Line {idx}: unsupported or unparseable syntax")
            continue

        level, field_name, redefines, pic, usage, occurs = m.groups()

        if level == "01" and not pic:
            continue

        if redefines:
            warnings.append(f"Line {idx}: field {field_name} uses REDEFINES and is skipped")
            continue

        if not pic:
            errors.append(f"Line {idx}: missing PIC clause for {field_name}")
            continue

        usage = (usage or "DISPLAY").upper()
        try:
            dtype, length, decimals, signed = _parse_pic(pic, usage)
        except Exception:
            warnings.append(f"Line {idx}: unsupported PIC format for {field_name}")
            continue

        field = CopybookField(
            level=level,
            field_name=field_name.upper(),
            pic=pic.upper(),
            usage=usage,
            type=dtype,
            length=length,
            decimals=decimals,
            signed=signed,
            occurs=int(occurs or 1),
            redefines=redefines or "",
        )
        fields.append(field.__dict__)

    return {"fields": flatten_occurs(fields), "warnings": warnings, "errors": errors}


def flatten_occurs(fields: List[Dict]) -> List[Dict]:
    flattened: List[Dict] = []
    for field in fields:
        occurs = int(field.get("occurs", 1) or 1)
        if occurs <= 1:
            flattened.append(field)
            continue

        for index in range(1, occurs + 1):
            clone = dict(field)
            clone["field_name"] = f"{field['field_name']}_{index}"
            clone["occurs_index"] = index
            flattened.append(clone)
    return flattened
