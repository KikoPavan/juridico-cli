import json
import re
from typing import Dict, Any, Optional

# Structured locator format regex: [[judicial_locator: key1="value1", key2="value2", ...]]
STRUCTURED_LOCATOR_RE = re.compile(r"\[\[judicial_locator:\s*(.*?)\s*\]\]", re.IGNORECASE)
ATTR_RE = re.compile(r'(\w+)\s*=\s*"((?:\\.|[^"\\])*)"')

# Legacy page markers regex
LEGACY_MARKER_RE = re.compile(r"\[\[Pág\.\s*(\d+)\]\]", re.IGNORECASE)
LEGACY_COMMENT_RE = re.compile(r"<!--\s*page\s*(\d+)(?:\s*:\s*\w+)?\s*-->", re.IGNORECASE)
LEGACY_FLS_MARKER_RE = re.compile(r"\bfls?\.?\s*(\d+)\b", re.IGNORECASE)

# Electronic locator header/footer formats
# e.g., "Processo 4000153-37.2026.8.26.0136/SP, Evento 43, CONTES1, Página 1"
# or ".0136/SP, Evento 43, CONTES1, Pägina 33"
TJSP_ELECTRONIC_RE = re.compile(
    r"(?:Processo\s+)?([\d\.\-/]*\d+[\d\.\-/A-Z]*),\s*Evento\s*(\d+),\s*([A-Z0-9_\-]+),\s*P[áaä]gina\s*(\d+)",
    re.IGNORECASE
)

# Flexible individual regexes
PROCESS_RE = re.compile(
    r"\bProcesso\s*(?:Digital)?\s*(?:nº|no)?:?\s*([\d\.\-/]+[A-Z]{0,2})\b",
    re.IGNORECASE
)
EVENT_RE = re.compile(
    r"\b(?:Evento|Ev\.?)\s*:?\s*(\d+)\b",
    re.IGNORECASE
)
EVENT_TITLE_RE = re.compile(
    r"\b(?:Título\s+do\s+Evento|Título|Descrição\s+do\s+Evento)\s*:\s*(.+?)(?=\n|$)",
    re.IGNORECASE,
)
DOC_CODE_RE = re.compile(
    r"\b(?:Cód(?:igo)?\.?\s*do\s*documento|Cód\.?\s*Doc\.?|Doc\.?)\s*:?\s*([A-Z0-9_\-]+)\b",
    re.IGNORECASE
)
PAGE_RE = re.compile(
    r"\bP[áaä]gina\s*:?\s*(\d+)\b",
    re.IGNORECASE
)
FLS_RE = re.compile(
    r"\bfls?\.?\s*(\d+)\b",
    re.IGNORECASE
)
SEQ_RE = re.compile(
    r"\b(?:Seq(?:uência)?\.?|seq)\s*:?\s*(\d+)\b",
    re.IGNORECASE
)
USER_RE = re.compile(
    r"\b(?:Usuário|User|Assinado\s+por)\s*:?\s*([A-Za-z0-9_\s\.\-À-ÿ]+?)(?=\s*-\s*|\s*,\s*|\n|$)",
    re.IGNORECASE
)
USER_ROLE_RE = re.compile(
    r"\b(?:Papel\s+do\s+Usuário|Papel|Perfil)\s*:\s*(.+?)(?=\n|$)",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:Data|Date)\s*:?\s*(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE
)

SEPARATOR_METADATA_LINE_RES = (
    TJSP_ELECTRONIC_RE,
    PROCESS_RE,
    EVENT_RE,
    EVENT_TITLE_RE,
    DOC_CODE_RE,
    PAGE_RE,
    FLS_RE,
    SEQ_RE,
    USER_RE,
    USER_ROLE_RE,
    DATE_RE,
)

_EPROC_SEPARATOR_HEADING = "PÁGINA DE SEPARAÇÃO"
_EPROC_GROUPED_LABELS = (
    "EVENTO:",
    "DATA:",
    "USUÁRIO:",
    "PROCESSO:",
    "SEQUÊNCIA EVENTO:",
)
_EPROC_EVENT_SUMMARY_RE = re.compile(r"^Evento\s+(\d+)\s*$", re.IGNORECASE)
_EPROC_DATE_VALUE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?$")
_EPROC_PROCESS_VALUE_RE = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/[A-Z]{2}$", re.IGNORECASE)
_EPROC_ROLE_SUFFIX_RE = re.compile(r"^(?P<user>.+)\s+-\s+(?P<role>[A-ZÀ-ÖØ-Ý][A-ZÀ-ÖØ-Ý ]+)$")


def _without_markdown_heading(line: str) -> str:
    return re.sub(r"^\s*#{1,6}\s*", "", line).strip()


def _find_grouped_eproc_separator(text: str) -> Optional[tuple[Dict[str, Any], int, int]]:
    """Find the conservative grouped-label eproc separator layout."""
    lines = text.splitlines(keepends=True)
    compact = [(index, line.strip()) for index, line in enumerate(lines) if line.strip()]

    for compact_start, (line_start, raw_heading) in enumerate(compact):
        if _without_markdown_heading(raw_heading).upper() != _EPROC_SEPARATOR_HEADING:
            continue

        cursor = compact_start + 1
        if cursor < len(compact) and "GERADA AUTOMATICAMENTE" in compact[cursor][1].upper():
            cursor += 1
        if cursor >= len(compact):
            continue

        event_match = _EPROC_EVENT_SUMMARY_RE.fullmatch(compact[cursor][1])
        if not event_match:
            continue
        cursor += 1

        candidate_labels = tuple(
            compact[cursor + offset][1].upper()
            for offset in range(len(_EPROC_GROUPED_LABELS))
            if cursor + offset < len(compact)
        )
        if candidate_labels != _EPROC_GROUPED_LABELS:
            continue
        cursor += len(_EPROC_GROUPED_LABELS)

        if cursor + 4 >= len(compact):
            continue
        values = [compact[cursor + offset][1] for offset in range(5)]
        event_title = _without_markdown_heading(values[0])
        event_date, event_user_role, process_number, sequence = values[1:]
        if (
            not event_title
            or not _EPROC_DATE_VALUE_RE.fullmatch(event_date)
            or not _EPROC_PROCESS_VALUE_RE.fullmatch(process_number)
            or not sequence.isdigit()
        ):
            continue

        user = event_user_role
        user_role = None
        role_match = _EPROC_ROLE_SUFFIX_RE.fullmatch(event_user_role)
        if role_match:
            user = role_match.group("user").strip()
            user_role = role_match.group("role").strip()

        meta: Dict[str, Any] = {
            "process_number": process_number,
            "event": event_match.group(1),
            "event_title": event_title,
            "date": event_date,
            "user": user,
            "sequence": sequence,
            "kind": "event_separator",
        }
        if user_role:
            meta["user_role"] = user_role

        line_end = compact[cursor + 4][0] + 1
        return meta, line_start, line_end

    return None


def structure_eproc_event_separator_markdown(text: str) -> str:
    """Enrich the first locator and rewrite a grouped eproc separator as key/value text."""
    found = _find_grouped_eproc_separator(text)
    if not found:
        return text

    meta, line_start, line_end = found
    lines = text.splitlines(keepends=True)

    for index in range(line_start):
        locator_match = STRUCTURED_LOCATOR_RE.fullmatch(lines[index].strip())
        if not locator_match:
            continue
        existing = parse_locator_text(lines[index]) or {}
        existing.update(meta)
        newline = "\n" if lines[index].endswith(("\n", "\r")) else ""
        lines[index] = format_locator(existing) + newline
        break

    rendered = [
        "# PÁGINA DE SEPARAÇÃO\n",
        f"Evento: {meta['event']}\n",
        f"Título do Evento: {meta['event_title']}\n",
        f"Data: {meta['date']}\n",
        f"Usuário: {meta['user']}\n",
    ]
    if meta.get("user_role"):
        rendered.append(f"Papel do Usuário: {meta['user_role']}\n")
    rendered.extend(
        [
            f"Processo: {meta['process_number']}\n",
            f"Sequência Evento: {meta['sequence']}\n",
        ]
    )
    lines[line_start:line_end] = rendered
    return "".join(lines)


def strip_judicial_metadata_text(text: str) -> str:
    """Remove locator/separator-only lines while preserving judicial body text."""
    body_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or STRUCTURED_LOCATOR_RE.fullmatch(stripped):
            continue
        if any(pattern.fullmatch(stripped) for pattern in SEPARATOR_METADATA_LINE_RES):
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip()


def parse_locator_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Parses a page marker line and extracts locator fields.
    Supports structured judicial_locator, legacy [[Pág. N]], <!-- page N -->, and fls. N formats.
    """
    text_strip = text.strip()
    
    # 1. Parse structured locator
    m = STRUCTURED_LOCATOR_RE.match(text_strip)
    if m:
        attrs = {}
        for key, val in ATTR_RE.findall(m.group(1)):
            attrs[key] = json.loads(f'"{val}"')
        return attrs

    # 2. Parse legacy marker format [[Pág. N]]
    m = LEGACY_MARKER_RE.match(text_strip)
    if m:
        return {"page": m.group(1)}

    # 3. Parse legacy comment format <!-- page N -->
    m = LEGACY_COMMENT_RE.match(text_strip)
    if m:
        return {"page": m.group(1)}

    # 4. Parse physical leaf fls. N format
    m = LEGACY_FLS_MARKER_RE.search(text_strip)
    if m:
        return {"page": m.group(1), "page_separation": f"fls. {m.group(1)}"}

    return None


def format_locator(meta: Dict[str, Any]) -> str:
    """
    Formats the metadata dictionary into a structured locator string:
    [[judicial_locator: key1="value1", key2="value2", ...]]
    """
    # Order of fields for clean formatting
    field_order = [
        "process_number",
        "event",
        "event_title",
        "document_code",
        "page",
        "page_separation",
        "date",
        "user",
        "user_role",
        "sequence",
        "kind",
    ]
    
    parts = []
    for field in field_order:
        val = meta.get(field)
        if val is not None and val != "":
            parts.append(f"{field}={json.dumps(str(val), ensure_ascii=False)}")
            
    # Include any other fields not in field_order
    for key, val in meta.items():
        if key not in field_order and val is not None and val != "":
            parts.append(f"{key}={json.dumps(str(val), ensure_ascii=False)}")
            
    return f"[[judicial_locator: {', '.join(parts)}]]"


def extract_judicial_metadata_from_text(text: str) -> Dict[str, Any]:
    """
    Scans raw text of a page to extract judicial metadata fields.
    """
    meta: Dict[str, Any] = {
        "process_number": None,
        "event": None,
        "event_title": None,
        "document_code": None,
        "page": None,
        "page_separation": None,
        "date": None,
        "user": None,
        "user_role": None,
        "sequence": None,
        "kind": None,
    }

    grouped_separator = _find_grouped_eproc_separator(text)
    if grouped_separator:
        grouped_meta = grouped_separator[0]
        for key in meta:
            if key in grouped_meta:
                meta[key] = grouped_meta[key]
    
    # Pre-parse lines to look for the TJSP electronic locator pattern
    lines = text.splitlines()
    for line in lines:
        line_strip = line.strip()
        m_tjsp = TJSP_ELECTRONIC_RE.search(line_strip)
        if m_tjsp:
            meta["process_number"] = m_tjsp.group(1)
            meta["event"] = m_tjsp.group(2)
            meta["document_code"] = m_tjsp.group(3)
            meta["page"] = m_tjsp.group(4)
            break
            
    # Flexible scan of the entire page for missing values
    # Process number
    if not meta["process_number"]:
        m = PROCESS_RE.search(text)
        if m:
            meta["process_number"] = m.group(1)
            
    # Event
    if not meta["event"]:
        m = EVENT_RE.search(text)
        if m:
            meta["event"] = m.group(1)

    # Event title
    m = EVENT_TITLE_RE.search(text)
    if m and not meta["event_title"]:
        meta["event_title"] = m.group(1).strip()
            
    # Document Code
    if not meta["document_code"]:
        m = DOC_CODE_RE.search(text)
        if m:
            meta["document_code"] = m.group(1)
            
    # Page
    if not meta["page"]:
        m = PAGE_RE.search(text)
        if m:
            meta["page"] = m.group(1)
            
    # Physical leaves (fls.)
    m_fls = FLS_RE.search(text)
    if m_fls:
        # Save the physical leaves (fls) reference
        meta["page_separation"] = f"fls. {m_fls.group(1)}"
        if not meta["page"]:
            meta["page"] = m_fls.group(1)
            
    # Sequence
    m = SEQ_RE.search(text)
    if m and not meta["sequence"]:
        meta["sequence"] = m.group(1)
        
    # User
    m = USER_RE.search(text)
    if m and not meta["user"]:
        meta["user"] = m.group(1).strip()

    # User role
    m = USER_ROLE_RE.search(text)
    if m and not meta["user_role"]:
        meta["user_role"] = m.group(1).strip()
        
    # Date
    m = DATE_RE.search(text)
    if m and not meta["date"]:
        dt_val = m.group(1)
        m_dmy = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", dt_val)
        if m_dmy:
            day, month, year = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
            if 1 <= month <= 12 and 1 <= day <= 31:
                time_part = dt_val[m_dmy.end():]
                meta["date"] = f"{year:04d}-{month:02d}-{day:02d}{time_part}"
            else:
                meta["date"] = dt_val
        else:
            meta["date"] = dt_val
        
    return meta
