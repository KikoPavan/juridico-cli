"""
Output quality checks beyond schema validation.

These checks enforce traceability and business rules that JSON Schema
cannot express (e.g., source_id must be non-empty, payload must not be empty).
"""

import re
from typing import Any, Dict, List, Tuple


DEFAULT_MIN_MEANINGFUL_CONTENT = 50

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*(?:\n|\Z)", re.DOTALL)
_STRUCTURED_LOCATOR_RE = re.compile(
    r"^\s*\[\[judicial_locator:[^\]]*\]\]\s*$", re.IGNORECASE
)
_TEXTUAL_LOCATOR_RES = (
    re.compile(
        r"^\s*(?:Processo\s+)?[\d.\-/]+(?:/[A-Z]{2})?,\s*Evento\s*\d+,"
        r"\s*[A-Z0-9_-]+,\s*P[áaä]gina\s*\d+\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:Processo|Evento|Título\s+do\s+Evento|Título|Descrição\s+do\s+Evento|"
        r"Data|Usuário|User|Papel\s+do\s+Usuário|Papel|Perfil|Sequência|Seq\.?|"
        r"Cód(?:igo)?\.?\s+do\s+documento|P[áaä]gina)\s*:\s*.+$",
        re.IGNORECASE,
    ),
)
_BOILERPLATE_RES = (
    re.compile(r"^\s*[Ff]l[s]?\.?\s*\d+\s*$"),
    re.compile(r"^\s*\d{1,4}\s*$"),
    re.compile(r"^\s*(?:TRIBUNAL\s+DE\s+JUSTI[CÇ]A|PODER\s+JUDICI[AÁ]RIO)", re.IGNORECASE),
    re.compile(r"^\s*(?:FORO|VARA|COMARCA)\s+", re.IGNORECASE),
    re.compile(r"^\s*Assinado\s+eletronicamente\s+por", re.IGNORECASE),
    re.compile(r"^\s*Para\s+conferir\s+o\s+original", re.IGNORECASE),
    re.compile(r"^\s*[-_=]{5,}\s*$"),
)


def _meaningful_content(text: str) -> str:
    without_frontmatter = _FRONTMATTER_RE.sub("", text, count=1)
    kept: list[str] = []
    for line in without_frontmatter.splitlines():
        if _STRUCTURED_LOCATOR_RE.fullmatch(line):
            continue
        if any(pattern.fullmatch(line) for pattern in _TEXTUAL_LOCATOR_RES):
            continue
        if any(pattern.search(line) for pattern in _BOILERPLATE_RES):
            continue
        kept.append(line)
    return "\n".join(kept)


def check_document_has_content(
    markdown: str, *, min_meaningful_chars: int = DEFAULT_MIN_MEANINGFUL_CONTENT
) -> bool:
    """Return whether Markdown reaches the configured useful-character threshold."""
    if min_meaningful_chars < 0:
        raise ValueError("min_meaningful_chars must be non-negative")
    meaningful = _meaningful_content(markdown)
    useful_chars = sum(1 for char in meaningful if not char.isspace())
    return useful_chars >= min_meaningful_chars


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
