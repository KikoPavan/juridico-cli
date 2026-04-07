"""Unit tests for cleaners/clean_legal_docs.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.cleaners.clean_legal_docs import LegalDocCleaner


def test_fix_encoding_replaces_artifacts():
    cleaner = LegalDocCleaner()
    result = cleaner.fix_encoding("Ã£o")
    assert result == "ão", f"Expected 'ão', got '{result}'"


def test_remove_page_references():
    cleaner = LegalDocCleaner()
    text = "Texto relevante fls. 123 mais texto."
    result = cleaner.remove_headers_footers(text)
    assert "fls." not in result


def test_normalize_whitespace_collapses_blank_lines():
    cleaner = LegalDocCleaner()
    text = "linha1\n\n\n\nlinha2"
    result = cleaner.normalize_whitespace(text)
    assert "\n\n\n" not in result


def test_preserve_legal_structure_adds_newline_before_art():
    cleaner = LegalDocCleaner()
    text = "texto anterior Art. 5 continua"
    result = cleaner.preserve_legal_structure(text)
    assert "\n\nArt." in result


def test_clean_batch_empty_folder(tmp_path):
    cleaner = LegalDocCleaner()
    results = cleaner.clean_batch(str(tmp_path), str(tmp_path / "out"))
    assert results == []


def test_clean_document_roundtrip(tmp_path):
    cleaner = LegalDocCleaner()
    src = tmp_path / "doc.txt"
    src.write_text("Texto com fls. 10 e mais conteúdo jurídico relevante.", encoding="utf-8")
    dst = tmp_path / "doc_clean.txt"
    ok, msg = cleaner.clean_document(str(src), str(dst))
    assert ok, msg
    assert dst.exists()
    content = dst.read_text(encoding="utf-8")
    assert "fls." not in content
