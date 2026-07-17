import pytest
from judicial_locator import (
    parse_locator_text,
    format_locator,
    extract_judicial_metadata_from_text
)


def test_parse_structured_locator():
    locator_str = '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1", page="2"]]'
    parsed = parse_locator_text(locator_str)
    assert parsed is not None
    assert parsed["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert parsed["event"] == "43"
    assert parsed["document_code"] == "CONTES1"
    assert parsed["page"] == "2"


def test_parse_legacy_pag():
    parsed = parse_locator_text("[[Pág. 15]]")
    assert parsed is not None
    assert parsed["page"] == "15"


def test_parse_legacy_comment():
    parsed = parse_locator_text("<!-- page 4 -->")
    assert parsed is not None
    assert parsed["page"] == "4"
    
    parsed_with_status = parse_locator_text("<!-- page 7 : scanned_no_ocr -->")
    assert parsed_with_status is not None
    assert parsed_with_status["page"] == "7"


def test_parse_legacy_fls():
    parsed = parse_locator_text("fls. 83")
    assert parsed is not None
    assert parsed["page"] == "83"
    assert parsed["page_separation"] == "fls. 83"


def test_format_locator():
    meta = {
        "process_number": "12345",
        "page": "3",
        "user": "kiko"
    }
    formatted = format_locator(meta)
    assert formatted == '[[judicial_locator: process_number="12345", page="3", user="kiko"]]'


def test_extract_judicial_metadata_tjsp():
    text = (
        "Núcleo Jurídico Bauru\n"
        "Processo 4000153-37.2026.8.26.0136/SP, Evento 43, CONTES1, Página 12\n"
        "Some random lawsuit text here.\n"
    )
    meta = extract_judicial_metadata_from_text(text)
    assert meta["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert meta["event"] == "43"
    assert meta["document_code"] == "CONTES1"
    assert meta["page"] == "12"


def test_extract_judicial_metadata_tjsp_umlaut():
    text = "Processo 4000153-37.2026.8.26.0136/SP, Evento 43, CONTES1, Pägina 33\n"
    meta = extract_judicial_metadata_from_text(text)
    assert meta["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert meta["event"] == "43"
    assert meta["document_code"] == "CONTES1"
    assert meta["page"] == "33"


def test_extract_judicial_metadata_flexible():
    text = (
        "Processo nº: 1111222-33.2024.8.26.0100\n"
        "Evento: 5\n"
        "Data: 17/07/2026 14:00:00\n"
        "Usuário: Francisco Carlos\n"
    )
    meta = extract_judicial_metadata_from_text(text)
    assert meta["process_number"] == "1111222-33.2024.8.26.0100"
    assert meta["event"] == "5"
    assert meta["date"] == "2026-07-17 14:00:00"
    assert meta["user"] == "Francisco Carlos"


def test_gemini_client_extract_pages_with_judicial_locator():
    import sys
    from pathlib import Path
    _project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(_project_root / "packages" / "shared-llm"))
    from gemini_client import GeminiLLMClient
    
    markdown_text = (
        '[[judicial_locator: process_number="123", page="1"]]\n'
        "Content page 1\n"
        '[[judicial_locator: process_number="123", page="2"]]\n'
        "Content page 2\n"
        '[[judicial_locator: process_number="123", page="3"]]\n'
        "Content page 3\n"
    )
    
    res = GeminiLLMClient._extract_pages_from_markdown(None, markdown_text, [2])
    assert "Content page 2" in res
    assert "Content page 1" not in res
    assert "Content page 3" not in res
