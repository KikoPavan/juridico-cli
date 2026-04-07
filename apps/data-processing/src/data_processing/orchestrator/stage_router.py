"""
Stage router: maps CLI commands to individual pipeline stages.
Each function here is a thin adapter between the CLI and the stage implementation.
"""

from pathlib import Path
from typing import Literal

from rich.console import Console

console = Console()

CollectorName = Literal["cad_obr", "proc"]


_SCANNED_THRESHOLD = 150  # chars below which a page is treated as scanned


def _convert_one_hybrid(pdf_path: Path, out_md: Path) -> None:
    """
    Hybrid PDF → Markdown converter.

    Strategy per page:
    - Extract text with PyMuPDF (fast, zero cost).
    - If extracted text < _SCANNED_THRESHOLD chars, the page is likely scanned:
      render it to a JPEG and transcribe with Gemini OCR.
    - Produces page-anchored Markdown: [[Pág. N]] per page.
    - Gemini client is initialised lazily only when a scanned page is detected.
    - Requires GEMINI_API_KEY env var for OCR fallback; if absent, scanned pages
      are skipped with a warning instead of raising.
    """
    import tempfile

    import fitz
    from pdf2image import convert_from_path

    doc = fitz.open(pdf_path)
    parts: list[str] = []
    gemini_available: bool | None = None  # None = not yet checked

    with tempfile.TemporaryDirectory() as tmp:
        for pno in range(doc.page_count):
            page_num = pno + 1
            text = (doc.load_page(pno).get_text("text") or "").strip()

            if len(text) >= _SCANNED_THRESHOLD:
                parts.append(f"[[Pág. {page_num}]]\n{text}")
                continue

            # Scanned page — try Gemini OCR
            if gemini_available is None:
                import os
                gemini_available = bool(os.getenv("GEMINI_API_KEY"))
                if not gemini_available:
                    console.print(
                        "[yellow]GEMINI_API_KEY não definida — "
                        "páginas escaneadas serão omitidas.[/yellow]"
                    )

            if not gemini_available:
                console.print(
                    f"  [yellow]SKIP (escaneada)[/yellow] Pág. {page_num} de {pdf_path.name}"
                )
                continue

            from pathlib import Path as _Path
            from data_processing.converters.gemini_ocr.page_ocr import ocr_page

            images = convert_from_path(
                str(pdf_path), dpi=200, first_page=page_num, last_page=page_num
            )
            img_path = _Path(tmp) / f"page_{page_num}.jpg"
            images[0].save(str(img_path), "JPEG", quality=95)

            console.print(
                f"  [cyan]OCR[/cyan] Pág. {page_num} de {pdf_path.name} → Gemini"
            )
            ocr_text = ocr_page(img_path)
            if ocr_text:
                parts.append(f"[[Pág. {page_num}]]\n{ocr_text}")

    doc.close()
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def run_convert_stage(input_path: Path, output_path: Path) -> None:
    """PDF → Markdown conversion stage using PyMuPDF."""
    from ..converters.markdown_engine.engine import Engine, EngineIO

    io = EngineIO(dir_pdf=input_path, dir_md=output_path)
    engine = Engine(io)
    pdfs = engine.list_pdfs()
    console.print(f"[bold]Converting {len(pdfs)} PDF(s)...[/bold]")
    console.print(f"  Input : {input_path}")
    console.print(f"  Output: {output_path}")

    moves = engine.run_batch(_convert_one_hybrid)
    for mv in moves:
        if mv.ok:
            console.print(f"  [green]OK[/green] {mv.stem}.md ({mv.out_md})")
        else:
            console.print(f"  [red]FAIL[/red] {mv.stem}: {mv.error}")


def run_clean_stage(input_path: Path, output_path: Path) -> None:
    """Legal cleaning stage."""
    from ..cleaners.clean_legal_docs import LegalDocCleaner

    cleaner = LegalDocCleaner()
    results = cleaner.clean_batch(str(input_path), str(output_path))
    ok = sum(1 for _, s, _ in results if s)
    console.print(f"[bold]Cleaned {ok}/{len(results)} file(s)[/bold]")
    for name, success, msg in results:
        icon = "[green]OK[/green]" if success else "[red]FAIL[/red]"
        console.print(f"  {icon} {name} — {msg}")


def run_analyze_stage(input_path: Path, output_path: Path) -> None:
    """Structural rule analysis stage."""
    from ..rule_analysis.analisador_de_regras import GeradorDeRegras

    output_path.mkdir(parents=True, exist_ok=True)
    rules_file = output_path / "regras_propostas.txt"
    gerador = GeradorDeRegras(min_ocorrencias=2, min_comprimento=25)
    frases = gerador.analisar_diretorio(str(input_path))
    if frases:
        gerador.gerar_arquivo_regras(frases, str(rules_file))
        console.print(f"[bold]Rule analysis complete:[/bold] {rules_file}")
    else:
        console.print("[yellow]No repeated phrases found.[/yellow]")


def run_collect_stage(collector: CollectorName, config_path: Path) -> None:
    """
    Dispatch to the appropriate LLM collector agent.

    collector: "cad_obr" | "proc"
    config_path: path to the collector's config.yaml (from project root)
    """
    import importlib.util, sys

    collector_map = {
        "cad_obr": "apps/data-processing/src/data_processing/collectors/collector_cad_obr/main.py",
        "proc": "apps/data-processing/src/data_processing/collectors/collector_proc/main.py",
    }

    main_path = Path(collector_map[collector])
    if not main_path.exists():
        raise FileNotFoundError(f"Collector main.py not found: {main_path}")

    console.print(f"[bold]Running collector:[/bold] {collector}")

    spec = importlib.util.spec_from_file_location(f"collector_{collector}_main", main_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()
