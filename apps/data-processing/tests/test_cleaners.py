"""Unit tests for cleaners/clean_legal_docs.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.cleaners.clean_legal_docs import LegalDocCleaner


def test_fix_encoding_replaces_artifacts():
    cleaner = LegalDocCleaner()
    result = cleaner.fix_encoding("Ã£o")
    assert result == "ão", f"Expected 'ão', got '{result}'"


def test_fix_typographic_ligatures_expands_all_supported_characters():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_typographic_ligatures("oﬁcial ﬂagrante oﬀício ﬃ ﬄ ﬅ ﬆ") == (
        "oficial flagrante offício ffi ffl st st"
    )


def test_fix_typographic_ligatures_preserves_other_unicode():
    cleaner = LegalDocCleaner()
    text = "AÇÃO, NÃO e § 1º"
    assert cleaner.fix_typographic_ligatures(text) == text


def test_fix_typographic_ligatures_is_idempotent():
    cleaner = LegalDocCleaner()
    once = cleaner.fix_typographic_ligatures("ﬁnal e ﬂagrante")
    assert cleaner.fix_typographic_ligatures(once) == once


def test_clean_document_expands_ligatures_before_encoding_fix(tmp_path):
    cleaner = LegalDocCleaner()
    src = tmp_path / "ligatures.md"
    src.write_text("A ﬁnalidade do oﬀício é o ﬂagrante.", encoding="utf-8")
    dst = tmp_path / "ligatures_clean.md"

    ok, msg = cleaner.clean_document(str(src), str(dst))

    assert ok, msg
    assert dst.read_text(encoding="utf-8") == "A finalidade do offício é o flagrante."


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


# ---------------------------------------------------------------------------
# Regression tests — fix-md-clean-markdown-preserve-legal-text
# Bug 1: "Ã": "Á" in fix_encoding corrupted valid Ã (U+00C3) → Á (U+00C1)
# Bug 2: trailing \s* in patterns_to_remove consumed \n, joining headings
# ---------------------------------------------------------------------------

def test_fix_encoding_does_not_corrupt_acao():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_encoding("AÇÃO DECLARATÓRIA") == "AÇÃO DECLARATÓRIA"


def test_fix_encoding_does_not_corrupt_nao():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_encoding("NÃO contém") == "NÃO contém"


def test_fix_encoding_does_not_corrupt_qualificacao():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_encoding("QUALIFICAÇÃO") == "QUALIFICAÇÃO"


def test_fix_encoding_does_not_corrupt_procuracao():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_encoding("PROCURAÇÃO") == "PROCURAÇÃO"


def test_fix_encoding_does_not_corrupt_pretensao():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_encoding("PRETENSÃO") == "PRETENSÃO"


def test_fix_encoding_preserves_page_marker():
    cleaner = LegalDocCleaner()
    assert cleaner.fix_encoding("[[Pág. 3]]") == "[[Pág. 3]]"


def test_remove_headers_footers_does_not_join_heading_after_comarca():
    cleaner = LegalDocCleaner()
    text = "DE CERQUEIRA CÉSAR – SP\nCOMARCA DE CERQUEIRA CÉSAR\n# DECLARATÓRIA DE NULIDADE"
    result = cleaner.remove_headers_footers(text)
    assert "SP# DECLARATÓRIA" not in result, repr(result)
    assert "# DECLARATÓRIA DE NULIDADE" in result


def test_remove_headers_footers_does_not_join_heading_after_foro():
    cleaner = LegalDocCleaner()
    text = "ajuizamento desta demanda declaratória.\nFORO DE CERQUEIRA CÉSAR\n# DA PROCURAÇÃO SEM PODERES ESPECIAIS"
    result = cleaner.remove_headers_footers(text)
    assert "declaratória.#" not in result, repr(result)
    assert "# DA PROCURAÇÃO SEM PODERES ESPECIAIS" in result


def test_clean_document_preserves_accents_end_to_end(tmp_path):
    cleaner = LegalDocCleaner()
    src = tmp_path / "peticao.md"
    src.write_text(
        "AÇÃO DECLARATÓRIA\nNÃO contém poderes\nDA QUALIFICAÇÃO\nDA PROCURAÇÃO\nPRETENSÃO declaratória\n",
        encoding="utf-8",
    )
    dst = tmp_path / "peticao_clean.md"
    ok, msg = cleaner.clean_document(str(src), str(dst))
    assert ok, msg
    content = dst.read_text(encoding="utf-8")
    assert "AÇÃO" in content, "AÇÃO foi corrompida"
    assert "NÃO" in content, "NÃO foi corrompido"
    assert "QUALIFICAÇÃO" in content, "QUALIFICAÇÃO foi corrompida"
    assert "PROCURAÇÃO" in content, "PROCURAÇÃO foi corrompida"
    assert "PRETENSÃO" in content, "PRETENSÃO foi corrompida"
    assert "AÇÁO" not in content, "Bug de acento ainda presente: AÇÁO"
    assert "NÁO" not in content, "Bug de acento ainda presente: NÁO"
