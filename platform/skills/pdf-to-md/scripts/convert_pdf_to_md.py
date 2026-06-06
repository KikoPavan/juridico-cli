#!/usr/bin/env python3
"""
pdf-to-md · convert_pdf_to_md.py
=================================
Converte um arquivo PDF em Markdown bruto com anchors [[Pág. N]] por página.
Híbrido: texto nativo via PyMuPDF; OCR via PaddleOCR para páginas escaneadas.

Uso:
    python convert_pdf_to_md.py --input DOC.pdf --output DOC.md [opções]

Opções:
    --input PATH      Caminho do PDF de entrada (obrigatório)
    --output PATH     Caminho do .md de saída (obrigatório)
    --engine ENGINE   Motor: auto|pdfminer|pymupdf (padrão: auto)
    --no-markers      Não inserir anchors [[Pág. N]]
    --verbose         Log detalhado por página no stderr
    --report          Gerar conversion_report.md junto ao output

Exit codes: 0=ok  1=input_error  2=extract_error  3=write_error
"""

import argparse
import datetime
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

EXIT_OK, EXIT_INPUT_ERROR, EXIT_EXTRACT_ERROR, EXIT_WRITE_ERROR = 0, 1, 2, 3

# Anchor format per spec (tasks.md §2)
PAGE_ANCHOR_TPL = "[[Pág. {n}]]"

# Density thresholds for OCR fallback decision (tasks.md §3)
MIN_CHARS_FOR_TEXT = 50    # minimum useful characters per page
MIN_PRINTABLE_RATIO = 0.6  # minimum ratio of printable chars
MIN_TEXT_QUALITY = 0.45    # minimum heuristic quality score (space density + long-token ratio)
MIN_OCR_POST_QUALITY = MIN_TEXT_QUALITY  # minimum post-OCR quality score (design decision 5)
# Ratio of lines with ≤ 2 non-whitespace chars that signals garbled/fragmented OCR text.
# Normal Portuguese prose: < 5%. Scanned docs with per-char OCR extraction: > 15%.
SHORT_LINE_RATIO_THRESHOLD = 0.15
# Case-chaos thresholds for post-OCR quality detection.
# Good OCR output: ~0% chaotic words. Corrupted OCR: 4–10%+.
OCR_CHAOS_NOISE_FLOOR = 0.02   # chaos below this is within normal OCR noise
OCR_CHAOS_SATURATION  = 0.06   # chaos at or above this → maximum penalty (score → 0)

OUTPUT_ENCODING = "utf-8"
OCR_RENDER_SCALE = 300 / 72.0  # scale factor for page-to-image (300 DPI)

LM_STUDIO_BASE_URL_ENV = "LM_STUDIO_BASE_URL"
LM_STUDIO_OCR_MODEL_ENV = "LM_STUDIO_OCR_MODEL"
LM_STUDIO_OCR_TIMEOUT_ENV = "LM_STUDIO_OCR_TIMEOUT_SECONDS"
_LM_STUDIO_OCR_TIMEOUT_DEFAULT = 300  # seconds per page; override via LM_STUDIO_OCR_TIMEOUT_SECONDS

LM_STUDIO_OCR_PROMPT = (
    "OCR: Extract only the readable text from this image. "
    "Return only the recognized text. Do not include bounding boxes, "
    "coordinates, layout tokens, explanations, summaries, or repeated filler."
)

_local_paddle_ocr_instance = None  # lazy-init cache for local PaddleOCR
_local_paddle_ocr_checked = False  # True once initialization has been attempted

# PaddleOCR-VL output sanitization patterns
LOC_TOKEN_RE = re.compile(r"<\|LOC_[^|]*\|>")
_OCR_OO_DASH_RE = re.compile(r"(?:o-){4,}", re.IGNORECASE)
_OCR_REPETITION_LINE_THRESHOLD = 3   # same non-trivial line repeated > this many times → excessive
_OCR_REPETITION_NUMBER_THRESHOLD = 3  # same 4+ digit sequence repeated > this many times → excessive

# ---------------------------------------------------------------------------
# Boilerplate patterns for Brazilian legal documents
# Lines matching any of these are discounted before the OCR decision.
# ---------------------------------------------------------------------------
BOILERPLATE_PATTERNS: list[re.Pattern] = [
    # Page numbering: "Fls. 42", "fl. 5", "Fl.42", "fls.5"
    re.compile(r"^\s*[Ff]l[s]?\.?\s*\d+\s*$"),
    # Standalone page numbers: "42", " 5 " (1–4 digits only)
    re.compile(r"^\s*\d{1,4}\s*$"),
    # Court identifiers
    re.compile(r"^\s*TRIBUNAL\s+DE\s+JUSTI[CÇ]A", re.IGNORECASE),
    re.compile(r"^\s*PODER\s+JUDICI[AÁ]RIO", re.IGNORECASE),
    re.compile(r"^\s*JUSTI[CÇ]A\s+(DO\s+)?ESTADO", re.IGNORECASE),
    # Foro / Vara / Comarca headers
    re.compile(r"^\s*FORO\s+", re.IGNORECASE),
    re.compile(r"^\s*VARA\s+", re.IGNORECASE),
    re.compile(r"^\s*COMARCA\s+DE\s+", re.IGNORECASE),
    # Institutional addresses
    re.compile(r"^\s*(Avenida|Av\.|Rua|Pra[cç]a|Alameda)\s+", re.IGNORECASE),
    # Contact info / Footer emails/phones
    re.compile(r".*cartorioderegistrode.*@gmail\.com.*", re.IGNORECASE),
    re.compile(r".*Tel\.\s*\(?\d{2}\)?\s*\d{4}.*", re.IGNORECASE),
    # Internal page anchor [[Pág. N]]
    re.compile(r"^\s*\[\[P[áa]g\.\s*\d+\]\]\s*$"),
    # "Página N de M" / "Pág. N / M"
    re.compile(r"^\s*[Pp][áa]g(?:ina|\.)\s*\d+\s*(?:de|/)\s*\d+\s*$"),
    # Electronic signature footers common in e-process PDFs
    re.compile(r"^\s*Assinado\s+eletronicamente\s+por", re.IGNORECASE),
    re.compile(r"^\s*Este\s+documento\s+[eé]\s+c[oó]pia", re.IGNORECASE),
    # ESAJ verification footer: "Para conferir o original, acesse o site..."
    re.compile(r"^\s*Para\s+conferir\s+o\s+original", re.IGNORECASE),
    # Horizontal rule lines (5+ dashes, underscores or equals)
    re.compile(r"^\s*[-_=]{5,}\s*$"),
]

# Metadata patterns commonly found in legal document headers or stamps
DOCUMENT_METADATA_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\s*CNM\s*:\s*[a-zA-Z0-9.-]+\s*$", re.IGNORECASE),
    re.compile(r"^\s*MATR[IÍ]CULA\s*:?\s*\d*\s*$", re.IGNORECASE),
    re.compile(r"^\s*FICHA\s*:?\s*\d*\s*$", re.IGNORECASE),
    re.compile(r"^\s*LIVRO\s+N\.?[oº°]?\s*\d+.*$", re.IGNORECASE),
    re.compile(r"^\s*SELO\s+DIGITAL\s*:?\s*[a-zA-Z0-9]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*CUSTAS\s*$", re.IGNORECASE),
    re.compile(r"^\s*CERTID[AÃ]O\s*$", re.IGNORECASE),
    # Standalone dates like "14 de fevereiro de 2024" or "junho de 1987"
    re.compile(r"^\s*(\d{1,2}\s+de\s+)?[a-zA-ZçÇ]+\s+de\s+[12]\d{3}\s*$", re.IGNORECASE),
    re.compile(r"^\s*[a-zA-ZçÇ]+\s+de\s+[12]\d{3}\s*$", re.IGNORECASE),
    # Carimbo eletrônico de impressão TJSP
    re.compile(r"^\s*\d{5}[-\s]+\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+[12]\d{3}\s+\d{2}:\d{2}:\d{2}.*$", re.IGNORECASE),
    # Hash de selo digital isolado (25 chars alfanuméricos)
    re.compile(r"^\s*[a-zA-Z0-9]{25}\s*$", re.IGNORECASE),
]

# Set of valid documentary and legal words in Portuguese to detect gibberish.
# Words are stored without accents; comparison normalizes both sides via
# _COMMON_WORDS_NORMALIZED (built below) to catch accented OCR variants.
COMMON_WORDS_SIGNIFICANT: set[str] = {
    "residente", "domiciliado", "portador", "comercio", "estado", "cidade",
    "registro", "matricula", "imovel", "banco", "brasil", "cpc", "direito",
    "processo", "tabeliao", "certidao", "folhas", "livro", "geral", "comarca",
    "oficial", "proprietario", "proprietarios", "proprietaria", "proprietarias",
    "escritura", "compra", "venda", "vendeu", "adquirido", "adquiriu", "aquisicao",
    "notas", "prenotacao", "penhora", "execucao", "valor", "reais", "emolumentos",
    "selo", "digital", "conferir", "original", "site", "assinatura", "eletronica",
    "peticao", "requerente", "autor", "reu", "tutela", "urgencia", "pede", "deferimento",
    "termos", "civil", "codigo", "lei", "artigo", "resolucao", "decreto", "portaria",
    "vara", "foro", "tribunal", "justica", "poder", "judiciario", "copia",
    "autentica", "averbacao", "anexos", "brasileiro", "brasileira",
    "brasileiros", "brasileiras", "casado", "casada", "solteiro", "solteira", "viuvo",
    "viuva", "empresario", "empresaria", "comerciante", "lar", "advogado", "advogada",
    "professor", "professora", "maior", "menor", "escrevente", "substituto", "auxiliar",
    "conferir", "procedencia", "leitura", "code", "impresso", "acesse", "endereco",
    "eletronico", "tjsp", "jus", "br", "fls", "pag", "pagina", "paginas",
    "rua", "avenida", "praca", "alameda", "bairro", "cep", "telefone", "tel", "mail",
    "gmail", "outlook", "yahoo", "contato", "servico", "servicos", "cartorio", "cartorios",
    # Mortgage, credit and property law terms
    "hipoteca", "hipotecario", "hipotecaria",
    "cedula", "cedular", "credito", "subcredito",
    "comercial", "comerciais",
    "terceiro", "terceiros",
    "condomino", "condomina",
    "grau", "primeiro", "segundo",
    "juros", "vencimento", "prazo", "efetivo", "efetivos", "anual",
    "vigencia", "conforme", "retro",
    "cancelado", "cancelada", "cancelamento",
    # Common date words and months (appear in registration entries)
    "data", "maio", "junho", "julho", "agosto",
    "janeiro", "fevereiro", "marco", "abril",
    "setembro", "outubro", "novembro", "dezembro",
    # Registral/document structure terms
    "continuacao", "ficha", "documento", "presente", "constante",
    "versao", "numero", "proporcao", "proporcoes",
    "regime", "comunhao", "bens", "vigente",
    "devedor", "credor", "outorgante", "outorgado",
    "agencia", "empresa", "sociedade", "economia", "mista",
    # Court/enforcement terms
    "bloqueio", "judicial", "extrajudicial", "autos", "titulo",
    "depositario", "deposito", "bloqueado", "bloqueada",
}

# Pre-computed normalized form of COMMON_WORDS_SIGNIFICANT (NFKD, ASCII, lowercase).
# Used by _is_line_gibberish to match accented text variants from OCR output.
_COMMON_WORDS_NORMALIZED: frozenset[str] = frozenset(
    unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode("ascii").lower()
    for w in COMMON_WORDS_SIGNIFICANT
)

# Regex to detect strict intrusive symbols in the middle of alphabetic words
_OCR_INTRUSIVE_STRICT_RE = re.compile(
    r"[a-zA-ZáéíóúâêîôûãõçüöíÁÉÍÓÚÂÊÎÔÛÃÕÇÜÖÍ]"
    r"[&!'\"_*#·•▪▸]+"
    r"[a-zA-ZáéíóúâêîôûãõçüöíÁÉÍÓÚÂÊÎÔÛÃÕÇÜÖÍ]",
    re.IGNORECASE
)

# Regex to detect intrusive noise characters inside words indicating poor OCR substitutions
_OCR_INTRUSIVE_NOISE_RE = re.compile(
    r"[a-zA-Z0-9áéíóúâêîôûãõçíÁÉÍÓÚÂÊÎÔÛÃÕÇÍ]"
    r"[&+=%$#@*_üöÜÖ]"
    r"[a-zA-Z0-9áéíóúâêîôûãõçíÁÉÍÓÚÂÊÎÔÛÃÕÇÍ]"
)

# Patterns for repetitive separators or fillers that indicate gibberish VLM output
_OCR_REPETITIVE_SEPARATORS_RE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?:0-){4,}", re.IGNORECASE), "oo_dash_sequence"),
    (re.compile(r"(?:o-){4,}", re.IGNORECASE), "oo_dash_sequence"),
    (re.compile(r"(?:-0){4,}", re.IGNORECASE), "oo_dash_sequence"),
    (re.compile(r"(?:-o){4,}", re.IGNORECASE), "oo_dash_sequence"),
    (re.compile(r"(?://=){3,}", re.IGNORECASE), "excessive_slashes"),
    (re.compile(r"(?:=//){3,}", re.IGNORECASE), "excessive_slashes"),
    (re.compile(r"[-_=*#·•▪▸]{5,}"), "repeated_symbols"),
    (re.compile(r"(?:\.\s*){5,}"), "excessive_dots"),
    (re.compile(r"(?:/\s*){5,}"), "excessive_slashes"),
]



# ---------------------------------------------------------------------------
# LM Studio / PaddleOCR-VL — OCR via OpenAI-compatible vision API
# ---------------------------------------------------------------------------

def _lm_studio_ocr_timeout() -> int:
    try:
        return int(os.environ.get(LM_STUDIO_OCR_TIMEOUT_ENV, _LM_STUDIO_OCR_TIMEOUT_DEFAULT))
    except (ValueError, TypeError):
        return _LM_STUDIO_OCR_TIMEOUT_DEFAULT


class LmStudioUnavailableError(RuntimeError):
    """Raised when the LM Studio backend is unreachable or misconfigured."""


def _run_lm_studio_ocr(img_bytes: bytes) -> str:
    """Send page image to LM Studio/PaddleOCR-VL and return extracted text.

    Reads LM_STUDIO_BASE_URL and LM_STUDIO_OCR_MODEL from environment.
    Raises LmStudioUnavailableError if env vars are missing or the call fails.

    Tries data URI format first (standard OpenAI vision API); falls back to raw
    base64 without the data: prefix on HTTP 400, logging the error body each time.
    """
    import base64
    import json
    import urllib.error
    import urllib.request

    base_url = os.environ.get(LM_STUDIO_BASE_URL_ENV, "").rstrip("/")
    model = os.environ.get(LM_STUDIO_OCR_MODEL_ENV, "")

    if not base_url or not model:
        raise LmStudioUnavailableError(
            f"env vars not set: {LM_STUDIO_BASE_URL_ENV}, {LM_STUDIO_OCR_MODEL_ENV}"
        )

    timeout = _lm_studio_ocr_timeout()

    b64 = base64.b64encode(img_bytes).decode("ascii")
    endpoint = f"{base_url}/chat/completions"
    text_part = {
        "type": "text",
        "text": LM_STUDIO_OCR_PROMPT,
    }

    def _build_payload(image_url_value: str) -> dict:
        return {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url_value}},
                        text_part,
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0,
        }

    def _post(payload: dict) -> str:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            return body["choices"][0]["message"]["content"].strip()

    def _read_http_error_body(exc: urllib.error.HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")
        except Exception:
            return "<unable to read error body>"

    def _is_timeout(exc: BaseException) -> bool:
        if isinstance(exc, TimeoutError):
            return True
        if isinstance(exc, urllib.error.URLError):
            return isinstance(exc.reason, TimeoutError) or "timed out" in str(exc).lower()
        return False

    # Attempt 1: data URI (standard OpenAI vision format)
    try:
        return _post(_build_payload(f"data:image/png;base64,{b64}"))
    except urllib.error.HTTPError as exc:
        body1 = _read_http_error_body(exc)
        print(
            f"  [lm_studio_ocr] HTTP {exc.code} with data URI: {body1}",
            file=sys.stderr,
        )
        if exc.code != 400:
            raise LmStudioUnavailableError(
                f"LM Studio request failed: HTTP {exc.code} — {body1}"
            ) from exc
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, IndexError) as exc:
        if _is_timeout(exc):
            raise LmStudioUnavailableError(f"LM Studio OCR timed out after {timeout}s") from exc
        raise LmStudioUnavailableError(f"LM Studio request failed: {exc}") from exc

    # Attempt 2: raw base64 without data URI prefix (fallback for LM Studio variants)
    try:
        return _post(_build_payload(b64))
    except urllib.error.HTTPError as exc:
        body2 = _read_http_error_body(exc)
        raise LmStudioUnavailableError(
            f"LM Studio request failed: HTTP {exc.code}"
            f" (data URI and raw base64 both rejected) — {body2}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, IndexError) as exc:
        if _is_timeout(exc):
            raise LmStudioUnavailableError(
                f"LM Studio OCR timed out after {timeout}s (data URI and raw base64 both timed out)"
            ) from exc
        raise LmStudioUnavailableError(f"LM Studio request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Local PaddleOCR — optional candidate for quality-based OCR selection
# ---------------------------------------------------------------------------

def _get_local_paddle_ocr():
    """Lazy-init and cache local PaddleOCR instance. Returns None if unavailable."""
    global _local_paddle_ocr_instance, _local_paddle_ocr_checked
    if _local_paddle_ocr_checked:
        return _local_paddle_ocr_instance
    _local_paddle_ocr_checked = True
    try:
        from paddleocr import PaddleOCR
        _local_paddle_ocr_instance = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
    except Exception:
        _local_paddle_ocr_instance = None
    return _local_paddle_ocr_instance


def _run_local_ocr(img_bytes: bytes) -> str | None:
    """Run local PaddleOCR on img_bytes. Returns extracted text or None if unavailable/failed."""
    try:
        import io
        import numpy as np
        from PIL import Image

        ocr = _get_local_paddle_ocr()
        if ocr is None:
            return None

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_arr = np.array(img)
        result = ocr.ocr(img_arr, cls=True)

        lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if text_info:
                        lines.append(str(text_info[0]))
        return "\n".join(lines)
    except Exception as exc:
        print(f"  [local_ocr] falhou: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# PaddleOCR-VL output sanitization and quality validation
# ---------------------------------------------------------------------------

def _is_line_gibberish(line: str) -> bool:
    """True if a line consists of unusable OCR noise, inverted text, or symbol chaos."""
    trimmed = line.strip()
    if not trimmed:
        return False
    
    # 1. Se a linha for majoritariamente numérica (ex: processos, valores, CPF, tabelas), não é gibberish
    total_len = len(trimmed)
    digits = [c for c in trimmed if c.isdigit()]
    if total_len >= 8 and len(digits) / total_len >= 0.40:
        return False

    # Low letter ratio in printable characters (mostly symbols/numbers/noise)
    letters = [c for c in trimmed if c.isalpha()]
    if total_len >= 8:
        letter_ratio = len(letters) / total_len
        if letter_ratio < 0.40:
            return True


    # 2. Chaos of short words / case chaos / non-Portuguese noise
    words = trimmed.split()
    if len(words) >= 3:
        # If > 30% of the words are case-chaotic, the line is garbled
        chaotic_count = sum(1 for w in words if _is_case_chaotic(w))
        if chaotic_count / len(words) > 0.30:
            return True
            
        # Lines with many ultra-short disconnected words (e.g. per-char OCR noise)
        short_words = [w for w in words if len(w) <= 2]
        if len(short_words) / len(words) > 0.65:
            return True

    # 3. Strict intrusive symbols (typical of rotated stamps/noise in word middle)
    if len(words) >= 2:
        intrusive_count = sum(1 for w in words if len(w) >= 3 and _OCR_INTRUSIVE_STRICT_RE.search(w))
        if intrusive_count >= 2:
            return True

    # 4. Absence of legitimate documentary Portuguese words in longer text lines.
    # Normalizes accents (NFKD→ASCII) before comparison so that “Cédula” matches
    # “cedula” and “crédito” matches “credito” in the reference set.
    if len(words) >= 4:
        _sc = ":,.;!?()[]{}'\u201c\u201d\u2018\u2019-"
        clean_words = [
            unicodedata.normalize("NFKD", w.strip(_sc)).encode("ascii", "ignore").decode("ascii").lower()
            for w in words
            if len(w.strip(_sc)) >= 3
        ]
        if clean_words:
            has_legit = any(w in _COMMON_WORDS_NORMALIZED for w in clean_words)
            if not has_legit:
                # Only flag as gibberish when words also contain non-alphabetic noise.
                # Pure-alpha clean_words may be valid proper names (people, places)
                # not present in the reference set — do not remove those.
                has_suspicious = any(not w.isalpha() for w in clean_words)
                if has_suspicious:
                    return True
            
    # 5. Specific patterns of inverted/flipped stamps (common in e-process margins)
    # E.g. "so '6zS's-l' u qos B!!xnv"
    if re.search(r"[‘'\"`!]{2,}", trimmed) and len(letters) / total_len < 0.6:
        return True

    return False


def _get_useful_text(text: str) -> str:
    """Extract only the meaningful documentary content, discarding boilerplate and metadata."""
    if not text:
        return ""
    useful_lines = []
    for line in text.splitlines():
        trimmed = line.strip()
        if len(trimmed) < 4:
            continue
        # Check against standard boilerplate patterns
        if any(p.search(trimmed) for p in BOILERPLATE_PATTERNS):
            continue
        # Check against metadata patterns
        if any(p.search(trimmed) for p in DOCUMENT_METADATA_PATTERNS):
            continue
        useful_lines.append(trimmed)
    return "\n".join(useful_lines)


def _sanitize_paddleocr_output(text: str) -> tuple[str, dict]:
    """Remove PaddleOCR-VL artifacts, filter gibberish lines, and evaluate quality.

    Returns (sanitized_text, metrics):
        loc_tokens_removed       — number of <|LOC_...|> tokens stripped
        repetition_detected      — True if excessive repetition, symbols, or low quality found
        repetition_reasons       — list of detected pattern tags
        gibberish_lines_removed  — count of structural garbage lines deleted
    """
    metrics: dict = {
        "loc_tokens_removed": 0,
        "repetition_detected": False,
        "repetition_reasons": [],
        "gibberish_lines_removed": 0,
        "gibberish_lines_removed_list": [],
        "score_before": 0.0,
        "score_after": 0.0,
        "confidence": "accepted"
    }

    # 1. Remove <|LOC_...|> tokens
    cleaned, n_loc = LOC_TOKEN_RE.subn("", text)
    metrics["loc_tokens_removed"] = n_loc
    cleaned = cleaned.strip()

    # Reject if excessive LOC tokens are generated (indicates VLM alignment failure)
    if n_loc > 3:
        metrics["repetition_detected"] = True
        metrics["repetition_reasons"].append(f"excessive_loc_tokens:{n_loc}")

    # 2. Reject if repetitive separator patterns (dashes, dots, etc.) are found
    for pattern, reason in _OCR_REPETITIVE_SEPARATORS_RE:
        if pattern.search(cleaned):
            metrics["repetition_detected"] = True
            metrics["repetition_reasons"].append(reason)
            break

    # Calculate quality score BEFORE removing gibberish/noise lines
    metrics["score_before"] = _ocr_post_quality_score(cleaned)

    # 3. Filter out gibberish/noise lines (e.g. inverted margins, stamp noise)
    lines = cleaned.splitlines()
    good_lines = []
    removed_list = []
    for line in lines:
        if _is_line_gibberish(line):
            removed_list.append(line.strip())
        else:
            good_lines.append(line)
            
    metrics["gibberish_lines_removed"] = len(removed_list)
    metrics["gibberish_lines_removed_list"] = removed_list
    cleaned_document = "\n".join(good_lines).strip()

    # 4. Detect standard line repetition on the clean document
    non_trivial = [ln.strip() for ln in cleaned_document.splitlines() if len(ln.strip()) > 3]
    if non_trivial:
        line_counts = Counter(non_trivial)
        top_line, top_count = line_counts.most_common(1)[0]
        if top_count > _OCR_REPETITION_LINE_THRESHOLD:
            metrics["repetition_detected"] = True
            metrics["repetition_reasons"].append(f"line_repeat:{top_count}x")

    # 5. Detect code/number repetition on the clean document
    numbers = re.findall(r"\d{4,}", cleaned_document)
    if numbers:
        num_counts = Counter(numbers)
        top_num, top_num_count = num_counts.most_common(1)[0]
        if top_num_count > _OCR_REPETITION_NUMBER_THRESHOLD:
            metrics["repetition_detected"] = True
            metrics["repetition_reasons"].append(f"number_repeat:{top_num_count}x")

    # 6. Detect lexical loops and consecutive bigram repetitions (stuttering)
    words = [w.lower() for w in cleaned_document.split() if w.isalnum()]
    if len(words) >= 10:
        # Low unique word ratio (vocabulary looping)
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.35:
            metrics["repetition_detected"] = True
            metrics["repetition_reasons"].append(f"low_unique_word_ratio:{unique_ratio:.2f}")

        # Bigram repetition (stuttering loop)
        bigrams = [(words[i], words[i+1]) for i in range(len(words)-1)]
        consecutive_repeats = 0
        max_consecutive = 0
        for i in range(len(bigrams)-2):
            if bigrams[i] == bigrams[i+2]:
                consecutive_repeats += 1
                max_consecutive = max(max_consecutive, consecutive_repeats)
            else:
                consecutive_repeats = 0
        if max_consecutive >= 3:
            metrics["repetition_detected"] = True
            metrics["repetition_reasons"].append(f"consecutive_bigram_repeat:{max_consecutive+1}x")

    # 7. Check for useful documentary content ratio (prevent accepting header-only pages)
    useful_text = _get_useful_text(cleaned_document)
    useful_words = [w for w in useful_text.split() if w]
    original_words = [w for w in cleaned_document.split() if w]
    
    if len(original_words) > 0:
        ratio = len(useful_words) / len(original_words)
        if len(useful_words) < 3 or (len(useful_words) < 15 and ratio < 0.65):
            metrics["repetition_detected"] = True
            metrics["repetition_reasons"].append("insufficient_useful_text")

    # Calculate score AFTER removing gibberish
    score_after = _ocr_post_quality_score(cleaned_document)
    metrics["score_after"] = score_after

    # Determine confidence metric
    if metrics["repetition_detected"] or score_after < MIN_OCR_POST_QUALITY:
        metrics["confidence"] = "low_ocr_quality"
    elif metrics["gibberish_lines_removed"] > 0:
        metrics["confidence"] = "accepted_with_cleaning"
    else:
        metrics["confidence"] = "accepted"

    return cleaned_document, metrics


def _pick_best_ocr(
    candidates: list[tuple[str | None, str]],
) -> tuple[str, str, str, str, dict]:
    """Score OCR candidates and pick the best passing output.

    candidates: list of (raw_text_or_None, backend_name)
    Returns: (selected_text, status, ocr_mode, reason, scores_by_backend)
      - selected_text: the best text, or a placeholder token
      - status: "ok" | "scanned_ocr_empty" | "low_ocr_quality" | "ocr_backend_unavailable"
      - ocr_mode: winning backend name, or "none"
      - reason: selection rationale tag
      - scores_by_backend: {
          backend_name: score_float_or_None,
          "details": {
              backend_name: {
                  "score": float_or_None,
                  "repetition_detected": bool,
                  "repetition_reasons": list[str],
                  "loc_tokens_removed": int,
                  "raw_text_length": int
              }
          }
        }
    """
    scored: list[tuple[float, str, str]] = []
    scores_by_backend: dict[str, any] = {}
    details: dict[str, dict] = {}

    for raw_text, backend_name in candidates:
        if raw_text is None:
            scores_by_backend[backend_name] = None
            details[backend_name] = {
                "score": None,
                "repetition_detected": False,
                "repetition_reasons": [],
                "loc_tokens_removed": 0,
                "raw_text_length": 0,
            }
            continue

        clean, metrics = _sanitize_paddleocr_output(raw_text)
        if metrics["repetition_detected"]:
            score = 0.0
        else:
            score = metrics["score_after"]

        scores_by_backend[backend_name] = score
        details[backend_name] = {
            "score": score,
            "repetition_detected": metrics["repetition_detected"],
            "repetition_reasons": metrics["repetition_reasons"],
            "loc_tokens_removed": metrics["loc_tokens_removed"],
            "raw_text_length": len(raw_text),
            "gibberish_lines_removed": metrics["gibberish_lines_removed"],
            "gibberish_lines_removed_list": metrics["gibberish_lines_removed_list"],
            "score_before": metrics["score_before"],
            "score_after": metrics["score_after"],
            "confidence": metrics["confidence"],
        }
        scored.append((score, clean, backend_name))

    scores_by_backend["details"] = details
    passing = [(s, t, m) for s, t, m in scored if s >= MIN_OCR_POST_QUALITY]

    if passing:
        best_score, best_text, best_mode = max(passing, key=lambda x: x[0])
        if len(scored) == 1:
            reason = "unico_disponivel"
        elif len(passing) == 1:
            reason = "unico_aprovado"
        else:
            reason = "score_superior"
        status = "ok" if best_text else "scanned_ocr_empty"
        return best_text, status, best_mode, reason, scores_by_backend

    if not scored:
        return (
            "[ocr_backend_unavailable]",
            "ocr_backend_unavailable",
            "none",
            "nenhum_backend_disponivel",
            scores_by_backend,
        )

    return "[low_ocr_quality]", "low_ocr_quality", "none", "ambos_reprovados", scores_by_backend


# ---------------------------------------------------------------------------
# Text density evaluation (tasks.md §3)
# ---------------------------------------------------------------------------
def _printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(1 for c in text if c.isprintable()) / len(text)


def _text_quality_score(text: str) -> float:
    """Heuristic quality score in [0.0, 1.0]; low values indicate corrupted/glued text.

    Penalises high space density (chars per space) and high long-token ratio (tokens > 20 chars).
    Normal Portuguese prose: 5–10 chars/space, few long tokens → score near 1.0.
    Glued/corrupted text: many chars without spaces, very long tokens → score near 0.0.
    """
    if not text:
        return 0.0
    spaces = text.count(" ")
    chars_per_space = len(text) / (spaces + 1)
    tokens = text.split()
    if not tokens:
        return 0.0
    long_word_ratio = sum(1 for t in tokens if len(t) > 20) / len(tokens)
    # Penalty starts at >10 chars/space; saturates at 30 chars/space.
    space_density_penalty = min(1.0, max(0.0, (chars_per_space - 10.0) / 20.0))
    penalty = long_word_ratio * 0.6 + space_density_penalty * 0.4
    return max(0.0, 1.0 - penalty)


def _is_case_chaotic(word: str) -> bool:
    """True if a word mixes case in a non-standard pattern — a corrupted OCR artifact.

    Accepts: ALL_CAPS, all_lower, Title_case (first upper then all lower).
    Flags: sAO, tS1aDO, EStADO, PAUi, pAuLO.
    """
    letters = [c for c in word if c.isalpha()]
    if len(letters) < 3:
        return False
    if all(c.isupper() for c in letters):
        return False
    if all(c.islower() for c in letters):
        return False
    if letters[0].isupper() and all(c.islower() for c in letters[1:]):
        return False  # title case
    return True


def _case_chaos_ratio(text: str) -> float:
    """Fraction of whitespace-separated tokens that are case-chaotic."""
    words = text.split()
    if not words:
        return 0.0
    return sum(1 for w in words if _is_case_chaotic(w)) / len(words)


def _intrusive_symbol_ratio(text: str) -> float:
    """Fraction of whitespace-separated tokens that contain intrusive OCR noise symbols."""
    words = text.split()
    if not words:
        return 0.0
    intrusive_count = sum(1 for w in words if len(w) >= 3 and _OCR_INTRUSIVE_NOISE_RE.search(w))
    return intrusive_count / len(words)


def _ocr_post_quality_score(text: str) -> float:
    """Post-OCR quality score; stricter than _text_quality_score.

    Adds a case-chaos penalty for character substitution artifacts,
    and an intrusive symbol penalty for typical OCR noise characters.
    """
    base = _text_quality_score(text)
    chaos = _case_chaos_ratio(text)
    chaos_penalty = max(
        0.0,
        min(1.0, (chaos - OCR_CHAOS_NOISE_FLOOR) / (OCR_CHAOS_SATURATION - OCR_CHAOS_NOISE_FLOOR)),
    )
    
    # Penalize intrusive OCR noise symbols (typical of corrupt/weak OCR)
    intrusive = _intrusive_symbol_ratio(text)
    # Penalty starts at 0.5% (0.005) and saturates at 2% (0.02)
    intrusive_penalty = max(
        0.0,
        min(1.0, (intrusive - 0.005) / 0.015)
    )
    
    return max(0.0, base - chaos_penalty - intrusive_penalty)


_NATIVE_STAMP_INTRUSIVE_RE = re.compile(
    r"[a-zA-ZáéíóúâêîôûãõçüÁÉÍÓÚÂÊÎÔÛÃÕÇÜ]"
    r"[!&'\"*#@$|\\]"
    r"[a-zA-ZáéíóúâêîôûãõçüÁÉÍÓÚÂÊÎÔÛÃÕÇÜ]"
)


def _is_native_text_gibberish(line: str) -> bool:
    """Conservative gibberish filter for native PyMuPDF text.

    Targets only clear stamp artifacts: near-zero letter density, or
    multiple words with alpha[symbol]alpha character substitutions
    (the rotated/inverted stamp signature in native PDF extraction).
    Does NOT apply vocabulary-based rules — those are too aggressive
    for structured legal text containing CNPJs, addresses, and article
    references absent from the reference vocabulary.
    """
    trimmed = line.strip()
    if not trimmed or len(trimmed) < 8:
        return False

    total_len = len(trimmed)
    letters = [c for c in trimmed if c.isalpha()]
    letter_ratio = len(letters) / total_len

    # Near-zero letter density → symbol artifact or corrupt encoding,
    # unless the line is mostly digits (dates, process numbers, currency values).
    if letter_ratio < 0.15:
        digits = [c for c in trimmed if c.isdigit()]
        if len(digits) / total_len < 0.15:
            return True

    # Two or more words with alpha[intrusive-symbol]alpha substitutions
    # combined with sub-0.75 letter ratio → rotated/inverted stamp pattern
    if total_len >= 15:
        words = trimmed.split()
        if len(words) >= 4:
            count = sum(
                1 for w in words
                if len(w) >= 3 and _NATIVE_STAMP_INTRUSIVE_RE.search(w)
            )
            if count >= 2 and letter_ratio < 0.75:
                return True

    return False


def _strip_boilerplate(text: str) -> str:
    """Remove boilerplate lines from native extracted text; return residual."""
    if not text:
        return text
    kept = [
        line for line in text.splitlines()
        if not any(p.search(line) for p in BOILERPLATE_PATTERNS)
    ]
    return "\n".join(kept)


def _needs_ocr(text: str) -> tuple[bool, str]:
    """Returns (needs_ocr, reason) after stripping boilerplate.

    Reasons: 'low_chars', 'low_printable', 'low_quality', 'garbled_text', 'ok'.
    """
    effective = _strip_boilerplate(text)
    if len(effective) < MIN_CHARS_FOR_TEXT:
        return (True, "low_chars")
    if _printable_ratio(effective) < MIN_PRINTABLE_RATIO:
        return (True, "low_printable")
    if _text_quality_score(effective) < MIN_TEXT_QUALITY:
        return (True, "low_quality")
    # Detect garbled/fragmented OCR text: many lines with ≤ 2 chars (e.g. per-char extraction).
    # This pattern yields a high quality score (abundant spaces) but unusable content.
    lines = [ln.strip() for ln in effective.splitlines() if ln.strip()]
    if lines:
        short_ratio = sum(1 for ln in lines if len(ln) <= 2) / len(lines)
        if short_ratio > SHORT_LINE_RATIO_THRESHOLD:
            return (True, "garbled_text")
    return (False, "ok")


def _assess(text: str) -> tuple[str, str]:
    if not text:
        return ("empty", "empty")
    needs, reason = _needs_ocr(text)
    if needs:
        return ("scanned_no_ocr", reason)
    return ("ok", "ok")


# ---------------------------------------------------------------------------
# Page rendering for OCR (tasks.md §4)
# ---------------------------------------------------------------------------
def _render_page_image(doc, page_idx: int) -> bytes:
    """Render a single PDF page to PNG bytes at OCR_RENDER_SCALE (~300 DPI)."""
    import fitz
    dpi = round(OCR_RENDER_SCALE * 72)
    print(f"[render] p.{page_idx + 1}: scale={OCR_RENDER_SCALE:.4f} ({dpi} DPI)", file=sys.stderr)
    mat = fitz.Matrix(OCR_RENDER_SCALE, OCR_RENDER_SCALE)
    pix = doc[page_idx].get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def _preprocess_image(img_bytes: bytes) -> bytes:
    """Preprocess a rendered page image for OCR using Pillow only.

    Pipeline: grayscale → auto-contrast → contrast boost → sharpen →
    median denoise → binary threshold (L mode, not 1-bit).
    On any error, logs to stderr and returns the original bytes unchanged.
    """
    try:
        import io
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        img = Image.open(io.BytesIO(img_bytes)).convert("L")
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = img.point(lambda x: 255 if x > 128 else 0)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as exc:
        print(f"[preprocess] image preprocessing failed: {exc}", file=sys.stderr)
        return img_bytes


# ---------------------------------------------------------------------------
# Extraction — pdfminer.six (no OCR support)
# ---------------------------------------------------------------------------
def _extract_pdfminer(pdf_path: Path, verbose: bool) -> list[dict]:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer

    pages = []
    for num, layout in enumerate(extract_pages(str(pdf_path)), 1):
        try:
            raw = "".join(
                el.get_text() for el in layout if isinstance(el, LTTextContainer)
            ).strip()
            status, reason = _assess(raw)
        except Exception:
            raw, status, reason = "", "failed", "failed"

        if verbose:
            print(f"  [pdfminer] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)
        pages.append({"page": num, "text": raw, "status": status, "ocr": False, "reason": reason})

    return pages


# ---------------------------------------------------------------------------
# Extraction — PyMuPDF with LM Studio/PaddleOCR-VL OCR backend
# ---------------------------------------------------------------------------
def _extract_pymupdf(pdf_path: Path, verbose: bool) -> list[dict]:
    import fitz

    lm_base = os.environ.get(LM_STUDIO_BASE_URL_ENV, "")
    lm_model = os.environ.get(LM_STUDIO_OCR_MODEL_ENV, "")
    lm_timeout = _lm_studio_ocr_timeout()
    vl_configured = bool(lm_base and lm_model)
    if vl_configured:
        print(
            f"[pdf-to-md] LM Studio/PaddleOCR-VL configurado (timeout: {lm_timeout}s) — "
            "seleção por qualidade entre OCR local e OCR-VL.",
            file=sys.stderr,
        )
    else:
        print(
            f"[pdf-to-md] {LM_STUDIO_BASE_URL_ENV} ou {LM_STUDIO_OCR_MODEL_ENV} não definidos — "
            "apenas OCR local será tentado para páginas escaneadas.",
            file=sys.stderr,
        )

    pages = []
    doc = fitz.open(str(pdf_path))
    try:
        for num in range(1, len(doc) + 1):
            page_idx = num - 1
            used_ocr = False
            reason = "ok"
            ocr_mode = ""

            try:
                raw = doc[page_idx].get_text("text").strip()
                extraction_ok = True
            except Exception:
                raw = ""
                extraction_ok = False

            if not extraction_ok:
                status = "failed"
                reason = "failed"
            else:
                needs, reason = _needs_ocr(raw)
                if needs:
                    try:
                        img_bytes = _render_page_image(doc, page_idx)
                        preprocessed_bytes = _preprocess_image(img_bytes)
                    except Exception as exc:
                        if verbose:
                            print(f"  [ocr] p.{num}: falha ao renderizar — {exc}", file=sys.stderr)
                        status = "scanned_no_ocr"
                    else:
                        # Candidate 1: local PaddleOCR (optional)
                        t_local_start = time.monotonic()
                        local_text = _run_local_ocr(preprocessed_bytes)
                        t_local_elapsed = time.monotonic() - t_local_start
                        if local_text is not None and verbose:
                            print(
                                f"  [local_ocr] p.{num}: {len(local_text)} chars ({t_local_elapsed:.1f}s)",
                                file=sys.stderr,
                            )

                        # Candidate 2: LM Studio/PaddleOCR-VL (if configured)
                        vl_text: str | None = None
                        if vl_configured:
                            if verbose:
                                print(
                                    f"  [lm_studio_ocr] p.{num}: enviando para LM Studio/PaddleOCR-VL",
                                    file=sys.stderr,
                                )
                            t_vl_start = time.monotonic()
                            try:
                                vl_text = _run_lm_studio_ocr(preprocessed_bytes).strip()
                                t_vl_elapsed = time.monotonic() - t_vl_start
                                if verbose:
                                    print(
                                        f"  [lm_studio_ocr] p.{num}: {len(vl_text)} chars"
                                        f" ({t_vl_elapsed:.1f}s)",
                                        file=sys.stderr,
                                    )
                            except LmStudioUnavailableError as exc:
                                t_vl_elapsed = time.monotonic() - t_vl_start
                                is_timeout = "timed out" in str(exc).lower()
                                tag = "timeout" if is_timeout else "unavailable"
                                print(
                                    f"  [ocr_backend_unavailable/{tag}] p.{num}: {exc}"
                                    f" (duração: {t_vl_elapsed:.1f}s)",
                                    file=sys.stderr,
                                )
                            except Exception as exc:
                                if verbose:
                                    print(
                                        f"  [lm_studio_ocr] p.{num}: falhou — {exc}",
                                        file=sys.stderr,
                                    )

                        # Score and select best candidate
                        raw, status, ocr_mode, selection_reason, scores = _pick_best_ocr([
                            (local_text, "local_ocr"),
                            (vl_text, "lm_studio_ocr"),
                        ])
                        score_local = scores.get("local_ocr")
                        score_vl = scores.get("lm_studio_ocr")
                        score_local_str = f"{score_local:.3f}" if score_local is not None else "N/A"
                        score_vl_str = f"{score_vl:.3f}" if score_vl is not None else "N/A"

                        # Extract details for logging
                        details = scores.get("details", {})
                        local_det = details.get("local_ocr", {})
                        vl_det = details.get("lm_studio_ocr", {})

                        # Identify rejection reasons for each candidate
                        rejection_reasons = []
                        for name, det in [("local_ocr", local_det), ("lm_studio_ocr", vl_det)]:
                            if det.get("score") is not None:
                                reasons = []
                                if det.get("repetition_detected"):
                                    reasons.extend(det.get("repetition_reasons", []))
                                if det.get("score") < MIN_OCR_POST_QUALITY:
                                    reasons.append(f"low_quality_score:{det.get('score'):.3f}")
                                if reasons:
                                    rejection_reasons.append(f"{name}:[{','.join(reasons)}]")

                        rejection_str = " | ".join(rejection_reasons) if rejection_reasons else "None"
                        used_ocr = ocr_mode not in ("none", "")

                        # Extract winning candidate details for telemetry.
                        # When status=="ok", chosen_det holds the accepted backend's metrics.
                        # When all backends were rejected (ocr_mode="none"), chosen_det is empty;
                        # we then find the best-scoring candidate to surface post_gate info.
                        chosen_det = details.get(ocr_mode, {}) if ocr_mode in details else {}
                        confidence = chosen_det.get("confidence", "low_ocr_quality") if used_ocr else "low_ocr_quality"
                        lines_removed = chosen_det.get("gibberish_lines_removed_list", [])
                        lines_removed_str = " | ".join(lines_removed) if lines_removed else "None"
                        removal_reason = "gibberish_line" if lines_removed else "None"

                        # Determine decision, post-gate, and final traceability fields.
                        # decision must be one of: accepted / accepted_with_cleaning / low_ocr_quality / ocr_backend_unavailable
                        if status == "ok":
                            decision_log = confidence  # "accepted" or "accepted_with_cleaning"
                            post_gate = "none"
                            post_gate_reason = "none"
                            selected_backend = ocr_mode
                            score_before = chosen_det.get("score_before", 0.0)
                            score_after = chosen_det.get("score_after", 0.0)
                            selected_score = score_after
                            final_decision = confidence
                            markdown_output = "text"
                        else:
                            decision_log = status
                            final_decision = status
                            markdown_output = f"[{status}]"
                            # Find best candidate to explain rejection (post-gate traceability).
                            # chosen_det is empty when ocr_mode="none"; scan all evaluated backends.
                            all_scored = [
                                (det.get("score_after", 0.0), name, det)
                                for name, det in details.items()
                                if isinstance(det, dict) and det.get("score") is not None
                            ]
                            if all_scored:
                                sel_raw, selected_backend, sel_det = max(all_scored, key=lambda x: x[0])
                                selected_score = sel_raw
                                score_before = sel_det.get("score_before", 0.0)
                                score_after = sel_det.get("score_after", 0.0)
                                sel_rep_reasons = sel_det.get("repetition_reasons", [])
                                if sel_det.get("repetition_detected") and sel_rep_reasons:
                                    post_gate = "repetition_detected"
                                    post_gate_reason = sel_rep_reasons[0]
                                elif sel_raw < MIN_OCR_POST_QUALITY:
                                    post_gate = "low_quality_score"
                                    post_gate_reason = f"score_after={sel_raw:.3f}<threshold={MIN_OCR_POST_QUALITY}"
                                else:
                                    post_gate = "unknown"
                                    post_gate_reason = "unknown"
                            else:
                                selected_backend = "none"
                                selected_score = 0.0
                                score_before = 0.0
                                score_after = 0.0
                                post_gate = "no_backend_available"
                                post_gate_reason = "no_backend_available"

                        print(
                            f"  [ocr_selection] p.{num}: "
                            f"score_local={score_local_str} "
                            f"score_vl={score_vl_str} "
                            f"backends_evaluated=local_ocr,lm_studio_ocr "
                            f"rejections={rejection_str} "
                            f"chosen_backend={ocr_mode} "
                            f"selected_backend={selected_backend} "
                            f"selected_score={selected_score:.3f} "
                            f"post_gate={post_gate} "
                            f"post_gate_reason={post_gate_reason} "
                            f"decision={decision_log} "
                            f"final_decision={final_decision} "
                            f"markdown_output={markdown_output} "
                            f"lines_removed=\"{lines_removed_str}\" "
                            f"removal_reason=\"{removal_reason}\" "
                            f"score_before={score_before:.3f} "
                            f"score_after={score_after:.3f} "
                            f"reason={selection_reason}",
                            file=sys.stderr,
                        )
                else:
                    status = "ok"
                    # Filter clear stamp artifacts from native text (rotated stamps, inverted margins).
                    # Uses _is_native_text_gibberish — a conservative filter that only removes
                    # near-zero-letter-density lines and rotated-stamp quote-chaos.
                    # _is_line_gibberish is NOT used here: its vocabulary-based rule (rule 4)
                    # incorrectly removes valid legal lines with mixed alphanumeric content
                    # (CNPJ, addresses, article references) when words are absent from the
                    # reference set but the text is structurally valid native output.
                    native_removed = [ln.strip() for ln in raw.splitlines() if _is_native_text_gibberish(ln)]
                    if native_removed:
                        raw = "\n".join(ln for ln in raw.splitlines() if not _is_native_text_gibberish(ln))
                        print(
                            f"  [native_cleanup] p.{num}: {len(native_removed)} linha(s) de artefato "
                            f"removida(s) do texto nativo: {' | '.join(native_removed[:3])}",
                            file=sys.stderr,
                        )

            if verbose:
                if used_ocr:
                    pass  # already fully logged via [ocr_selection]
                elif status in ("ocr_backend_unavailable", "low_ocr_quality"):
                    pass  # already logged via [ocr_selection]
                elif status in ("scanned_no_ocr", "scanned_ocr_empty"):
                    print(f"  [no_ocr/{reason}] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)
                elif status == "failed":
                    print(f"  [failed] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)
                else:
                    print(f"  [pymupdf/{reason}] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)

            pages.append({"page": num, "text": raw, "status": status, "ocr": used_ocr, "reason": reason})
    finally:
        doc.close()

    return pages


# ---------------------------------------------------------------------------
# Auto-detect engine
# ---------------------------------------------------------------------------
def _auto_detect_engine() -> str | None:
    for name, pkg in [("pymupdf", "fitz"), ("pdfminer", "pdfminer")]:
        try:
            __import__(pkg)
            return name
        except ImportError:
            continue
    return None


# ---------------------------------------------------------------------------
# Heurísticas genéricas de estrutura
# ---------------------------------------------------------------------------
def _heading_level(line: str) -> str | None:
    s = line.strip()
    if not s or len(s) > 120:
        return None

    words = s.split()
    upper_ratio = sum(1 for c in s if c.isupper()) / max(len(s), 1)

    # All-caps section headings (e.g. "DOS FATOS", "DO DIREITO", "DOS PEDIDOS").
    # Requirements beyond high upper_ratio:
    #   - At least 2 words: single-word lines are likely continuation fragments.
    #   - Does not end with ";" or ",": those are mid-sentence markers.
    #   - Last word is not a single letter: a trailing "A", "E", "O" means the
    #     next sentence started on the same line (e.g. "HIPOTECAR: A procuração").
    # The numbered-heading rule (lines starting with digits → "##") is intentionally
    # absent: in Brazilian legal documents it only matches article/law/registration
    # references ("166 do CC/2002", "905 em relação à autora"), never section titles.
    if upper_ratio >= 0.8 and 2 <= len(words) <= 10 and not s.endswith("."):
        if s.endswith(";") or s.endswith(","):
            return None
        if len(words[-1]) == 1 and words[-1].isalpha():
            return None
        return "#"

    return None


def _list_prefix(line: str) -> str | None:
    s = line.strip()
    if not s:
        return None

    if s[0] in ("•", "·", "–", "—", "▪", "▸"):
        return "bullet"

    tok = s.split(".", 1)
    if len(tok) == 2 and tok[0].strip().isdigit():
        # Only a numbered list item if the part after the period starts with a
        # non-digit character (space or letter). Law numbers like "10.406/2002"
        # or article references like "1.102" start with more digits and must
        # NOT be converted to numbered list items.
        rest = tok[1].lstrip()
        if rest and not rest[0].isdigit():
            return f"numbered:{tok[0].strip()}"

    return None


def _format_page(text: str) -> str:
    result = []
    for line in text.split("\n"):
        h = _heading_level(line)
        if h and line.strip():
            result.append(f"{h} {line.strip()}")
            continue

        lp = _list_prefix(line)
        if lp and line.strip():
            content = line.strip().lstrip("•·–—▪▸").strip()
            if lp == "bullet":
                result.append(f"- {content}")
            else:
                num = lp.split(":")[1]
                rest = line.strip().split(".", 1)[-1].strip()
                result.append(f"{num}. {rest}")
            continue

        result.append(line)

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Markdown assembly (tasks.md §2 — [[Pág. N]] anchors)
# ---------------------------------------------------------------------------
def build_markdown(pages: list[dict], page_markers: bool) -> str:
    blocks = []
    for entry in pages:
        n, status, text = entry["page"], entry["status"], entry.get("text", "")

        if page_markers:
            blocks.append(PAGE_ANCHOR_TPL.format(n=n))

        if status == "ok" and text:
            blocks.append(_format_page(text))
        elif status == "low_ocr_quality":
            blocks.append("[low_ocr_quality]")
        elif status == "ocr_backend_unavailable":
            blocks.append("[ocr_backend_unavailable]")

    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------------------
# Conversion report
# ---------------------------------------------------------------------------
def build_report(
    pdf_path: Path, pages: list[dict],
    engine: str, warnings: list[str], exit_code: int,
) -> str:
    total = len(pages)
    ok = sum(1 for p in pages if p["status"] == "ok")
    ocr_pages = [p["page"] for p in pages if p.get("ocr")]
    failed = [p["page"] for p in pages if p["status"] == "failed"]
    empty = [p["page"] for p in pages if p["status"] == "empty"]
    scanned = [p["page"] for p in pages if p["status"] in ("scanned_no_ocr", "scanned_ocr_empty")]
    low_ocr = [p["page"] for p in pages if p["status"] == "low_ocr_quality"]
    unavailable = [p["page"] for p in pages if p["status"] == "ocr_backend_unavailable"]
    status = "success" if not (failed or scanned or low_ocr or unavailable) else ("partial" if ok else "failed")
    now = datetime.datetime.now().isoformat(timespec="seconds")

    fl = lambda lst: f" (páginas: {lst})" if lst else ""
    lines = [
        "# Relatório de Conversão — pdf-to-md", "",
        f"- **Arquivo:** `{pdf_path.name}`",
        f"- **Total de páginas:** {total}",
        f"- **Extraídas com sucesso:** {ok}",
        f"- **Via OCR (LM Studio/PaddleOCR-VL):** {len(ocr_pages)}{fl(ocr_pages)}",
        f"- **Com falha:** {len(failed)}{fl(failed)}",
        f"- **Em branco:** {len(empty)}{fl(empty)}",
        f"- **Escaneadas sem OCR:** {len(scanned)}{fl(scanned)}",
        f"- **OCR de baixa qualidade:** {len(low_ocr)}{fl(low_ocr)}",
        f"- **Backend OCR indisponível:** {len(unavailable)}{fl(unavailable)}",
        f"- **Motor:** `{engine}`",
        f"- **Status:** `{status}`",
        f"- **Data/hora:** {now}",
        f"- **Exit code:** {exit_code}",
    ]
    if warnings:
        lines += ["", "## Warnings"] + [f"- {w}" for w in warnings]

    lines += ["", "## Detalhe por Página", "",
              "| Página | Status | OCR | Motivo |",
              "|--------|--------|-----|--------|"]
    for p in pages:
        origem = "sim" if p.get("ocr") else "não"
        reason = p.get("reason", "ok")
        lines.append(f"| {p['page']} | {p['status']} | {origem} | {reason} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="pdf-to-md: converte PDF em Markdown bruto com anchors [[Pág. N]]."
    )
    parser.add_argument("--input",      required=True)
    parser.add_argument("--output",     required=True)
    parser.add_argument("--engine",     default="auto",
                        choices=["auto", "pdfminer", "pymupdf"])
    parser.add_argument("--no-markers", action="store_true")
    parser.add_argument("--verbose",    action="store_true")
    parser.add_argument("--report",     action="store_true")
    args = parser.parse_args()

    pdf_path    = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    page_markers = not args.no_markers
    warnings: list[str] = []

    if not pdf_path.exists():
        print(f"[ERRO] PDF não encontrado: {pdf_path}", file=sys.stderr)
        sys.exit(EXIT_INPUT_ERROR)

    engine = args.engine
    if engine == "auto":
        engine = _auto_detect_engine()
        if engine is None:
            print(
                "[ERRO] Nenhum motor disponível.\n"
                "       pip install pymupdf   ou   pip install pdfminer.six",
                file=sys.stderr,
            )
            sys.exit(EXIT_EXTRACT_ERROR)
        if args.verbose:
            print(f"[auto] Motor selecionado: {engine}", file=sys.stderr)

    if args.verbose:
        print(f"[pdf-to-md] {pdf_path}", file=sys.stderr)

    try:
        if engine == "pdfminer":
            pages = _extract_pdfminer(pdf_path, args.verbose)
        else:
            pages = _extract_pymupdf(pdf_path, args.verbose)
    except ImportError as exc:
        print(f"[ERRO] Motor '{engine}' não instalado: {exc}", file=sys.stderr)
        sys.exit(EXIT_EXTRACT_ERROR)
    except Exception as exc:
        print(f"[ERRO] Extração falhou: {exc}", file=sys.stderr)
        sys.exit(EXIT_EXTRACT_ERROR)

    for p in pages:
        if p["status"] == "failed":
            warnings.append(f"Página {p['page']}: falha na extração")
        elif p["status"] in ("scanned_no_ocr", "scanned_ocr_empty"):
            warnings.append(f"Página {p['page']}: escaneada sem texto recuperável")
        elif p["status"] == "low_ocr_quality":
            warnings.append(f"Página {p['page']}: OCR de baixa qualidade — texto substituído por placeholder")
        elif p["status"] == "ocr_backend_unavailable":
            warnings.append(f"Página {p['page']}: backend OCR indisponível — texto substituído por placeholder")

    md = build_markdown(pages, page_markers)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md, encoding=OUTPUT_ENCODING, errors="replace")
    except Exception as exc:
        print(f"[ERRO] Escrita falhou: {exc}", file=sys.stderr)
        sys.exit(EXIT_WRITE_ERROR)

    if args.verbose:
        print(f"[pdf-to-md] Gerado: {output_path} ({len(pages)} págs.)", file=sys.stderr)

    if args.report:
        rp = output_path.parent / "conversion_report.md"
        try:
            rp.write_text(
                build_report(pdf_path, pages, engine, warnings, EXIT_OK),
                encoding=OUTPUT_ENCODING,
            )
            if args.verbose:
                print(f"[pdf-to-md] Relatório: {rp}", file=sys.stderr)
        except Exception as exc:
            print(f"[AVISO] Relatório não gravado: {exc}", file=sys.stderr)

    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
