import pytest
from judicial_locator import (
    parse_locator_text,
    format_locator,
    extract_judicial_metadata_from_text,
    structure_eproc_event_separator_markdown,
    strip_judicial_metadata_text,
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


def test_extract_complete_eproc_separator_metadata():
    text = (
        "Processo: 4000153-37.2026.8.26.0136/SP\n"
        "Evento: 43\n"
        "Título do Evento: Contestação\n"
        "Data: 17/07/2026\n"
        "Usuário: Maria da Silva\n"
        "Papel do Usuário: Advogada\n"
        "Sequência: 1\n"
    )

    meta = extract_judicial_metadata_from_text(text)

    assert meta["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert meta["event"] == "43"
    assert meta["event_title"] == "Contestação"
    assert meta["date"] == "2026-07-17"
    assert meta["user"] == "Maria da Silva"
    assert meta["user_role"] == "Advogada"
    assert meta["sequence"] == "1"


def test_extract_partial_separator_does_not_invent_missing_fields():
    meta = extract_judicial_metadata_from_text(
        "Processo: 4000153-37.2026.8.26.0136/SP\nEvento: 43\nSequência: 2\n"
    )

    assert meta["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert meta["event"] == "43"
    assert meta["sequence"] == "2"
    assert meta["event_title"] is None
    assert meta["date"] is None
    assert meta["user"] is None
    assert meta["user_role"] is None


def test_extract_grouped_eproc_event_separator_metadata():
    text = (
        "# PÁGINA DE SEPARAÇÃO\n"
        "(Gerada automaticamente pelo sistema.)\n"
        "Evento 32\n"
        "Evento:\n"
        "Data:\n"
        "Usuário:\n"
        "Processo:\n"
        "Sequência Evento:\n"
        "# DETERMINADA A CITACAO\n"
        "27/04/2026 13:34:24\n"
        "J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO - MAGISTRADO\n"
        "4000153-37.2026.8.26.0136/SP\n"
        "32\n"
    )

    meta = extract_judicial_metadata_from_text(text)

    assert meta["event"] == "32"
    assert meta["event_title"] == "DETERMINADA A CITACAO"
    assert meta["date"] == "27/04/2026 13:34:24"
    assert meta["user"] == "J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO"
    assert meta["user_role"] == "MAGISTRADO"
    assert meta["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert meta["sequence"] == "32"


def test_structure_grouped_eproc_separator_enriches_first_locator():
    markdown = (
        '[[judicial_locator: event="32", page="1"]]\n\n'
        "# PÁGINA DE SEPARAÇÃO\n"
        "(Gerada automaticamente pelo sistema.)\n"
        "Evento 32\nEvento:\nData:\nUsuário:\nProcesso:\nSequência Evento:\n"
        "# DETERMINADA A CITACAO\n"
        "27/04/2026 13:34:24\n"
        "J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO - MAGISTRADO\n"
        "4000153-37.2026.8.26.0136/SP\n32\n"
        "Conteúdo jurídico posterior.\n"
    )

    structured = structure_eproc_event_separator_markdown(markdown)
    first_line = structured.splitlines()[0]
    parsed = parse_locator_text(first_line)

    assert parsed == {
        "process_number": "4000153-37.2026.8.26.0136/SP",
        "event": "32",
        "event_title": "DETERMINADA A CITACAO",
        "page": "1",
        "date": "27/04/2026 13:34:24",
        "user": "J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO",
        "user_role": "MAGISTRADO",
        "sequence": "32",
        "kind": "event_separator",
    }
    assert "Evento: 32" in structured
    assert "Título do Evento: DETERMINADA A CITACAO" in structured
    assert "Evento:\nData:" not in structured
    assert "Conteúdo jurídico posterior." in structured


def test_locator_round_trip_preserves_new_fields_and_escaping():
    meta = {
        "process_number": "4000153-37.2026.8.26.0136/SP",
        "event": "43",
        "event_title": 'Petição "urgente"',
        "date": "2026-07-17",
        "user": "Maria \\ Silva",
        "user_role": "Advogada",
        "sequence": "1",
    }

    formatted = format_locator(meta)
    parsed = parse_locator_text(formatted)

    assert formatted.index('event="43"') < formatted.index('event_title=')
    assert formatted.index('event_title=') < formatted.index('date="2026-07-17"')
    assert parsed == meta


def test_separator_only_text_has_no_judicial_body():
    text = (
        "Processo: 4000153-37.2026.8.26.0136/SP\n"
        "Evento: 43\n"
        "Título do Evento: Contestação\n"
        "Data: 17/07/2026\n"
        "Usuário: Maria da Silva\n"
        "Papel do Usuário: Advogada\n"
        "Sequência: 1\n"
    )
    assert strip_judicial_metadata_text(text) == ""


def test_separator_stripping_preserves_judicial_body():
    text = "Evento: 43\nA parte apresentou contestação tempestiva.\n"
    assert strip_judicial_metadata_text(text) == "A parte apresentou contestação tempestiva."


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
