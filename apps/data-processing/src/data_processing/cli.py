"""
data-processing CLI entry point.

Commands:
  run      - Execute the full pipeline (convert → clean → analyze → collect → validate → load)
  convert  - Run only the conversion stage (PDF → Markdown)
  clean    - Run only the cleaning stage
  analyze  - Run only the rule analysis stage
"""

import typer
from pathlib import Path

app = typer.Typer(name="data-processing", help="Juridico-cli data processing pipeline.")

@app.command()
def extract(
    bundle: str = typer.Option(..., "--bundle", "-b", help="ID do bundle extr-* (ex: extr-contrato-social)"),
    input_file: str = typer.Option(..., "--input", "-i", help="Nome do arquivo limpo em var/output/processed/ para extrair")
) -> None:
    """Extrai entidades usando DataExtractorApp V1.1 (LLM estruturado)."""
    from .extractor import DataExtractorApp
    
    app_engine = DataExtractorApp(platform_path="platform", var_dir="var")
    
    try:
        output_path = app_engine.run_extraction(bundle_id=bundle, input_filename=input_file)
        typer.echo(f"\n✅ Pipeline concluído. Arquivo final: {output_path}")
    except Exception as e:
        typer.echo(f"\n❌ Erro crítico no pipeline: {str(e)}", err=True)
        raise typer.Exit(code=1)

@app.command()
def run(
    input: Path = typer.Option(..., "--input", "-i", help="Input file or directory"),
    collector: str = typer.Option(
        ...,
        "--collector",
        "-c",
        help="Collector to dispatch to: cad_obr | proc",
    ),
    output: Path = typer.Option(
        Path("var/output"), "--output", "-o", help="Output directory"
    ),
    use_nova_esteira_juridica: bool = typer.Option(
        False,
        "--use-nova-esteira-juridica",
        help="Ativar a nova esteira jurídica (segmentador → curador → normalizador) no lugar do analyze heurístico",
    ),
) -> None:
    """Execute the full data-processing pipeline."""
    from .orchestrator.pipeline_runner import PipelineRunner

    runner = PipelineRunner(
        input_path=input,
        collector=collector,
        output_path=output,
        use_nova_esteira_juridica=use_nova_esteira_juridica,
    )
    runner.run()


@app.command()
def convert(
    input: Path = typer.Option(..., "--input", "-i", help="Directory with PDF files"),
    output: Path = typer.Option(
        Path("var/input/md"), "--output", "-o", help="Output directory for Markdown files"
    ),
) -> None:
    """Convert PDF files to Markdown."""
    from .orchestrator.stage_router import run_convert_stage

    run_convert_stage(input_path=input, output_path=output)


@app.command()
def clean(
    input: Path = typer.Option(
        ..., "--input", "-i", help="Directory with Markdown files to clean"
    ),
    output: Path = typer.Option(
        Path("var/output/processed"), "--output", "-o", help="Output directory for cleaned files"
    ),
) -> None:
    """Apply legal cleaning to Markdown files."""
    from .orchestrator.stage_router import run_clean_stage

    run_clean_stage(input_path=input, output_path=output)


@app.command()
def analyze(
    input: Path = typer.Option(
        ..., "--input", "-i", help="Directory with cleaned files to analyze"
    ),
    output: Path = typer.Option(
        Path("var/staging"), "--output", "-o", help="Output directory for analyzed files"
    ),
) -> None:
    """Run structural rule analysis on cleaned files."""
    from .orchestrator.stage_router import run_analyze_stage

    run_analyze_stage(input_path=input, output_path=output)


if __name__ == "__main__":
    app()
