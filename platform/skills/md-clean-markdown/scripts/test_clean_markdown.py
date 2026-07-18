"""Tests for clean_markdown.py — unit and integration coverage for all cleaning rules."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from clean_markdown import (
    CleanStats,
    _extract_code_blocks,
    _fix_bullet,
    _fix_heading_space,
    _fix_horizontal_rule,
    _fix_trailing_whitespace,
    _remove_decorative_line,
    _recompose_hyphenated_words,
    _recompose_prose_lines,
    _restore_code_blocks,
    clean_lines,
)

FIXTURE_DIR = Path(__file__).parent / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# Artificial line recomposition unit tests
# ---------------------------------------------------------------------------

def test_recompose_hyphenated_word_with_lowercase_continuation():
    assert _recompose_hyphenated_words(["juris-\n", "prudência\n"]) == [
        "jurisprudência\n"
    ]


def test_recompose_hyphenated_words_preserves_semantic_hyphen():
    lines = ["relação jurídico-\n", "Processual autônoma\n"]
    assert _recompose_hyphenated_words(lines) == lines


def test_recompose_fragmented_prose_with_space():
    assert _recompose_prose_lines(
        ["A parte apresentou fundamento\n", "jurídico relevante.\n"]
    ) == ["A parte apresentou fundamento jurídico relevante.\n"]


def test_recompose_prose_does_not_cross_markdown_boundaries():
    lines = [
        "Texto sem pontuação\n",
        "\n",
        "continuação após parágrafo\n",
        "# heading\n",
        "continuação após heading\n",
        "- item\n",
        "continuação após lista\n",
        '[[judicial_locator: page="2"]]\n',
        "continuação após marcador\n",
        "__CODE_BLOCK_0__\n",
    ]
    assert _recompose_prose_lines(lines) == lines


def test_line_recomposition_is_idempotent_for_chained_fragments():
    lines = ["juris-\n", "pru-\n", "dência sem\n", "interrupção final.\n"]
    once = _recompose_prose_lines(_recompose_hyphenated_words(lines))
    twice = _recompose_prose_lines(_recompose_hyphenated_words(once))
    assert once == ["jurisprudência sem interrupção final.\n"]
    assert twice == once


# ---------------------------------------------------------------------------
# _fix_trailing_whitespace unit tests
# ---------------------------------------------------------------------------

def test_spaces_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("foo   \n", stats)
    assert result == "foo\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_tab_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("bar\t\n", stats)
    assert result == "bar\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_mixed_space_tab_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("baz \t \n", stats)
    assert result == "baz\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_forced_break_two_spaces_preserved():
    stats = CleanStats()
    result = _fix_trailing_whitespace("line  \n", stats)
    assert result == "line  \n", repr(result)
    assert stats.trailing_ws_fixed == 0


def test_single_space_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("word \n", stats)
    assert result == "word\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_line_without_newline_trailing_spaces_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("end   ", stats)
    assert result == "end", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_forced_break_no_newline_preserved():
    stats = CleanStats()
    result = _fix_trailing_whitespace("line  ", stats)
    assert result == "line  ", repr(result)
    assert stats.trailing_ws_fixed == 0


def test_clean_line_unchanged():
    stats = CleanStats()
    result = _fix_trailing_whitespace("clean line\n", stats)
    assert result == "clean line\n", repr(result)
    assert stats.trailing_ws_fixed == 0


def test_empty_line_unchanged():
    stats = CleanStats()
    result = _fix_trailing_whitespace("\n", stats)
    assert result == "\n", repr(result)
    assert stats.trailing_ws_fixed == 0


# ---------------------------------------------------------------------------
# Pipeline integration: markers pass through untouched
# ---------------------------------------------------------------------------

def test_page_marker_primary_preserved():
    lines = ["[[Pág. 3]]\n", "text with space   \n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    assert result[0] == "[[Pág. 3]]\n", repr(result[0])
    assert result[1] == "text with space\n", repr(result[1])


def test_page_marker_legacy_preserved():
    lines = ["<!-- page 5 -->\n", "trailing tab\t\n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    assert result[0] == "<!-- page 5 -->\n", repr(result[0])
    assert result[1] == "trailing tab\n", repr(result[1])


def test_page_marker_not_preserved_when_disabled():
    lines = ["[[Pág. 1]]\n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=False, stats=stats, verbose=False)
    # Marker treated as normal text — trailing whitespace fix still applies
    assert result[0] == "[[Pág. 1]]\n", repr(result[0])


# ---------------------------------------------------------------------------
# Real fixture integration tests
# ---------------------------------------------------------------------------

def test_realfixture_markers_preserved():
    md_path = FIXTURE_DIR / "pdf_to_md_sample.md"
    raw_text = md_path.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines(keepends=True)
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    result_text = "".join(result)
    assert "[[Pág. 1]]" in result_text, "[[Pág. 1]] ausente na saída"
    assert "[[Pág. 2]]" in result_text, "[[Pág. 2]] ausente na saída"
    # Verify order is preserved
    idx1 = result_text.index("[[Pág. 1]]")
    idx2 = result_text.index("[[Pág. 2]]")
    assert idx1 < idx2, "Ordem dos marcadores foi alterada"


def test_realfixture_content_integrity():
    md_path = FIXTURE_DIR / "pdf_to_md_sample.md"
    raw_text = md_path.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines(keepends=True)
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    result_text = "".join(result)
    # Legal text: proprietário qualification should survive intact
    assert "JURACI PIRES PAVAN" in result_text, "Texto jurídico do proprietário foi removido"
    assert "portadora da cédula de" in result_text, \
        "Qualificação foi truncada (parte 1)"
    assert "identidade RG. n.4.294.873-SSP/SP" in result_text, \
        "Qualificação foi truncada (parte 2)"
    assert "793.933.908-78" in result_text, "CPF foi removido"
    # OCR artifact text should also be preserved (cleaner preserves content)
    assert "MARIAALVES DA SILVACONTRUCCI" in result_text, \
        "Cabeçalho OCR com artifact não foi preservado"


# ---------------------------------------------------------------------------
# _fix_heading_space unit tests
# ---------------------------------------------------------------------------

def test_heading_no_space_corrected():
    stats = CleanStats()
    result = _fix_heading_space("##Título\n", stats)
    assert result == "## Título\n", repr(result)
    assert stats.headings_fixed == 1


def test_heading_excess_spaces_normalized():
    stats = CleanStats()
    result = _fix_heading_space("###   Título com excesso\n", stats)
    assert result == "### Título com excesso\n", repr(result)
    assert stats.headings_fixed == 1


def test_heading_already_correct_unchanged():
    stats = CleanStats()
    result = _fix_heading_space("## Título correto\n", stats)
    assert result == "## Título correto\n", repr(result)
    assert stats.headings_fixed == 0


# ---------------------------------------------------------------------------
# _fix_bullet unit tests
# ---------------------------------------------------------------------------

def test_asterisk_bullet_normalized_to_dash():
    stats = CleanStats()
    result = _fix_bullet("* Item A\n", stats)
    assert result == "- Item A\n", repr(result)
    assert stats.bullets_normalized == 1


def test_plus_bullet_normalized_to_dash():
    stats = CleanStats()
    result = _fix_bullet("+ Item B\n", stats)
    assert result == "- Item B\n", repr(result)
    assert stats.bullets_normalized == 1


def test_dash_bullet_unchanged():
    stats = CleanStats()
    result = _fix_bullet("- Item C\n", stats)
    assert result == "- Item C\n", repr(result)
    assert stats.bullets_normalized == 0


def test_inline_asterisk_not_treated_as_bullet():
    stats = CleanStats()
    result = _fix_bullet("*palavra* em destaque\n", stats)
    assert result == "*palavra* em destaque\n", repr(result)
    assert stats.bullets_normalized == 0


# ---------------------------------------------------------------------------
# _fix_horizontal_rule unit tests
# ---------------------------------------------------------------------------

def test_triple_asterisk_normalized():
    stats = CleanStats()
    result = _fix_horizontal_rule("***\n", stats)
    assert result == "---\n", repr(result)
    assert stats.separators_normalized == 1


def test_triple_underscore_normalized():
    stats = CleanStats()
    result = _fix_horizontal_rule("___\n", stats)
    assert result == "---\n", repr(result)
    assert stats.separators_normalized == 1


def test_triple_equals_normalized():
    stats = CleanStats()
    result = _fix_horizontal_rule("===\n", stats)
    assert result == "---\n", repr(result)
    assert stats.separators_normalized == 1


def test_spaced_dashes_normalized():
    stats = CleanStats()
    result = _fix_horizontal_rule("- - - -\n", stats)
    assert result == "---\n", repr(result)
    assert stats.separators_normalized == 1


def test_line_with_text_not_normalized():
    stats = CleanStats()
    result = _fix_horizontal_rule("--- texto\n", stats)
    assert result == "--- texto\n", repr(result)
    assert stats.separators_normalized == 0


# ---------------------------------------------------------------------------
# _remove_decorative_line unit tests
# ---------------------------------------------------------------------------

def test_dots_only_line_removed():
    stats = CleanStats()
    result = _remove_decorative_line("....\n", stats)
    assert result is None
    assert stats.decorative_removed == 1


def test_equals_only_line_removed():
    stats = CleanStats()
    result = _remove_decorative_line("====\n", stats)
    assert result is None
    assert stats.decorative_removed == 1


def test_normal_text_line_preserved():
    stats = CleanStats()
    result = _remove_decorative_line("Texto normal\n", stats)
    assert result == "Texto normal\n", repr(result)
    assert stats.decorative_removed == 0


# ---------------------------------------------------------------------------
# _extract_code_blocks and _restore_code_blocks unit tests
# ---------------------------------------------------------------------------

def test_extract_code_block_creates_placeholder():
    lines = ["antes\n", "```python\n", "x = 1\n", "```\n", "depois\n"]
    result_lines, blocks = _extract_code_blocks(lines)
    assert "__CODE_BLOCK_0__\n" in result_lines, "Placeholder missing from extracted lines"
    assert len(blocks) == 1, f"Expected 1 block, got {len(blocks)}"
    block_content = list(blocks.values())[0]
    assert "```python\n" in block_content, "Opening fence missing from block content"
    assert "x = 1\n" in block_content, "Block body missing from stored content"


def test_restore_code_block_exact_content():
    lines = ["texto\n", "```python\n", "x = 1   \n", "```\n", "fim\n"]
    extracted, blocks = _extract_code_blocks(lines)
    restored = _restore_code_blocks(extracted, blocks)
    restored_text = "".join(restored)
    assert "x = 1   \n" in restored_text, "Trailing whitespace inside code block not preserved"
    assert "```python\n" in restored_text, "Opening fence lost after restore"


def test_code_block_ws_preserved_through_pipeline():
    lines = [
        "antes\n",
        "```\n",
        "    code with trailing   \n",
        "```\n",
        "depois\n",
    ]
    extracted, blocks = _extract_code_blocks(lines)
    stats = CleanStats()
    cleaned = clean_lines(extracted, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    restored = _restore_code_blocks(cleaned, blocks)
    result_text = "".join(restored)
    assert "    code with trailing   \n" in result_text, \
        "Trailing whitespace inside code block was modified by pipeline"


# ---------------------------------------------------------------------------
# --max-blank customization tests
# ---------------------------------------------------------------------------

def test_max_blank_one_collapses_excess_blanks():
    lines = ["A\n", "\n", "\n", "\n", "B\n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=1, preserve_markers=True, stats=stats, verbose=False)
    result_text = "".join(result)
    assert result_text == "A\n\nB\n", repr(result_text)


# ---------------------------------------------------------------------------
# --no-markers tests
# ---------------------------------------------------------------------------

def test_no_markers_marker_treated_as_normal_text():
    lines = ["[[Pág. 1]]\n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=False, stats=stats, verbose=False)
    assert "[[Pág. 1]]" in "".join(result), "Marker line should still appear in output as normal text"


# ---------------------------------------------------------------------------
# CLI end-to-end tests
# ---------------------------------------------------------------------------

def test_cli_e2e_exit_code_and_output_exists(tmp_path):
    input_file = FIXTURE_DIR / "pdf_to_md_sample.md"
    output_file = tmp_path / "cleaned.md"
    script = Path(__file__).parent / "clean_markdown.py"

    proc = subprocess.run(
        [sys.executable, str(script), "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"CLI failed (exit {proc.returncode}):\n{proc.stderr}"
    assert output_file.exists(), "Output file not created by CLI"
    assert output_file.stat().st_size > 0, "Output file is empty"


def test_cli_e2e_output_passes_validate_output(tmp_path):
    input_file = FIXTURE_DIR / "pdf_to_md_sample.md"
    output_file = tmp_path / "cleaned.md"
    script = Path(__file__).parent / "clean_markdown.py"
    validate_script = Path(__file__).parent / "validate_output.py"

    subprocess.run(
        [sys.executable, str(script), "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        check=True,
    )

    validate_proc = subprocess.run(
        [sys.executable, str(validate_script), "--input", str(output_file)],
        capture_output=True,
        text=True,
    )
    assert validate_proc.returncode == 0, \
        f"validate_output failed:\n{validate_proc.stdout}\n{validate_proc.stderr}"


def test_cli_e2e_preserves_markers_and_legal_content(tmp_path):
    input_file = FIXTURE_DIR / "pdf_to_md_sample.md"
    output_file = tmp_path / "cleaned.md"
    script = Path(__file__).parent / "clean_markdown.py"

    subprocess.run(
        [sys.executable, str(script), "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        check=True,
    )
    content = output_file.read_text(encoding="utf-8")
    assert "[[Pág. 1]]" in content, "[[Pág. 1]] missing from CLI output"
    assert "[[Pág. 2]]" in content, "[[Pág. 2]] missing from CLI output"
    assert "JURACI PIRES PAVAN" in content, "Legal owner name missing from CLI output"
    assert "793.933.908-78" in content, "CPF missing from CLI output"


def test_judicial_locator_preserved():
    lines = ['[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1", page="2"]]\n']
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    assert result[0] == '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1", page="2"]]\n', repr(result[0])


def test_cli_e2e_decodes_html_entities(tmp_path):
    input_file = tmp_path / "entity_input.md"
    input_file.write_text("Certid&atilde;o da d&iacute;vida.", encoding="utf-8")
    output_file = tmp_path / "entity_output.md"
    script = Path(__file__).parent / "clean_markdown.py"
    
    subprocess.run(
        [sys.executable, str(script), "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        check=True,
    )
    content = output_file.read_text(encoding="utf-8")
    assert "Certidão da dívida." in content, f"HTML entity not decoded: {repr(content)}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
