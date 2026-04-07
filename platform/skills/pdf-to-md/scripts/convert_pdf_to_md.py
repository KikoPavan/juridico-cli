#!/usr/bin/env python3
"""
pdf-to-md · convert_pdf_to_md.py
=================================
Converte um arquivo PDF em Markdown bruto.
Agnóstico de domínio — funciona para qualquer tipo de PDF textual.

Não realiza limpeza semântica, classificação nem extração de dados.

Uso:
    python convert_pdf_to_md.py --input DOC.pdf --output DOC.md [opções]

Opções:
    --input PATH      Caminho do PDF de entrada (obrigatório)
    --output PATH     Caminho do .md de saída (obrigatório)
    --engine ENGINE   Motor: auto|pdfminer|pymupdf (padrão: auto)
    --no-markers      Não inserir marcadores <!-- page N -->
    --verbose         Log detalhado por página no stderr
    --report          Gerar conversion_report.md junto ao output

Exit codes: 0=ok  1=input_error  2=extract_error  3=write_error
"""

import argparse
import datetime
import sys
from pathlib import Path

EXIT_OK, EXIT_INPUT_ERROR, EXIT_EXTRACT_ERROR, EXIT_WRITE_ERROR = 0, 1, 2, 3

PAGE_MARKER_TPL     = "<!-- page {n} -->"
EMPTY_PAGE_MARKER   = "<!-- page {n}: empty -->"
FAILED_PAGE_MARKER  = "<!-- page {n}: extraction_failed -->"
SCANNED_PAGE_MARKER = "<!-- page {n}: scanned_no_ocr -->"
OUTPUT_ENCODING     = "utf-8"


# ---------------------------------------------------------------------------
# Detecção automática de motor
# ---------------------------------------------------------------------------
def _auto_detect_engine() -> str | None:
    for name, pkg in [("pdfminer", "pdfminer"), ("pymupdf", "fitz")]:
        try:
            __import__(pkg)
            return name
        except ImportError:
            continue
    return None


# ---------------------------------------------------------------------------
# Extração pdfminer.six
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
        pages.append({"page": num, "text": raw, "status": status})

    return pages


# ---------------------------------------------------------------------------
# Extração PyMuPDF
# ---------------------------------------------------------------------------
def _extract_pymupdf(pdf_path: Path, verbose: bool) -> list[dict]:
    import fitz

    pages = []
    doc = fitz.open(str(pdf_path))
    try:
        for num in range(1, len(doc) + 1):
            try:
                raw = doc[num - 1].get_text("text").strip()
                status = _assess(raw)
            except Exception:
                raw, status = "", "failed"

            if verbose:
                print(f"  [pymupdf] p.{num}: {status} ({len(raw)} chars)", file=sys.stderr)
            pages.append({"page": num, "text": raw, "status": status})
    finally:
        doc.close()

    return pages


# ---------------------------------------------------------------------------
# Qualidade do texto extraído
# ---------------------------------------------------------------------------
def _assess(text: str) -> str:
    if not text:
        return "empty"
    ratio = sum(1 for c in text if c.isprintable()) / len(text)
    return "scanned_no_ocr" if ratio < 0.1 else "ok"


# ---------------------------------------------------------------------------
# Heurísticas genéricas de estrutura
# ---------------------------------------------------------------------------
def _heading_level(line: str) -> str | None:
    """Detecta nível de heading sem assumir domínio do documento."""
    s = line.strip()
    if not s or len(s) > 120:
        return None

    words = s.split()
    upper_ratio = sum(1 for c in s if c.isupper()) / max(len(s), 1)

    # H1: linha toda maiúscula, curta, sem ponto final
    if upper_ratio > 0.8 and len(words) <= 10 and not s.endswith("."):
        return "#"

    # H2/H3: começa com número de seção (ex.: "1.", "2.3", "4.1.2")
    first = words[0].rstrip(".")
    parts = first.split(".")
    if all(p.isdigit() for p in parts if p) and len(parts) >= 1 and len(words) <= 12:
        if not s.endswith("."):
            return "##" if len(parts) <= 2 else "###"

    return None


def _list_prefix(line: str) -> str | None:
    """Detecta prefixo de item de lista. Retorna marcador Markdown ou None."""
    s = line.strip()
    if not s:
        return None

    # Marcadores simbólicos
    if s[0] in ("•", "·", "–", "—", "▪", "▸"):
        return "bullet"

    # Lista numerada: "1.", "12."
    tok = s.split(".", 1)
    if len(tok) == 2 and tok[0].strip().isdigit():
        return f"numbered:{tok[0].strip()}"

    return None


# ---------------------------------------------------------------------------
# Formatação de página
# ---------------------------------------------------------------------------
def _format_page(text: str) -> str:
    """Mapeia headings e listas; preserva literalidade do restante."""
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
# Montagem do Markdown
# ---------------------------------------------------------------------------
def build_markdown(pages: list[dict], page_markers: bool) -> str:
    blocks = []
    for entry in pages:
        n, status, text = entry["page"], entry["status"], entry.get("text", "")

        if page_markers:
            marker = {
                "empty":   EMPTY_PAGE_MARKER,
                "failed":  FAILED_PAGE_MARKER,
                "scanned_no_ocr": SCANNED_PAGE_MARKER,
            }.get(status, PAGE_MARKER_TPL)
            blocks.append(marker.format(n=n))

        if status == "ok" and text:
            blocks.append(_format_page(text))

    return "\n".join(blocks) + "\n"


# ---------------------------------------------------------------------------
# Relatório de conversão
# ---------------------------------------------------------------------------
def build_report(
    pdf_path: Path, pages: list[dict],
    engine: str, warnings: list[str], exit_code: int,
) -> str:
    total = len(pages)
    ok      = sum(1 for p in pages if p["status"] == "ok")
    failed  = [p["page"] for p in pages if p["status"] == "failed"]
    empty   = [p["page"] for p in pages if p["status"] == "empty"]
    scanned = [p["page"] for p in pages if p["status"] == "scanned_no_ocr"]
    status  = "success" if not (failed or scanned) else ("partial" if ok else "failed")
    now     = datetime.datetime.now().isoformat(timespec="seconds")

    fl = lambda lst: f" (páginas: {lst})" if lst else ""
    lines = [
        "# Relatório de Conversão — pdf-to-md", "",
        f"- **Arquivo:** `{pdf_path.name}`",
        f"- **Total de páginas:** {total}",
        f"- **Extraídas com sucesso:** {ok}",
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
        description="pdf-to-md: converte PDF em Markdown bruto (agnóstico de domínio)."
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
                "       pip install pdfminer.six   ou   pip install pymupdf",
                file=sys.stderr,
            )
            sys.exit(EXIT_EXTRACT_ERROR)
        if args.verbose:
            print(f"[auto] Motor: {engine}", file=sys.stderr)

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
        elif p["status"] == "scanned_no_ocr":
            warnings.append(f"Página {p['page']}: imagem sem OCR")

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
