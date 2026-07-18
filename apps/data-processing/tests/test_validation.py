"""Unit tests for validation/ modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.validation.output_checks import (
    check_document_has_content,
    check_extraction_result,
    check_normalized_doc,
)
from data_processing.validation.contract_validation import (
    validate_normalized_doc,
    validate_ingestion_job,
    validate_extraction_result,
)


# --- output_checks ---

def test_check_extraction_result_valid():
    result = {
        "job_id": "j1",
        "collector": "proc",
        "source_id": "doc_001",
        "status": "ok",
        "payload": {"campo": "valor"},
    }
    ok, issues = check_extraction_result(result)
    assert ok, issues


def test_check_extraction_result_missing_source_id():
    result = {
        "job_id": "j1",
        "collector": "proc",
        "source_id": "",
        "status": "ok",
        "payload": {"x": 1},
    }
    ok, issues = check_extraction_result(result)
    assert not ok
    assert any("source_id" in i for i in issues)


def test_check_extraction_result_empty_payload():
    result = {
        "job_id": "j1",
        "collector": "proc",
        "source_id": "doc_001",
        "status": "ok",
        "payload": {},
    }
    ok, issues = check_extraction_result(result)
    assert not ok
    assert any("payload" in i for i in issues)


def test_check_normalized_doc_valid():
    doc = {
        "source_id": "doc_001",
        "content_md": "# Contrato\n\nClausula 1...",
    }
    ok, issues = check_normalized_doc(doc)
    assert ok, issues


def test_check_normalized_doc_empty_content():
    doc = {"source_id": "doc_001", "content_md": ""}
    ok, issues = check_normalized_doc(doc)
    assert not ok


def test_check_document_has_content_accepts_valid_legal_body():
    markdown = (
        "---\ndocument_type: peticao\n---\n"
        '[[judicial_locator: process_number="123", page="1"]]\n'
        "A parte requer a concessão da tutela porque demonstrou integralmente "
        "a probabilidade do direito alegado."
    )
    assert check_document_has_content(markdown)


def test_check_document_has_content_rejects_empty_document():
    assert not check_document_has_content("")


def test_check_document_has_content_rejects_locator_only_document():
    markdown = (
        "---\ndocument_type: separador\n---\n"
        '[[judicial_locator: process_number="123", event="4", page="1"]]\n'
        "Processo: 123\nEvento: 4\nSequência: 1\n"
    )
    assert not check_document_has_content(markdown)


def test_check_document_has_content_uses_custom_threshold():
    markdown = "conteúdo breve"
    assert check_document_has_content(markdown, min_meaningful_chars=10)
    assert not check_document_has_content(markdown, min_meaningful_chars=20)


def test_check_document_has_content_does_not_modify_input():
    markdown = "---\ntitle: Teste\n---\n[[judicial_locator: page=\"1\"]]\nTexto"
    original = markdown[:]
    check_document_has_content(markdown, min_meaningful_chars=1)
    assert markdown == original


def test_extractor_rejects_before_creating_llm_client(tmp_path, monkeypatch):
    from data_processing.extractor import DataExtractorApp, LLMClientFactory

    app = DataExtractorApp.__new__(DataExtractorApp)
    app.dirs = {
        "input_md_frontmatter": str(tmp_path / "frontmatter"),
        "input_clean": str(tmp_path / "clean"),
        "input_processed_fm_legacy": str(tmp_path / "legacy"),
        "extracted": str(tmp_path / "extracted"),
        "logs": str(tmp_path / "logs"),
    }
    for directory in app.dirs.values():
        Path(directory).mkdir(parents=True, exist_ok=True)

    input_file = Path(app.dirs["input_md_frontmatter"]) / "separator.md"
    input_file.write_text(
        "---\ndocument_type: separador\n---\n"
        '[[judicial_locator: process_number="123", event="4", page="1"]]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        LLMClientFactory,
        "create_client",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("LLM must not be called")),
    )

    assert app.run_extraction("extr-test", input_file.name) is None
    log_text = "".join(path.read_text(encoding="utf-8") for path in Path(app.dirs["logs"]).iterdir())
    assert "rejected: no_meaningful_content" in log_text


# --- contract_validation ---

def test_validate_normalized_doc_valid():
    doc = {
        "source_id": "doc_001",
        "source_path": "var/input/raw/doc.pdf",
        "content_md": "# Documento\n\nConteúdo jurídico.",
        "stage": "converted",
    }
    ok, errors = validate_normalized_doc(doc)
    assert ok, errors


def test_validate_normalized_doc_missing_required():
    doc = {"source_id": "doc_001"}
    ok, errors = validate_normalized_doc(doc)
    assert not ok
    assert len(errors) > 0


def test_validate_ingestion_job_valid():
    job = {
        "job_id": "job_001",
        "collector": "proc",
        "source_id": "doc_001",
        "content_md": "Texto processado.",
    }
    ok, errors = validate_ingestion_job(job)
    assert ok, errors


def test_validate_ingestion_job_invalid_collector():
    job = {
        "job_id": "job_001",
        "collector": "invalid_collector",
        "source_id": "doc_001",
        "content_md": "Texto.",
    }
    ok, errors = validate_ingestion_job(job)
    assert not ok


def test_validate_extraction_result_valid():
    result = {
        "job_id": "j1",
        "collector": "cad_obr",
        "source_id": "doc_001",
        "status": "ok",
        "payload": {"tipo": "escritura"},
    }
    ok, errors = validate_extraction_result(result)
    assert ok, errors
