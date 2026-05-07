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
import re
import sys
from pathlib import Path

EXIT_OK, EXIT_INPUT_ERROR, EXIT_EXTRACT_ERROR, EXIT_WRITE_ERROR = 0, 1, 2, 3

# Anchor format per spec (tasks.md §2)
PAGE_ANCHOR_TPL = "[[Pág. {n}]]"

# Density thresholds for OCR fallback decision (tasks.md §3)
MIN_CHARS_FOR_TEXT = 50    # minimum useful characters per page
MIN_PRINTABLE_RATIO = 0.6  # minimum ratio of printable chars

OUTPUT_ENCODING = "utf-8"
OCR_RENDER_SCALE = 3.0  # scale factor for page-to-image (~216 DPI)

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


def _strip_boilerplate(text: str) -> str:
    """Remove boilerplate lines from native extracted text; return residual."""
    if not text:
        return text
    kept = [
        line for line in text.splitlines()
        if not any(p.search(line) for p in BOILERPLATE_PATTERNS)
    ]
    return "\n".join(kept)


def _needs_ocr(text: str) -> bool:
    """Returns True when native text is too sparse to be trusted after stripping boilerplate."""
    effective = _strip_boilerplate(text)
    if len(effective) < MIN_CHARS_FOR_TEXT:
        return True
    if _printable_ratio(effective) < MIN_PRINTABLE_RATIO:
        return True
    return False


def _assess(text: str) -> str:
    if not text:
        return "empty"
    if _needs_ocr(text):
        return "scanned_no_ocr"
    return "ok"


# ---------------------------------------------------------------------------
# Page rendering for OCR (tasks.md §4)
# ---------------------------------------------------------------------------
def _render_page_image(doc, page_idx: int) -> bytes:
    """Render a single PDF page to PNG bytes."""
    import fitz
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
            status = _assess(raw)
        except Exception:
            raw, status = "", "failed"

        if verbose:
            print(f"  [pdfminer] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)
        pages.append({"page": num, "text": raw, "status": status, "ocr": False})

    return pages


# ---------------------------------------------------------------------------
# Extraction — PyMuPDF with PaddleOCR fallback (tasks.md §2–§4)
# ---------------------------------------------------------------------------
def _extract_pymupdf(pdf_path: Path, verbose: bool) -> list[dict]:
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

            try:
                raw = doc[page_idx].get_text("text").strip()
                extraction_ok = True
            except Exception:
                raw = ""
                extraction_ok = False

            if not extraction_ok:
                status = "failed"
            elif _needs_ocr(raw):
                if ocr_engine is not None:
                    try:
                        img_bytes = _render_page_image(doc, page_idx)
                        ocr_text = _run_paddle_ocr(img_bytes, ocr_engine)
                        raw = ocr_text.strip()
                        status = "ok" if raw else "scanned_ocr_empty"
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
                source = "ocr" if used_ocr else "pymupdf"
                print(f"  [{source}] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)

            pages.append({"page": num, "text": raw, "status": status, "ocr": used_ocr})
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
    status = "success" if not (failed or scanned) else ("partial" if ok else "failed")
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
        f"- **Motor:** `{engine}`",
        f"- **Status:** `{status}`",
        f"- **Data/hora:** {now}",
        f"- **Exit code:** {exit_code}",
    ]
    if warnings:
        lines += ["", "## Warnings"] + [f"- {w}" for w in warnings]

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
        pages = (_extract_pdfminer if engine == "pdfminer"
                 else _extract_pymupdf)(pdf_path, args.verbose)
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
