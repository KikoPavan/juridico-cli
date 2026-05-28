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


# ---------------------------------------------------------------------------
# PaddleOCR — lazy init; version pending validation in project_version_matrix.md
# ---------------------------------------------------------------------------
_paddle_ocr_instance = None


def _get_paddle_ocr():
    """Lazy-initialize PaddleOCR. Returns None if not installed."""
    global _paddle_ocr_instance
    if _paddle_ocr_instance is not None:
        return _paddle_ocr_instance
    try:
        from paddleocr import PaddleOCR
        _paddle_ocr_instance = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
        return _paddle_ocr_instance
    except ImportError:
        return None


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


def _ocr_post_quality_score(text: str) -> float:
    """Post-OCR quality score; stricter than _text_quality_score.

    Adds a case-chaos penalty for character substitution artifacts
    (e.g. tS1aDO, pAuLO, EStADO) that the space-density metric misses.
    Penalty starts at OCR_CHAOS_NOISE_FLOOR and drives score to 0 at OCR_CHAOS_SATURATION.
    For well-recognized OCR (~0% chaos) the base score is preserved unchanged.
    """
    base = _text_quality_score(text)
    chaos = _case_chaos_ratio(text)
    chaos_penalty = max(
        0.0,
        min(1.0, (chaos - OCR_CHAOS_NOISE_FLOOR) / (OCR_CHAOS_SATURATION - OCR_CHAOS_NOISE_FLOOR)),
    )
    return max(0.0, base - chaos_penalty)


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


def _run_paddle_ocr(img_bytes: bytes, ocr_engine) -> str:
    """Extract text from image bytes using PaddleOCR."""
    import io
    import numpy as np
    from PIL import Image

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_array = np.array(img)
    result = ocr_engine.ocr(img_array, cls=True)
    if not result or result[0] is None:
        return ""
    lines = []
    for block in result:
        if block:
            for line in block:
                if line and len(line) >= 2:
                    lines.append(line[1][0])
    return "\n".join(lines)


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
# Extraction — PyMuPDF with PaddleOCR fallback (tasks.md §2–§4)
# ---------------------------------------------------------------------------
def _extract_pymupdf(pdf_path: Path, verbose: bool, compare_ocr: bool = False) -> list[dict]:
    import fitz

    ocr_engine = _get_paddle_ocr()
    if verbose:
        if ocr_engine is not None:
            print("[pdf-to-md] PaddleOCR disponível — OCR ativo para páginas escaneadas.", file=sys.stderr)
        else:
            print("[pdf-to-md] PaddleOCR não instalado — páginas escaneadas marcadas como scanned_no_ocr.", file=sys.stderr)

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
                    if ocr_engine is not None:
                        try:
                            img_bytes = _render_page_image(doc, page_idx)

                            preprocessed_bytes = _preprocess_image(img_bytes)
                            preprocessed_ok = preprocessed_bytes is not img_bytes

                            if compare_ocr:
                                raw_ocr_text = _run_paddle_ocr(img_bytes, ocr_engine)
                                if verbose:
                                    print(
                                        f"  [ocr_raw] p.{num}: compare ({len(raw_ocr_text)} chars)",
                                        file=sys.stderr,
                                    )

                            ocr_text = _run_paddle_ocr(preprocessed_bytes, ocr_engine).strip()
                            ocr_quality = _ocr_post_quality_score(ocr_text)

                            if ocr_quality < MIN_OCR_POST_QUALITY:
                                raw = "[low_ocr_quality]"
                                status = "low_ocr_quality"
                                ocr_mode = "low_ocr_quality"
                            else:
                                raw = ocr_text
                                status = "ok" if raw else "scanned_ocr_empty"
                                ocr_mode = "ocr_preprocessed" if preprocessed_ok else "ocr_raw"

                            used_ocr = True
                        except Exception as exc:
                            if verbose:
                                print(f"  [ocr] p.{num}: falhou — {exc}", file=sys.stderr)
                            status = "scanned_no_ocr"
                    else:
                        status = "scanned_no_ocr"
                else:
                    status = "ok"

            if verbose:
                if used_ocr and ocr_mode:
                    print(f"  [{ocr_mode}] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)
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

    if upper_ratio > 0.8 and len(words) <= 10 and not s.endswith("."):
        return "#"

    first = words[0].rstrip(".")
    parts = first.split(".")
    if all(p.isdigit() for p in parts if p) and len(parts) >= 1 and len(words) <= 12:
        if not s.endswith("."):
            return "##" if len(parts) <= 2 else "###"

    return None


def _list_prefix(line: str) -> str | None:
    s = line.strip()
    if not s:
        return None

    if s[0] in ("•", "·", "–", "—", "▪", "▸"):
        return "bullet"

    tok = s.split(".", 1)
    if len(tok) == 2 and tok[0].strip().isdigit():
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
    status = "success" if not (failed or scanned or low_ocr) else ("partial" if ok else "failed")
    now = datetime.datetime.now().isoformat(timespec="seconds")

    fl = lambda lst: f" (páginas: {lst})" if lst else ""
    lines = [
        "# Relatório de Conversão — pdf-to-md", "",
        f"- **Arquivo:** `{pdf_path.name}`",
        f"- **Total de páginas:** {total}",
        f"- **Extraídas com sucesso:** {ok}",
        f"- **Via OCR (PaddleOCR):** {len(ocr_pages)}{fl(ocr_pages)}",
        f"- **Com falha:** {len(failed)}{fl(failed)}",
        f"- **Em branco:** {len(empty)}{fl(empty)}",
        f"- **Escaneadas sem OCR:** {len(scanned)}{fl(scanned)}",
        f"- **OCR de baixa qualidade:** {len(low_ocr)}{fl(low_ocr)}",
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
    parser.add_argument("--compare-ocr", action="store_true",
                        help="Also run OCR on the raw image for diagnostic comparison (stderr only).")
    args = parser.parse_args()

    pdf_path    = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    page_markers = not args.no_markers
    compare_ocr = args.compare_ocr or os.environ.get("PDF_TO_MD_COMPARE_OCR", "") == "1"
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
            pages = _extract_pymupdf(pdf_path, args.verbose, compare_ocr=compare_ocr)
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
