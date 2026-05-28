#!/usr/bin/env python3
"""
Unit tests for _text_quality_score and _needs_ocr low_quality detection.

Tests run without OCR engine — no PaddleOCR required.
Exit codes: 0=pass  1=fail
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert_pdf_to_md import (
    _text_quality_score,
    _needs_ocr,
    MIN_TEXT_QUALITY,
    MIN_CHARS_FOR_TEXT,
    SHORT_LINE_RATIO_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Task 4.1 — Synthetic fixture representing certidão.pdf corruption pattern
# Words glued together, no spaces, >= 100 printable chars, >= MIN_CHARS_FOR_TEXT
# ---------------------------------------------------------------------------

CORRUPTED_TEXT_FIXTURE = (
    "Certidãodeinteiroteornº12345dosautosdeprocessonº0001234-56.2024.8.26.0001"
    "daVaradeFamíliaeSuccessõesdaComarcadeSãoPauloEstadonãoexistem"
)

assert len(CORRUPTED_TEXT_FIXTURE) >= 100, "fixture must have >= 100 chars"
assert len(CORRUPTED_TEXT_FIXTURE) >= MIN_CHARS_FOR_TEXT, "fixture must pass MIN_CHARS_FOR_TEXT"
assert all(c.isprintable() or c == "\n" for c in CORRUPTED_TEXT_FIXTURE), "fixture must be printable"


# ---------------------------------------------------------------------------
# Fixture: garbled text with many short lines (procuração_Monica.pdf pattern)
# Per-char OCR extraction: individual letters on separate lines, quality score ~1.0
# but content is unusable. short_line_ratio > SHORT_LINE_RATIO_THRESHOLD.
# ---------------------------------------------------------------------------

GARBLED_LINES_FIXTURE = (
    "• \nl \n• \n' \n"
    "T \nI \nD \n"
    "Esta é uma certidão de teor do livro de notas número 262.\n"
    "C \nE \nR \nT \nI \nF \nI \nC \nA \n"
    "O Tabelião da cidade e comarca de Ourinhos.\n"
    "M \nO \nL \nE \nR \nO \n"
    "Conteúdo adicional para garantir comprimento suficiente do texto.\n"
    "P \nR \nO \nC \nU \nR \nA \nÇ \nÃ \nO \n"
    "Documento lavrado em conformidade com as normas vigentes.\n"
    "B \nA \nS \nT \nA \nN \nT \nE \n"
)

assert len(GARBLED_LINES_FIXTURE) >= MIN_CHARS_FOR_TEXT, "garbled fixture must pass MIN_CHARS_FOR_TEXT"
assert _text_quality_score(GARBLED_LINES_FIXTURE) >= MIN_TEXT_QUALITY, (
    "garbled fixture must have quality score >= MIN_TEXT_QUALITY "
    "(documents why the existing score alone is insufficient)"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        raise AssertionError(name)


# ---------------------------------------------------------------------------
# Task 3.1 — _text_quality_score: glued/corrupted text → score < MIN_TEXT_QUALITY
# ---------------------------------------------------------------------------

def test_quality_score_glued_words():
    glued = "oprocessofoiadistribuídoparaavaradesenhores"
    score = _text_quality_score(glued)
    _run(
        f"quality_score: glued words → score {score:.3f} < MIN_TEXT_QUALITY ({MIN_TEXT_QUALITY})",
        score < MIN_TEXT_QUALITY,
    )


def test_quality_score_corrupted_fixture():
    score = _text_quality_score(CORRUPTED_TEXT_FIXTURE)
    _run(
        f"quality_score: certidão fixture → score {score:.3f} < MIN_TEXT_QUALITY ({MIN_TEXT_QUALITY})",
        score < MIN_TEXT_QUALITY,
    )


# ---------------------------------------------------------------------------
# Task 3.2 — _text_quality_score: clean Portuguese text → score >= MIN_TEXT_QUALITY
# ---------------------------------------------------------------------------

def test_quality_score_clean_portuguese():
    clean = "O processo foi distribuído para a vara de senhores."
    score = _text_quality_score(clean)
    _run(
        f"quality_score: clean Portuguese → score {score:.3f} >= MIN_TEXT_QUALITY ({MIN_TEXT_QUALITY})",
        score >= MIN_TEXT_QUALITY,
    )


def test_quality_score_legal_body_text():
    clean = (
        "Vem respeitosamente à presença de Vossa Excelência o autor da ação, "
        "por intermédio de seu advogado constituído nos autos, expor e requerer "
        "o que se segue, com fundamento no artigo 319 do Código de Processo Civil."
    )
    score = _text_quality_score(clean)
    _run(
        f"quality_score: legal body text → score {score:.3f} >= MIN_TEXT_QUALITY ({MIN_TEXT_QUALITY})",
        score >= MIN_TEXT_QUALITY,
    )


# ---------------------------------------------------------------------------
# Task 3.3 — _needs_ocr: corrupted text with sufficient chars → (True, "low_quality")
# ---------------------------------------------------------------------------

def test_needs_ocr_corrupted_returns_low_quality():
    needs, reason = _needs_ocr(CORRUPTED_TEXT_FIXTURE)
    _run(
        f"needs_ocr: corrupted fixture → ({needs}, '{reason}') == (True, 'low_quality')",
        needs is True and reason == "low_quality",
    )


def test_needs_ocr_glued_words_returns_low_quality():
    # Repeat enough to pass MIN_CHARS_FOR_TEXT
    glued = "oprocessofoiadistribuídoparaavaradesenhores" * 3
    assert len(glued) >= MIN_CHARS_FOR_TEXT
    needs, reason = _needs_ocr(glued)
    _run(
        f"needs_ocr: repeated glued words → ({needs}, '{reason}') == (True, 'low_quality')",
        needs is True and reason == "low_quality",
    )


# ---------------------------------------------------------------------------
# Task 3.4 — _needs_ocr: clean text with sufficient chars → (False, "ok")
# ---------------------------------------------------------------------------

def test_needs_ocr_clean_text_returns_ok():
    clean = (
        "Por meio desta petição, o requerente vem, com fundamento no artigo 300 "
        "do CPC, requerer a concessão de tutela de urgência, demonstrando a "
        "probabilidade do direito e o perigo de dano irreparável."
    )
    assert len(clean) >= MIN_CHARS_FOR_TEXT
    needs, reason = _needs_ocr(clean)
    _run(
        f"needs_ocr: clean text → ({needs}, '{reason}') == (False, 'ok')",
        needs is False and reason == "ok",
    )


# ---------------------------------------------------------------------------
# Garbled text: many short lines (procuração_Monica.pdf pattern)
# ---------------------------------------------------------------------------

def test_needs_ocr_garbled_lines_returns_garbled_text():
    needs, reason = _needs_ocr(GARBLED_LINES_FIXTURE)
    _run(
        f"needs_ocr: garbled lines fixture → ({needs}, '{reason}') == (True, 'garbled_text')",
        needs is True and reason == "garbled_text",
    )


def test_quality_score_garbled_lines_not_below_threshold():
    # Verifies the existing score alone is not enough to catch this pattern —
    # documents why the short_line_ratio check is necessary.
    score = _text_quality_score(GARBLED_LINES_FIXTURE)
    _run(
        f"quality_score: garbled lines → score {score:.3f} >= MIN_TEXT_QUALITY "
        f"(existing score insufficient; short_line_ratio check is required)",
        score >= MIN_TEXT_QUALITY,
    )


def test_needs_ocr_short_line_ratio_boundary():
    # Build text where exactly SHORT_LINE_RATIO_THRESHOLD of lines are single chars.
    # Use enough single-char and multi-word lines to stay above MIN_CHARS_FOR_TEXT.
    filler = "Este documento foi lavrado pelo tabelião conforme a lei vigente.\n"
    single_char_line = "X \n"
    # Compose: ratio of short lines just below threshold → must NOT trigger garbled_text
    long_lines = filler * 9
    short_lines = single_char_line * 1  # 1/(9+1) = 10% < 15% threshold
    below_text = long_lines + short_lines
    needs_below, reason_below = _needs_ocr(below_text)
    _run(
        f"needs_ocr: short_line_ratio below threshold → ({needs_below}, '{reason_below}') != garbled_text",
        not (needs_below and reason_below == "garbled_text"),
    )

    # ratio just above threshold → must trigger garbled_text
    long_lines_hi = filler * 5
    short_lines_hi = single_char_line * 2  # 2/(5+2) = 28.6% > 15% threshold
    above_text = long_lines_hi + short_lines_hi
    needs_above, reason_above = _needs_ocr(above_text)
    _run(
        f"needs_ocr: short_line_ratio above threshold → ({needs_above}, '{reason_above}') == (True, 'garbled_text')",
        needs_above is True and reason_above == "garbled_text",
    )


# ---------------------------------------------------------------------------
# Boundary: score at exactly 0.0 (pure glued, no spaces)
# ---------------------------------------------------------------------------

def test_quality_score_empty_returns_zero():
    score = _text_quality_score("")
    _run("quality_score: empty string → 0.0", score == 0.0)


def test_quality_score_range():
    samples = [
        CORRUPTED_TEXT_FIXTURE,
        "oprocessofoiadistribuídoparaavaradesenhores",
        "O processo foi distribuído para a vara.",
        "texto curto",
        "",
    ]
    results = [_text_quality_score(s) for s in samples]
    ok = all(0.0 <= s <= 1.0 for s in results)
    _run(f"quality_score: all scores in [0.0, 1.0] — {results}", ok)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        test_quality_score_glued_words,
        test_quality_score_corrupted_fixture,
        test_quality_score_clean_portuguese,
        test_quality_score_legal_body_text,
        test_needs_ocr_corrupted_returns_low_quality,
        test_needs_ocr_glued_words_returns_low_quality,
        test_needs_ocr_clean_text_returns_ok,
        test_needs_ocr_garbled_lines_returns_garbled_text,
        test_quality_score_garbled_lines_not_below_threshold,
        test_needs_ocr_short_line_ratio_boundary,
        test_quality_score_empty_returns_zero,
        test_quality_score_range,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError:
            failed += 1
    total = passed + failed
    print(f"\n{passed}/{total} tests passed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
