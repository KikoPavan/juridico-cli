#!/usr/bin/env python3
"""
Unit tests for boilerplate detection heuristic in convert_pdf_to_md.

Tests _strip_boilerplate and _needs_ocr in isolation — no OCR engine required.
Exit codes: 0=pass  1=fail
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert_pdf_to_md import _strip_boilerplate, _needs_ocr, MIN_CHARS_FOR_TEXT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        raise AssertionError(name)


# ---------------------------------------------------------------------------
# Task 3.1 — _strip_boilerplate: known patterns removed, body preserved
# ---------------------------------------------------------------------------

def test_strip_fls_numeration():
    result = _strip_boilerplate("Fls. 42")
    _run("strip: 'Fls. 42' → empty", result.strip() == "")


def test_strip_fl_lowercase():
    result = _strip_boilerplate("fl. 5")
    _run("strip: 'fl. 5' → empty", result.strip() == "")


def test_strip_standalone_page_number():
    result = _strip_boilerplate("  42  ")
    _run("strip: '  42  ' → empty", result.strip() == "")


def test_strip_tribunal_header():
    text = "TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO"
    result = _strip_boilerplate(text)
    _run("strip: tribunal header → empty", result.strip() == "")


def test_strip_poder_judiciario():
    text = "Poder Judiciário"
    result = _strip_boilerplate(text)
    _run("strip: 'Poder Judiciário' → empty", result.strip() == "")


def test_strip_foro_regional():
    text = "Foro Regional VII - Itaquera"
    result = _strip_boilerplate(text)
    _run("strip: foro regional header → empty", result.strip() == "")


def test_strip_assinado_eletronicamente():
    text = "Assinado eletronicamente por João Silva em 01/01/2024"
    result = _strip_boilerplate(text)
    _run("strip: e-signature footer → empty", result.strip() == "")


def test_strip_horizontal_rule():
    result = _strip_boilerplate("----------")
    _run("strip: horizontal rule → empty", result.strip() == "")


def test_body_text_preserved():
    text = (
        "Vem respeitosamente à presença de Vossa Excelência, "
        "o autor da presente ação, por meio de seu advogado, "
        "expor e requerer o seguinte."
    )
    result = _strip_boilerplate(text)
    _run("preserve: petition body text unchanged", result == text)


def test_body_text_with_numbers_preserved():
    text = "O réu foi citado em 15/03/2024 conforme certidão de fl. 10, tendo apresentado contestação."
    result = _strip_boilerplate(text)
    _run("preserve: body with inline 'fl. 10' reference preserved", result == text)


# ---------------------------------------------------------------------------
# Task 3.2 — _needs_ocr returns True for boilerplate-only input
# ---------------------------------------------------------------------------

def test_needs_ocr_boilerplate_only():
    text = (
        "TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO\n"
        "Foro Regional VII - Itaquera\n"
        "Fls. 42\n"
        "----------"
    )
    needs, _ = _needs_ocr(text)
    _run("needs_ocr: boilerplate-only page → True", needs is True)


def test_needs_ocr_empty():
    needs, _ = _needs_ocr("")
    _run("needs_ocr: empty string → True", needs is True)


def test_needs_ocr_short_real_text():
    needs, _ = _needs_ocr("Olá mundo.")
    _run("needs_ocr: 10-char real text → True", needs is True)


# ---------------------------------------------------------------------------
# Task 3.3 — Mixed page: boilerplate + sufficient body → _needs_ocr False
# ---------------------------------------------------------------------------

def test_needs_ocr_mixed_page_sufficient_body():
    body = (
        "Vem respeitosamente à presença de Vossa Excelência o autor da ação, "
        "por intermédio de seu advogado constituído nos autos, expor e requerer "
        "o que se segue, com fundamento no artigo 319 do Código de Processo Civil."
    )
    assert len(body) >= MIN_CHARS_FOR_TEXT, f"body too short for this test: {len(body)}"
    text = f"TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO\nFls. 10\n{body}"
    needs, _ = _needs_ocr(text)
    _run("needs_ocr: mixed (boilerplate + rich body) → False", needs is False)


def test_needs_ocr_mixed_page_thin_body():
    text = "TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO\nFls. 10\nOlá."
    needs, _ = _needs_ocr(text)
    _run("needs_ocr: mixed (boilerplate + thin body) → True", needs is True)


def test_needs_ocr_rich_text_no_boilerplate():
    text = (
        "Por meio desta petição, o requerente vem, com fundamento no artigo 300 "
        "do CPC, requerer a concessão de tutela de urgência, demonstrando a "
        "probabilidade do direito e o perigo de dano irreparável."
    )
    needs, _ = _needs_ocr(text)
    _run("needs_ocr: rich body without boilerplate → False", needs is False)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        test_strip_fls_numeration,
        test_strip_fl_lowercase,
        test_strip_standalone_page_number,
        test_strip_tribunal_header,
        test_strip_poder_judiciario,
        test_strip_foro_regional,
        test_strip_assinado_eletronicamente,
        test_strip_horizontal_rule,
        test_body_text_preserved,
        test_body_text_with_numbers_preserved,
        test_needs_ocr_boilerplate_only,
        test_needs_ocr_empty,
        test_needs_ocr_short_real_text,
        test_needs_ocr_mixed_page_sufficient_body,
        test_needs_ocr_mixed_page_thin_body,
        test_needs_ocr_rich_text_no_boilerplate,
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
