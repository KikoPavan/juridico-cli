#!/usr/bin/env python3
"""
Tests for the low_ocr_quality path and _preprocess_image function.

No PaddleOCR required — all tests use synthetic fixtures and Pillow only.
Exit codes: 0=pass  1=fail
"""

import io
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from convert_pdf_to_md import (
    LmStudioUnavailableError,
    _lm_studio_ocr_timeout,
    _preprocess_image,
    _run_lm_studio_ocr,
    _run_local_ocr,
    _pick_best_ocr,
    _sanitize_paddleocr_output,
    _is_line_gibberish,
    _is_native_text_gibberish,
    _get_useful_text,
    _text_quality_score,
    _ocr_post_quality_score,
    _case_chaos_ratio,
    _is_case_chaotic,
    _intrusive_symbol_ratio,
    _heading_level,
    LM_STUDIO_BASE_URL_ENV,
    LM_STUDIO_OCR_MODEL_ENV,
    LM_STUDIO_OCR_TIMEOUT_ENV,
    MIN_OCR_POST_QUALITY,
    OCR_RENDER_SCALE,
    _LM_STUDIO_OCR_TIMEOUT_DEFAULT,
    _OCR_REPETITION_LINE_THRESHOLD,
    _OCR_REPETITION_NUMBER_THRESHOLD,
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


def test_ocr_post_quality_penalizes_locator_only_text():
    locator_only = (
        "Processo: 4000153-37.2026.8.26.0136/SP\n"
        "Evento: 43\n"
        "Título do Evento: Contestação\n"
        "Usuário: Maria\n"
        "Sequência: 1\n"
    )
    score = _ocr_post_quality_score(locator_only)
    _run(
        f"locator-only OCR score {score:.3f} < MIN_OCR_POST_QUALITY",
        score < MIN_OCR_POST_QUALITY,
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
# Tests for LM Studio / PaddleOCR-VL backend (REQ-OCR-03, REQ-OCR-07)
# ---------------------------------------------------------------------------

def test_lm_studio_unavailable_error_importable():
    _run(
        "LmStudioUnavailableError is importable from convert_pdf_to_md",
        issubclass(LmStudioUnavailableError, RuntimeError),
    )


def test_lm_studio_ocr_raises_when_env_vars_absent():
    saved_base = os.environ.pop(LM_STUDIO_BASE_URL_ENV, None)
    saved_model = os.environ.pop(LM_STUDIO_OCR_MODEL_ENV, None)
    try:
        raised = False
        try:
            _run_lm_studio_ocr(b"fake-image-bytes")
        except LmStudioUnavailableError:
            raised = True
        _run(
            f"_run_lm_studio_ocr raises LmStudioUnavailableError when {LM_STUDIO_BASE_URL_ENV} and {LM_STUDIO_OCR_MODEL_ENV} are absent",
            raised,
        )
    finally:
        if saved_base is not None:
            os.environ[LM_STUDIO_BASE_URL_ENV] = saved_base
        if saved_model is not None:
            os.environ[LM_STUDIO_OCR_MODEL_ENV] = saved_model


def test_lm_studio_ocr_timeout_default():
    saved = os.environ.pop(LM_STUDIO_OCR_TIMEOUT_ENV, None)
    try:
        val = _lm_studio_ocr_timeout()
        _run(
            f"_lm_studio_ocr_timeout() default == {_LM_STUDIO_OCR_TIMEOUT_DEFAULT}s when {LM_STUDIO_OCR_TIMEOUT_ENV} is unset",
            val == _LM_STUDIO_OCR_TIMEOUT_DEFAULT,
        )
    finally:
        if saved is not None:
            os.environ[LM_STUDIO_OCR_TIMEOUT_ENV] = saved


def test_lm_studio_ocr_timeout_from_env():
    os.environ[LM_STUDIO_OCR_TIMEOUT_ENV] = "120"
    try:
        val = _lm_studio_ocr_timeout()
        _run(
            f"_lm_studio_ocr_timeout() reads {LM_STUDIO_OCR_TIMEOUT_ENV}=120 → 120",
            val == 120,
        )
    finally:
        os.environ.pop(LM_STUDIO_OCR_TIMEOUT_ENV, None)


def test_lm_studio_ocr_raises_when_base_url_absent():
    saved_base = os.environ.pop(LM_STUDIO_BASE_URL_ENV, None)
    saved_model = os.environ.get(LM_STUDIO_OCR_MODEL_ENV)
    os.environ[LM_STUDIO_OCR_MODEL_ENV] = "some-model"
    try:
        raised = False
        try:
            _run_lm_studio_ocr(b"fake-image-bytes")
        except LmStudioUnavailableError:
            raised = True
        _run(
            f"_run_lm_studio_ocr raises LmStudioUnavailableError when {LM_STUDIO_BASE_URL_ENV} is absent",
            raised,
        )
    finally:
        if saved_base is not None:
            os.environ[LM_STUDIO_BASE_URL_ENV] = saved_base
        if saved_model is not None:
            os.environ[LM_STUDIO_OCR_MODEL_ENV] = saved_model
        else:
            os.environ.pop(LM_STUDIO_OCR_MODEL_ENV, None)


# ---------------------------------------------------------------------------
# Fixtures for _sanitize_paddleocr_output tests
# ---------------------------------------------------------------------------

LOC_FIXTURE = (
    "<|LOC_0|>TRIBUNAL DE JUSTIÇA<|LOC_123|>\n"
    "Estado de São Paulo<|LOC_456|>"
)

OO_DASH_FIXTURE = "Texto válido\no-o-o-o-o-o-o-o\nmais texto"

REPEATED_LINE_FIXTURE = "\n".join(
    ["0001234-56.2024.8.26.0001"] * (_OCR_REPETITION_LINE_THRESHOLD + 2) + ["outro texto"]
)

REPEATED_NUMBER_FIXTURE = (
    " ".join(["00012345"] * (_OCR_REPETITION_NUMBER_THRESHOLD + 2)) + " outro texto"
)

CLEAN_SANITIZE_FIXTURE = (
    "Por meio desta petição, o requerente vem requerer a concessão de tutela "
    "de urgência, nos termos do artigo 300 do Código de Processo Civil."
)

EXCESSIVE_LOC_FIXTURE = (
    "<|LOC_0|>TRIBUNAL DE JUSTIÇA<|LOC_123|>\n"
    "Estado de São Paulo<|LOC_456|>comarca de São Paulo<|LOC_789|>"
)

BIGRAM_STUTTERING_FIXTURE = (
    "petição de petição de petição de petição de tutela de urgência "
    "nos termos do artigo 300 do CPC."
)

LOW_DIVERSITY_FIXTURE = (
    "cpc cpc cpc cpc cpc cpc cpc cpc cpc cpc cpc cpc"
)

GARBAGE_SYMBOLS_FIXTURE = (
    "Por meio desta petição ......................... o autor requer."
)

GARBAGE_SLASHES_FIXTURE = (
    "Por meio desta petição ///////////////////////// o autor requer."
)


# ---------------------------------------------------------------------------
# Tests for _sanitize_paddleocr_output
# ---------------------------------------------------------------------------

def test_sanitize_removes_loc_tokens():
    text, metrics = _sanitize_paddleocr_output(LOC_FIXTURE)
    _run(
        f"sanitize: LOC tokens removed == 3 (got {metrics['loc_tokens_removed']})",
        metrics["loc_tokens_removed"] == 3,
    )
    _run(
        "sanitize: no <|LOC_| remain in output",
        "<|LOC_" not in text,
    )
    _run(
        "sanitize: meaningful text preserved after LOC removal",
        "TRIBUNAL DE JUSTIÇA" in text and "Estado de São Paulo" in text,
    )


def test_sanitize_detects_oo_dash_sequence():
    text, metrics = _sanitize_paddleocr_output(OO_DASH_FIXTURE)
    _run(
        "sanitize: oo_dash_sequence detected in o-o-o-o fixture",
        metrics["repetition_detected"] is True
        and "oo_dash_sequence" in metrics["repetition_reasons"],
    )


def test_sanitize_detects_repeated_lines():
    text, metrics = _sanitize_paddleocr_output(REPEATED_LINE_FIXTURE)
    _run(
        f"sanitize: line_repeat detected when same line appears >{_OCR_REPETITION_LINE_THRESHOLD}x",
        metrics["repetition_detected"] is True
        and any("line_repeat" in r for r in metrics["repetition_reasons"]),
    )


def test_sanitize_detects_repeated_numbers():
    text, metrics = _sanitize_paddleocr_output(REPEATED_NUMBER_FIXTURE)
    _run(
        f"sanitize: number_repeat detected when same 4+ digit number appears >{_OCR_REPETITION_NUMBER_THRESHOLD}x",
        metrics["repetition_detected"] is True
        and any("number_repeat" in r for r in metrics["repetition_reasons"]),
    )


def test_sanitize_clean_text_no_false_positive():
    text, metrics = _sanitize_paddleocr_output(CLEAN_SANITIZE_FIXTURE)
    _run(
        "sanitize: clean text — loc_tokens_removed == 0",
        metrics["loc_tokens_removed"] == 0,
    )
    _run(
        "sanitize: clean text — repetition_detected == False",
        metrics["repetition_detected"] is False,
    )
    _run(
        "sanitize: clean text — text preserved unchanged",
        text == CLEAN_SANITIZE_FIXTURE,
    )


def test_sanitize_empty_text():
    text, metrics = _sanitize_paddleocr_output("")
    _run(
        "sanitize: empty input → loc_tokens_removed == 0",
        metrics["loc_tokens_removed"] == 0,
    )
    _run(
        "sanitize: empty input → repetition_detected == False",
        metrics["repetition_detected"] is False,
    )


def test_sanitize_loc_only_no_repetition():
    loc_only = "<|LOC_0|><|LOC_1|><|LOC_2|>"
    text, metrics = _sanitize_paddleocr_output(loc_only)
    _run(
        "sanitize: LOC-only input → 3 tokens removed",
        metrics["loc_tokens_removed"] == 3,
    )
    _run(
        "sanitize: LOC-only input → no repetition flagged (trivial empty result)",
        metrics["repetition_detected"] is False,
    )


def test_sanitize_detects_excessive_loc_tokens():
    text, metrics = _sanitize_paddleocr_output(EXCESSIVE_LOC_FIXTURE)
    _run(
        f"sanitize: LOC tokens removed == 4 (got {metrics['loc_tokens_removed']})",
        metrics["loc_tokens_removed"] == 4,
    )
    _run(
        "sanitize: excessive LOC tokens detected repetition",
        metrics["repetition_detected"] is True
        and any("excessive_loc_tokens" in r for r in metrics["repetition_reasons"]),
    )


def test_sanitize_detects_bigram_stuttering():
    text, metrics = _sanitize_paddleocr_output(BIGRAM_STUTTERING_FIXTURE)
    _run(
        "sanitize: bigram stuttering detected repetition",
        metrics["repetition_detected"] is True
        and any("consecutive_bigram_repeat" in r for r in metrics["repetition_reasons"]),
    )


def test_sanitize_detects_low_lexical_diversity():
    text, metrics = _sanitize_paddleocr_output(LOW_DIVERSITY_FIXTURE)
    _run(
        "sanitize: low lexical diversity detected repetition",
        metrics["repetition_detected"] is True
        and any("low_unique_word_ratio" in r for r in metrics["repetition_reasons"]),
    )


def test_sanitize_detects_garbage_symbols():
    text, metrics = _sanitize_paddleocr_output(GARBAGE_SYMBOLS_FIXTURE)
    _run(
        "sanitize: garbage dots detected repetition",
        metrics["repetition_detected"] is True
        and any("excessive_dots" in r for r in metrics["repetition_reasons"]),
    )


def test_sanitize_detects_garbage_slashes():
    text, metrics = _sanitize_paddleocr_output(GARBAGE_SLASHES_FIXTURE)
    _run(
        "sanitize: garbage slashes detected repetition",
        metrics["repetition_detected"] is True
        and any("excessive_slashes" in r for r in metrics["repetition_reasons"]),
    )


def test_is_line_gibberish():
    # 1. Inverted stamp text common in margins
    inverted_line = "so '6zS's-l' u qos B!!xnv ous!ai tO'u"
    _run("is_line_gibberish: inverted line returns True", _is_line_gibberish(inverted_line) is True)
    
    # 2. Mostly symbol lines (repeated characters)
    symbol_line = "-=-=-=-=-=-=-=-=-=-=-="
    _run("is_line_gibberish: symbol line returns True", _is_line_gibberish(symbol_line) is True)
    
    # 3. Valid Portuguese legal line
    valid_line = "GILBERTO PAVAN do comercio portador do RG 7.352.178"
    _run("is_line_gibberish: valid legal line returns False", _is_line_gibberish(valid_line) is False)


def test_get_useful_text():
    raw_document = (
        "CNM: 121095.2.0000905-60\n"
        "LIVRO N.o 2 - REGISTRO GERAL\n"
        "GILBERTO PAVAN do comercio portador do RG 7.352.178\n"
        "Para conferir o original, acesse o site..."
    )
    useful = _get_useful_text(raw_document)
    _run("get_useful_text: standard header and verification lines are stripped", "GILBERTO PAVAN" in useful and "CNM" not in useful and "LIVRO" not in useful)


def test_sanitize_detects_insufficient_useful_text():
    # A page containing only a header date and page standalone numbers
    only_header = (
        "51098 14 de fevereiro de 2024 16:17:24.7\n"
        "CNM: 121095.2.0000905-60\n"
        "fls. 36\n"
        "Matricula 905\n"
        "1210953C30E0000007697024K"
    )
    text, metrics = _sanitize_paddleocr_output(only_header)
    _run("sanitize: insufficient useful text detected repetition/insufficient text", metrics["repetition_detected"] is True and "insufficient_useful_text" in metrics["repetition_reasons"])


def test_is_line_gibberish_detects_marginal_stamps():
    line_a = "so '6zS's-l' u qos B!!xnv ous!ai tO'u oi!! ou eep cusaw eisau epels!Sa"
    line_b = "ngagop'apepua&opiajas O opeoaua eoy v/S lseg op oauc8 op Jonej wa noa8"
    _run("is_line_gibberish detects marginal stamp A", _is_line_gibberish(line_a) is True)
    _run("is_line_gibberish detects marginal stamp B", _is_line_gibberish(line_b) is True)


def test_is_line_gibberish_preserves_juridical_content():
    # Lines that the old logic incorrectly flagged as gibberish — must be preserved.
    cases = [
        # Juridical terms not previously in the reference set
        ("hipoteca cedular de primeiro grau e sem concorrência de terceiros", "hipoteca/terceiros line"),
        ("Por Cédula de Crédito Comercial, n.", "cedula/credito/comercial line"),
        ("R.7, em data de 29 dc maio dc 1.998.", "registration entry with date"),
        ("hipoteca cedular de primeiro grau e sem concorrência de terceiros, a favor do BANCO DO", "hipoteca with banco"),
        # Continuation/header notes
        ("continuação de ficha nº03.", "continuation note with ficha"),
        # Proper names (not in reference set but clearly valid)
        ("MARIA ALVES DA SILVA CONTRUCCI", "all-caps proper name"),
        ("Rosaldo Del Pesó Guerreiro", "mixed-case proper name"),
    ]
    for line, label in cases:
        _run(
            f"is_line_gibberish: {label} returns False",
            _is_line_gibberish(line) is False,
        )


def test_intrusive_symbol_ratio_penalizes_poor_ocr():
    poor_ocr = "CERTIFICO E DOU FE que a presente certid&o eiatrönlco"
    ratio = _intrusive_symbol_ratio(poor_ocr)
    _run(f"intrusive symbol ratio detected ({ratio:.3f}) > 0.05", ratio > 0.05)
    score = _ocr_post_quality_score(poor_ocr)
    _run(f"ocr post quality is penalized below threshold ({score:.3f})", score < MIN_OCR_POST_QUALITY)


def test_sanitize_tracks_cleaning_telemetry():
    dirty_text = "GILBERTO PAVAN do comercio\nso '6zS's-l' u qos B!!xnv\noutro texto legitimo"
    clean, metrics = _sanitize_paddleocr_output(dirty_text)
    _run("sanitize: tracks removed gibberish lines count", metrics["gibberish_lines_removed"] == 1)
    _run("sanitize: records removed lines list", "so '6zS's-l' u qos B!!xnv" in metrics["gibberish_lines_removed_list"])
    _run("sanitize: tracks score before", metrics["score_before"] is not None)
    _run("sanitize: tracks score after", metrics["score_after"] is not None)
    _run("sanitize: determines confidence as accepted_with_cleaning", metrics["confidence"] == "accepted_with_cleaning")



# ---------------------------------------------------------------------------
# Tests for _run_local_ocr (T13)
# ---------------------------------------------------------------------------

def test_run_local_ocr_returns_str_or_none():
    result = _run_local_ocr(b"not-a-real-image")
    _run(
        "_run_local_ocr: returns str or None (never raises)",
        result is None or isinstance(result, str),
    )


def test_run_local_ocr_valid_png_returns_str_or_none():
    png_bytes = _make_png_bytes(width=64, height=64, color=200)
    result = _run_local_ocr(png_bytes)
    _run(
        "_run_local_ocr: valid PNG input returns str or None (never raises)",
        result is None or isinstance(result, str),
    )


# ---------------------------------------------------------------------------
# Tests for _pick_best_ocr (T14) — dual-backend selection logic
# ---------------------------------------------------------------------------

GOOD_TEXT = (
    "Por meio desta petição, o requerente vem, com fundamento no artigo 300 "
    "do Código de Processo Civil, requerer a concessão de tutela de urgência, "
    "demonstrando a probabilidade do direito e o perigo de dano irreparável."
)

assert _ocr_post_quality_score(GOOD_TEXT) >= MIN_OCR_POST_QUALITY, (
    f"GOOD_TEXT score {_ocr_post_quality_score(GOOD_TEXT):.3f} must be >= {MIN_OCR_POST_QUALITY}"
)


def test_pick_best_ocr_both_unavailable():
    text, status, mode, reason, scores = _pick_best_ocr([
        (None, "local_ocr"),
        (None, "lm_studio_ocr"),
    ])
    _run(
        "pick_best_ocr: both unavailable → status=ocr_backend_unavailable",
        status == "ocr_backend_unavailable",
    )
    _run(
        "pick_best_ocr: both unavailable → text=[ocr_backend_unavailable]",
        text == "[ocr_backend_unavailable]",
    )
    _run(
        "pick_best_ocr: both unavailable → scores are None",
        scores.get("local_ocr") is None and scores.get("lm_studio_ocr") is None,
    )


def test_pick_best_ocr_both_poor_quality():
    text, status, mode, reason, scores = _pick_best_ocr([
        (CORRUPTED_OCR_FIXTURE, "local_ocr"),
        (CORRUPTED_OCR_FIXTURE, "lm_studio_ocr"),
    ])
    _run(
        "pick_best_ocr: both poor quality → status=low_ocr_quality",
        status == "low_ocr_quality",
    )
    _run(
        "pick_best_ocr: both poor quality → text=[low_ocr_quality]",
        text == "[low_ocr_quality]",
    )
    _run(
        "pick_best_ocr: both poor quality → mode=none",
        mode == "none",
    )


def test_pick_best_ocr_local_good_vl_unavailable():
    text, status, mode, reason, scores = _pick_best_ocr([
        (GOOD_TEXT, "local_ocr"),
        (None, "lm_studio_ocr"),
    ])
    _run(
        "pick_best_ocr: local good, vl unavailable → mode=local_ocr",
        mode == "local_ocr",
    )
    _run(
        "pick_best_ocr: local good, vl unavailable → status=ok",
        status == "ok",
    )
    _run(
        "pick_best_ocr: local good, vl unavailable → score_local set",
        scores.get("local_ocr") is not None and scores["local_ocr"] >= MIN_OCR_POST_QUALITY,
    )
    _run(
        "pick_best_ocr: local good, vl unavailable → score_vl is None",
        scores.get("lm_studio_ocr") is None,
    )


def test_pick_best_ocr_vl_good_local_unavailable():
    text, status, mode, reason, scores = _pick_best_ocr([
        (None, "local_ocr"),
        (GOOD_TEXT, "lm_studio_ocr"),
    ])
    _run(
        "pick_best_ocr: vl good, local unavailable → mode=lm_studio_ocr",
        mode == "lm_studio_ocr",
    )
    _run(
        "pick_best_ocr: vl good, local unavailable → status=ok",
        status == "ok",
    )


def test_pick_best_ocr_local_poor_vl_good():
    text, status, mode, reason, scores = _pick_best_ocr([
        (CORRUPTED_OCR_FIXTURE, "local_ocr"),
        (GOOD_TEXT, "lm_studio_ocr"),
    ])
    _run(
        "pick_best_ocr: local poor, vl good → mode=lm_studio_ocr",
        mode == "lm_studio_ocr",
    )
    _run(
        "pick_best_ocr: local poor, vl good → status=ok",
        status == "ok",
    )
    _run(
        "pick_best_ocr: local poor, vl good → reason=unico_aprovado",
        reason == "unico_aprovado",
    )


def test_pick_best_ocr_both_good_prefers_higher_score():
    # Use the same good text for both — should return one of them
    text, status, mode, reason, scores = _pick_best_ocr([
        (GOOD_TEXT, "local_ocr"),
        (GOOD_TEXT, "lm_studio_ocr"),
    ])
    _run(
        "pick_best_ocr: both good → status=ok",
        status == "ok",
    )
    _run(
        "pick_best_ocr: both good → mode is one of the backends",
        mode in ("local_ocr", "lm_studio_ocr"),
    )
    _run(
        "pick_best_ocr: both good → reason=score_superior",
        reason == "score_superior",
    )


def test_pick_best_ocr_single_candidate_good():
    text, status, mode, reason, scores = _pick_best_ocr([
        (GOOD_TEXT, "local_ocr"),
    ])
    _run(
        "pick_best_ocr: single candidate good → reason=unico_disponivel",
        reason == "unico_disponivel",
    )
    _run(
        "pick_best_ocr: single candidate good → status=ok",
        status == "ok",
    )


# ---------------------------------------------------------------------------
# Helper: simula a lógica de decision_log do _extract_pymupdf
# (para testes de rastreabilidade sem precisar invocar PyMuPDF)
# ---------------------------------------------------------------------------

def _build_decision_log(candidates: list) -> dict:
    """Replica o trecho decision_log/final_decision/markdown_output de _extract_pymupdf."""
    raw, status, ocr_mode, reason, scores = _pick_best_ocr(candidates)
    details = scores.get("details", {})
    chosen_det = details.get(ocr_mode, {}) if ocr_mode in details else {}
    used_ocr = ocr_mode not in ("none", "")
    confidence = chosen_det.get("confidence", "low_ocr_quality") if used_ocr else "low_ocr_quality"

    if status == "ok":
        decision_log = confidence
        final_decision = confidence
        markdown_output = "text"
    else:
        decision_log = status
        final_decision = status
        markdown_output = f"[{status}]"

    return {
        "raw": raw,
        "status": status,
        "ocr_mode": ocr_mode,
        "decision_log": decision_log,
        "final_decision": final_decision,
        "markdown_output": markdown_output,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Tests: rastreabilidade — decision nunca é "ok"
# ---------------------------------------------------------------------------

REPEATED_GOOD_TEXT = "\n".join(["Certidão de imóvel. Registro de imóveis."] * 10)

def test_decision_log_never_ok_when_status_ok():
    result = _build_decision_log([(None, "local_ocr"), (GOOD_TEXT, "lm_studio_ocr")])
    _run(
        f"decision_log never 'ok' when status=ok (got '{result['decision_log']}')",
        result["decision_log"] != "ok",
    )
    _run(
        f"decision_log is 'accepted' or 'accepted_with_cleaning' when status=ok (got '{result['decision_log']}')",
        result["decision_log"] in ("accepted", "accepted_with_cleaning"),
    )


def test_decision_log_never_ok_when_status_low_ocr_quality():
    result = _build_decision_log([(CORRUPTED_OCR_FIXTURE, "local_ocr"), (CORRUPTED_OCR_FIXTURE, "lm_studio_ocr")])
    _run(
        f"decision_log never 'ok' when status=low_ocr_quality (got '{result['decision_log']}')",
        result["decision_log"] != "ok",
    )
    _run(
        f"decision_log == 'low_ocr_quality' when all backends fail (got '{result['decision_log']}')",
        result["decision_log"] == "low_ocr_quality",
    )


def test_decision_log_never_ok_when_no_backend():
    result = _build_decision_log([(None, "local_ocr"), (None, "lm_studio_ocr")])
    _run(
        f"decision_log never 'ok' when no backend available (got '{result['decision_log']}')",
        result["decision_log"] != "ok",
    )
    _run(
        f"decision_log == 'ocr_backend_unavailable' when no backend (got '{result['decision_log']}')",
        result["decision_log"] == "ocr_backend_unavailable",
    )


def test_final_decision_matches_markdown_output_ok_path():
    result = _build_decision_log([(None, "local_ocr"), (GOOD_TEXT, "lm_studio_ocr")])
    _run(
        f"final_decision matches markdown when status=ok: final_decision={result['final_decision']!r} markdown_output={result['markdown_output']!r}",
        result["final_decision"] in ("accepted", "accepted_with_cleaning")
        and result["markdown_output"] == "text",
    )


def test_final_decision_matches_markdown_output_low_quality_path():
    result = _build_decision_log([(CORRUPTED_OCR_FIXTURE, "local_ocr"), (CORRUPTED_OCR_FIXTURE, "lm_studio_ocr")])
    _run(
        f"final_decision matches markdown when low_ocr_quality: final_decision={result['final_decision']!r} markdown_output={result['markdown_output']!r}",
        result["final_decision"] == "low_ocr_quality"
        and result["markdown_output"] == "[low_ocr_quality]",
    )


def test_post_gate_traces_repetition_detected():
    """Candidato com score_after alto mas repetition_detected=True.
    Log deve mostrar post_gate=repetition_detected, final_decision=low_ocr_quality.
    """
    raw, status, ocr_mode, reason, scores = _pick_best_ocr([
        (None, "local_ocr"),
        (REPEATED_GOOD_TEXT, "lm_studio_ocr"),
    ])
    details = scores.get("details", {})
    lm_det = details.get("lm_studio_ocr", {})

    # score forçado a 0 por repetição
    score_vl = scores.get("lm_studio_ocr")

    _run(
        f"post_gate trace: repetition forced effective score to 0 (got {score_vl})",
        score_vl is not None and score_vl == 0.0,
    )
    _run(
        f"post_gate trace: status=low_ocr_quality when repetition_detected (got {status!r})",
        status == "low_ocr_quality",
    )

    # selected_score (score_after real, antes da penalidade) deve ser > 0
    all_scored = [
        (det.get("score_after", 0.0), name, det)
        for name, det in details.items()
        if isinstance(det, dict) and det.get("score") is not None
    ]
    selected_score = max(all_scored, key=lambda x: x[0])[0] if all_scored else 0.0
    post_gate = "repetition_detected" if lm_det.get("repetition_detected") else "none"
    post_gate_reason = lm_det.get("repetition_reasons", ["none"])[0] if lm_det.get("repetition_detected") else "none"

    _run(
        f"post_gate trace: post_gate=repetition_detected (got {post_gate!r})",
        post_gate == "repetition_detected",
    )
    _run(
        f"post_gate trace: post_gate_reason starts with 'line_repeat' (got {post_gate_reason!r})",
        post_gate_reason.startswith("line_repeat"),
    )
    # final_decision deve ser low_ocr_quality
    result = _build_decision_log([(None, "local_ocr"), (REPEATED_GOOD_TEXT, "lm_studio_ocr")])
    _run(
        f"post_gate trace: final_decision=low_ocr_quality (got {result['final_decision']!r})",
        result["final_decision"] == "low_ocr_quality",
    )
    _run(
        f"post_gate trace: markdown_output=[low_ocr_quality] (got {result['markdown_output']!r})",
        result["markdown_output"] == "[low_ocr_quality]",
    )


# ---------------------------------------------------------------------------
# Tests for _heading_level — regression for false heading generation
#
# Bug A: ALL-CAPS rule matched single-word fragments (e.g. "NULIDADE" alone)
#        and lines ending with ";" (e.g. "ADMINISTRADORA LTDA.;") or with a
#        single trailing letter (e.g. "HIPOTECAR: A").
# Bug B: Numbered rule matched article/law/registration references as headings
#        (e.g. "166 do CC/2002:", "1.015 do Código Civil)", "905 em relação à autora").
#        Numbered rule was removed entirely — it creates no correct headings in
#        Brazilian legal petitions and only produces false positives.
# ---------------------------------------------------------------------------

# Lines that must NOT become headings
_HEADING_FALSE_POSITIVES = [
    ("ADMINISTRADORA LTDA.;", "ends with ';' — continuation"),
    ("ADMINISTRADORA LTDA;", "ends with ';' — continuation (no dot)"),
    ("166 do CC/2002:", "article reference — numbered"),
    ("1.015 do Código Civil) e desvio de finalidade", "article reference — numeric dotted"),
    ("905 em relação à autora e à empresa JKMG", "registration number — start of sentence"),
    ("NULIDADE", "single-word fragment"),
    ("AUSÊNCIA TOTAL DE PODERES PARA HIPOTECAR: A", "trailing single letter 'A'"),
    ("LTDA., E", "ends with single letter 'E'"),
]

# Lines that MUST remain headings
_HEADING_REAL = [
    ("DOS FATOS", "standard section heading"),
    ("DO DIREITO:", "section heading ending with ':'"),
    ("DOS PEDIDOS:", "section heading ending with ':'"),
    ("DA PROCURAÇÃO SEM PODERES ESPECIAIS", "section heading with preposition"),
    ("DA QUALIFICAÇÃO E LEGITIMIDADE ATIVA", "section heading — legitimidade"),
    ("DO ATO ULTRA VIRES SOCIETÁRIO", "section heading — ultra vires"),
    ("DA NULIDADE ABSOLUTA POR AUSÊNCIA DE PODERES ESPECIAIS -", "section heading ending with '-'"),
    ("DA INEFICÁCIA DO ATO PERANTE A OUTORGANTE (MANDANTE)", "section heading with parens"),
    ("DA IMPRESCRITIBILIDADE DA PRETENSÃO DECLARATÓRIA DE", "multi-line heading — first line"),
    ("DO ATO ULTRA VIRES SOCIETÁRIO (FUNDAMENTO SUBSIDIÁRIO)", "section heading — subsidiary"),
    ("DECLARATÓRIA DE NULIDADE", "petition title fragment"),
    ("DOS FATOS:", "section heading — exactly 80% uppercase (boundary case)"),
]


def test_heading_level_rejects_false_positives():
    """_heading_level must NOT produce headings for continuations and numeric refs."""
    for line, label in _HEADING_FALSE_POSITIVES:
        _run(
            f"_heading_level: not a heading — '{label}'",
            _heading_level(line) is None,
        )


def test_heading_level_preserves_real_headings():
    """_heading_level must still recognize real section headings."""
    for line, label in _HEADING_REAL:
        _run(
            f"_heading_level: is a heading — '{label}'",
            _heading_level(line) is not None,
        )


# ---------------------------------------------------------------------------
# Tests for _is_native_text_gibberish — regression for content loss bug
#
# Bug: _is_line_gibberish was applied to native PyMuPDF text. Rule 4
# (vocabulary check) incorrectly removed valid legal lines containing
# mixed alphanumeric content (CNPJ, addresses, article numbers) when
# meaningful words were absent from the reference set but the line was
# structurally valid. _is_native_text_gibberish replaces it with a
# conservative filter that only removes near-zero-letter-density artifacts
# and rotated-stamp quote-chaos.
# ---------------------------------------------------------------------------

# Lines that _is_line_gibberish incorrectly removed from native text
_NATIVE_VALID_LINES = [
    ("00.000.000/0001-91, com sede na Capital Federal e Unidade Regional", "CNPJ + sede (p1)"),
    ("nº 7-51, Bauru/SP; pelos fatos e fundamentos jurídicos a seguir", "endereço + fundamentos (p1)"),
    ("das Pessoas Naturais do 37º Subdistrito - Aclimação - São Paulo/SP", "cartório subdistrito (p2)"),
    ("assinar em nome delas OUTORGANTES, Confissão de Dívidas junto ao BANCO DO BRASIL S/A", "poderes procuração (p2)"),
    ("consequente liquidação de seu patrimônio, na forma dos arts. 1.102 a 1.112", "patrimônio/arts (p4)"),
    ("7.013, 946 e 905 foram atribuídos à autora JURACI PIRES PAVAN", "imóveis (p4)"),
    ("registrada e publicada na JUCESP desde 18/01/2002, ou seja, seis meses", "JUCESP (p6)"),
    ("Art. 145 – É nulo o ato jurídico:", "art 145 (p6)"),
    ("Art. 661, §1º...", "art 661 (p7)"),
    ("Art. 166 – É nulo o negócio jurídico quando:", "art 166 (p7)"),
    ("Lei 10.406/2002, art. 169: O negócio jurídico nulo não é suscetível de confirmação", "lei/art completo"),
    ("arts. 1.295, §1º, 661, §1º, 145, III, 166, IV", "referências múltiplas (p10)"),
]

# Lines that must still be flagged as native-text gibberish (stamp artifacts)
_NATIVE_ARTIFACT_LINES = [
    ("so '6zS's-l' u qos B!!xnv ous!ai tO'u", "inverted stamp (low letter + quote chaos)"),
    ("!!! ¡¡¡ ))) *** +++ ###", "symbol-only line"),
]


def test_native_text_gibberish_preserves_legal_content():
    """_is_native_text_gibberish must NOT remove any valid legal line."""
    for line, label in _NATIVE_VALID_LINES:
        _run(
            f"_is_native_text_gibberish: preserves '{label}'",
            _is_native_text_gibberish(line) is False,
        )


def test_native_text_gibberish_removes_stamp_artifacts():
    """_is_native_text_gibberish must remove clear stamp/artifact lines."""
    for line, label in _NATIVE_ARTIFACT_LINES:
        _run(
            f"_is_native_text_gibberish: removes '{label}'",
            _is_native_text_gibberish(line) is True,
        )


def test_native_text_gibberish_short_line_not_flagged():
    """Lines < 8 chars must never be flagged (too short to reliably detect artifacts)."""
    for short in ["", "x", "ok", "§1º", "nº"]:
        _run(
            f"_is_native_text_gibberish: short/empty '{short}' not flagged",
            _is_native_text_gibberish(short) is False,
        )


def test_is_line_gibberish_still_catches_ocr_noise():
    """_is_line_gibberish (for OCR output) must still catch all its original targets.
    This confirms the OCR filter was not degraded by the native text fix.
    """
    ocr_noise_lines = [
        ("so '6zS's-l' u qos B!!xnv ous!ai tO'u oi!! ou eep cusaw eisau", "inverted stamp A"),
        ("ngagop'apepua&opiajas O opeoaua eoy v/S lseg op oauc8 op Jonej", "inverted stamp B"),
        ("-=-=-=-=-=-=-=-=-=-=-=", "symbol repeat"),
    ]
    for line, label in ocr_noise_lines:
        _run(
            f"_is_line_gibberish: still catches OCR noise '{label}'",
            _is_line_gibberish(line) is True,
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
        test_lm_studio_unavailable_error_importable,
        test_lm_studio_ocr_timeout_default,
        test_lm_studio_ocr_timeout_from_env,
        test_lm_studio_ocr_raises_when_env_vars_absent,
        test_lm_studio_ocr_raises_when_base_url_absent,
        # T11: _sanitize_paddleocr_output
        test_sanitize_removes_loc_tokens,
        test_sanitize_detects_oo_dash_sequence,
        test_sanitize_detects_repeated_lines,
        test_sanitize_detects_repeated_numbers,
        test_sanitize_clean_text_no_false_positive,
        test_sanitize_empty_text,
        test_sanitize_loc_only_no_repetition,
        test_sanitize_detects_excessive_loc_tokens,
        test_sanitize_detects_bigram_stuttering,
        test_sanitize_detects_low_lexical_diversity,
        test_sanitize_detects_garbage_symbols,
        test_sanitize_detects_garbage_slashes,
        test_is_line_gibberish,
        test_get_useful_text,
        test_sanitize_detects_insufficient_useful_text,
        test_is_line_gibberish_detects_marginal_stamps,
        test_is_line_gibberish_preserves_juridical_content,
        test_intrusive_symbol_ratio_penalizes_poor_ocr,
        test_sanitize_tracks_cleaning_telemetry,
        # T16: _run_local_ocr
        test_run_local_ocr_returns_str_or_none,
        test_run_local_ocr_valid_png_returns_str_or_none,
        # T16: _pick_best_ocr
        test_pick_best_ocr_both_unavailable,
        test_pick_best_ocr_both_poor_quality,
        test_pick_best_ocr_local_good_vl_unavailable,
        test_pick_best_ocr_vl_good_local_unavailable,
        test_pick_best_ocr_local_poor_vl_good,
        test_pick_best_ocr_both_good_prefers_higher_score,
        test_pick_best_ocr_single_candidate_good,
        # Rastreabilidade: decision nunca é "ok"; final_decision ↔ markdown coerentes
        test_decision_log_never_ok_when_status_ok,
        test_decision_log_never_ok_when_status_low_ocr_quality,
        test_decision_log_never_ok_when_no_backend,
        test_final_decision_matches_markdown_output_ok_path,
        test_final_decision_matches_markdown_output_low_quality_path,
        test_post_gate_traces_repetition_detected,
        # Regressão: _heading_level não gera headings falsos
        test_heading_level_rejects_false_positives,
        test_heading_level_preserves_real_headings,
        # Regressão: _is_native_text_gibberish não remove conteúdo jurídico válido
        test_native_text_gibberish_preserves_legal_content,
        test_native_text_gibberish_removes_stamp_artifacts,
        test_native_text_gibberish_short_line_not_flagged,
        test_is_line_gibberish_still_catches_ocr_noise,
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
