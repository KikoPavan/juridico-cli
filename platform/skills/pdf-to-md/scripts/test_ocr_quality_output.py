#!/usr/bin/env python3
"""
Tests for the low_ocr_quality path and _preprocess_image function.

No PaddleOCR required — all tests use synthetic fixtures and Pillow only.
Exit codes: 0=pass  1=fail
"""

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert_pdf_to_md import (
    _preprocess_image,
    _text_quality_score,
    _ocr_post_quality_score,
    _case_chaos_ratio,
    _is_case_chaotic,
    MIN_OCR_POST_QUALITY,
    OCR_RENDER_SCALE,
)


# ---------------------------------------------------------------------------
# Fixture 1: glued text — no spaces → base quality score near 0.0
# ---------------------------------------------------------------------------

CORRUPTED_OCR_FIXTURE = (
    "Oatodeprocuraçãofoidevolvidoparaaspartesnosautos"
    "doprocessonº0001234-56.2024.8.26.0001semqualquer"
    "motivoexplicitoouregistronosistema"
    "ProcuradoraDoEstadoDevidamenteHabilitadaParaAtos"
)

assert len(CORRUPTED_OCR_FIXTURE) >= 50, "fixture must have >= 50 chars"
assert _text_quality_score(CORRUPTED_OCR_FIXTURE) < MIN_OCR_POST_QUALITY, (
    f"fixture score {_text_quality_score(CORRUPTED_OCR_FIXTURE):.3f} must be < {MIN_OCR_POST_QUALITY}"
)

# ---------------------------------------------------------------------------
# Fixture 2: case-chaos OCR — words with spaces but corrupted char substitution.
# Mirrors the actual PaddleOCR output from procuração_Monica.pdf.
# Space density is normal → _text_quality_score near 1.0 (misses this).
# _ocr_post_quality_score must detect it via case-chaos penalty.
# ---------------------------------------------------------------------------

OCR_CASE_CHAOS_FIXTURE = (
    "REPUILICA FEDERATIVA DO HRASIL\n"
    "tS1aDO De sAO PAUi.O\n"
    "REPUHLICA FEDERAiiVA DO BRASIIL\n"
    "EStADO De SAO pAuLO\n"
)

assert _text_quality_score(OCR_CASE_CHAOS_FIXTURE) >= MIN_OCR_POST_QUALITY, (
    f"case-chaos fixture: old score {_text_quality_score(OCR_CASE_CHAOS_FIXTURE):.3f} "
    f"must be >= {MIN_OCR_POST_QUALITY} (documents that old metric misses this pattern)"
)
assert _ocr_post_quality_score(OCR_CASE_CHAOS_FIXTURE) < MIN_OCR_POST_QUALITY, (
    f"case-chaos fixture: new score {_ocr_post_quality_score(OCR_CASE_CHAOS_FIXTURE):.3f} "
    f"must be < {MIN_OCR_POST_QUALITY}"
)


# ---------------------------------------------------------------------------
# Test: render scale must correspond to 300 DPI (300 / 72)
# ---------------------------------------------------------------------------

def test_render_scale_is_300_dpi():
    dpi = OCR_RENDER_SCALE * 72
    _run(
        f"OCR_RENDER_SCALE={OCR_RENDER_SCALE:.4f} → {dpi:.1f} DPI (expected ~300)",
        abs(dpi - 300) < 1,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        raise AssertionError(name)


def _make_png_bytes(width: int = 32, height: int = 32, color: int = 200) -> bytes:
    """Generate a synthetic grayscale PNG as bytes using Pillow."""
    from PIL import Image
    img = Image.new("L", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Test 6.2 — low_ocr_quality score below threshold (glued-text path)
# ---------------------------------------------------------------------------

def test_low_ocr_quality_score_below_threshold():
    score = _text_quality_score(CORRUPTED_OCR_FIXTURE)
    _run(
        f"low_ocr_quality: glued fixture score {score:.3f} < MIN_OCR_POST_QUALITY ({MIN_OCR_POST_QUALITY})",
        score < MIN_OCR_POST_QUALITY,
    )


# ---------------------------------------------------------------------------
# Tests for case-chaos detection (procuração_Monica.pdf pattern)
# ---------------------------------------------------------------------------

def test_case_chaos_fixture_below_threshold_with_post_score():
    score = _ocr_post_quality_score(OCR_CASE_CHAOS_FIXTURE)
    _run(
        f"case-chaos fixture: _ocr_post_quality_score {score:.3f} < MIN_OCR_POST_QUALITY ({MIN_OCR_POST_QUALITY})",
        score < MIN_OCR_POST_QUALITY,
    )


def test_old_score_misses_case_chaos():
    score = _text_quality_score(OCR_CASE_CHAOS_FIXTURE)
    _run(
        f"case-chaos fixture: _text_quality_score {score:.3f} >= threshold — old metric insufficient",
        score >= MIN_OCR_POST_QUALITY,
    )


def test_is_case_chaotic_flagged():
    chaotic_words = ["tS1aDO", "sAO", "pAuLO", "EStADO", "PAUiO", "FEDERAiiVA"]
    for w in chaotic_words:
        _run(f"_is_case_chaotic('{w}') == True", _is_case_chaotic(w) is True)


def test_is_case_chaotic_clean():
    clean_words = ["FEDERATIVA", "brasil", "Brasil", "DO", "São", "HRASIL", "De"]
    for w in clean_words:
        _run(f"_is_case_chaotic('{w}') == False", _is_case_chaotic(w) is False)


def test_case_chaos_ratio_on_clean_text():
    clean = "Vem respeitosamente à presença de Vossa Excelência o autor da ação."
    ratio = _case_chaos_ratio(clean)
    _run(
        f"_case_chaos_ratio on clean text: {ratio:.3f} < 0.1",
        ratio < 0.1,
    )


def test_ocr_post_quality_clean_text_passes():
    clean = (
        "Por meio desta petição, o requerente vem, com fundamento no artigo 300 "
        "do CPC, requerer a concessão de tutela de urgência, demonstrando a "
        "probabilidade do direito e o perigo de dano irreparável."
    )
    score = _ocr_post_quality_score(clean)
    _run(
        f"_ocr_post_quality_score on clean text: {score:.3f} >= MIN_OCR_POST_QUALITY",
        score >= MIN_OCR_POST_QUALITY,
    )


# ---------------------------------------------------------------------------
# Test 6.3 — _preprocess_image returns non-empty bytes for valid PNG
# ---------------------------------------------------------------------------

def test_preprocess_image_returns_bytes():
    png_bytes = _make_png_bytes()
    result = _preprocess_image(png_bytes)
    _run(
        f"preprocess_image: returns non-empty bytes ({len(result)} bytes)",
        isinstance(result, bytes) and len(result) > 0,
    )


def test_preprocess_image_returns_valid_png():
    from PIL import Image
    png_bytes = _make_png_bytes(width=64, height=64, color=128)
    result = _preprocess_image(png_bytes)
    try:
        img = Image.open(io.BytesIO(result))
        img.verify()
        valid = True
    except Exception:
        valid = False
    _run("preprocess_image: output is valid PNG", valid)


def test_preprocess_image_returns_different_object_on_success():
    png_bytes = _make_png_bytes()
    result = _preprocess_image(png_bytes)
    _run(
        "preprocess_image: returns a new bytes object (not the same reference)",
        result is not png_bytes,
    )


# ---------------------------------------------------------------------------
# Test 6.4 — _preprocess_image fallback on error
# ---------------------------------------------------------------------------

def test_preprocess_image_fallback_on_error():
    invalid_bytes = b"not-a-png"
    result = _preprocess_image(invalid_bytes)
    _run(
        "preprocess_image: returns original bytes on invalid input",
        result is invalid_bytes,
    )


def test_preprocess_image_fallback_on_empty_input():
    empty = b""
    result = _preprocess_image(empty)
    _run(
        "preprocess_image: returns original bytes on empty input",
        result is empty,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        test_render_scale_is_300_dpi,
        test_low_ocr_quality_score_below_threshold,
        test_case_chaos_fixture_below_threshold_with_post_score,
        test_old_score_misses_case_chaos,
        test_is_case_chaotic_flagged,
        test_is_case_chaotic_clean,
        test_case_chaos_ratio_on_clean_text,
        test_ocr_post_quality_clean_text_passes,
        test_preprocess_image_returns_bytes,
        test_preprocess_image_returns_valid_png,
        test_preprocess_image_returns_different_object_on_success,
        test_preprocess_image_fallback_on_error,
        test_preprocess_image_fallback_on_empty_input,
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
