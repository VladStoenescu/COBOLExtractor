from typing import Dict, List


def validate_parse_result(result: Dict) -> List[str]:
    issues = []
    if not result.get("fields"):
        issues.append("No parseable copybook fields found.")
    for error in result.get("errors", []):
        issues.append(error)
    return issues
