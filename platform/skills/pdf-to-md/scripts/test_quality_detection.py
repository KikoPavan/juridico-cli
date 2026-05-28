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
