"""Unit tests for validation/ modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.validation.output_checks import (
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
