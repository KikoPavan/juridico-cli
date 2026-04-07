"""
Output quality checks beyond schema validation.

These checks enforce traceability and business rules that JSON Schema
cannot express (e.g., source_id must be non-empty, payload must not be empty).
"""

from typing import Any, Dict, List, Tuple


def check_extraction_result(result: Dict) -> Tuple[bool, List[str]]:
    """
    Business-level checks on a collector's extraction result.
    Returns (passed, list_of_issues).
    """
    issues: List[str] = []

    if not result.get("source_id", "").strip():
        issues.append("source_id is missing or empty — traceability broken")

    if not result.get("job_id", "").strip():
        issues.append("job_id is missing or empty")

    status = result.get("status")
    if status not in ("ok", "partial", "failed"):
        issues.append(f"status '{status}' is not one of ok|partial|failed")

    payload = result.get("payload")
    if not payload:
        issues.append("payload is empty — collector produced no structured data")

    if status == "ok" and result.get("validation_errors"):
        issues.append("status is ok but validation_errors is non-empty — inconsistency")

    return (len(issues) == 0, issues)


def check_normalized_doc(doc: Dict) -> Tuple[bool, List[str]]:
    """
    Traceability checks on a converted document.
    Returns (passed, list_of_issues).
    """
    issues: List[str] = []

    if not doc.get("source_id", "").strip():
        issues.append("source_id is missing — cannot trace document origin")

    content = doc.get("content_md", "")
    if not content or len(content.strip()) < 10:
        issues.append("content_md is empty or too short — conversion may have failed")

    return (len(issues) == 0, issues)
