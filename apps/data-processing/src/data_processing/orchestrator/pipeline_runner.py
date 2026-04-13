"""
PipelineRunner: orchestrates all stages of the data-processing pipeline.

Stage sequence:
  1. convert  — PDF → Markdown (converters/)             [optional, if input_path has PDFs]
  2. clean    — Legal cleaning (cleaners/)
  3. analyze  — Structural rule analysis (rule_analysis/)
  4. collect  — LLM-based structured extraction (collectors/)
  5. validate — Schema/contract validation (validation/)
  6. load     — Persist to JSON + update index registry (loaders/)

Stages 1-3 prepare the document; stage 4 extracts; stages 5-6 persist.
"""

from pathlib import Path
from typing import Literal

from rich.console import Console

from .contracts import PipelineResult
from .stage_router import run_clean_stage, run_analyze_stage, run_collect_stage
from .stage_router import run_nova_esteira_juridica_stage

console = Console()

CollectorName = Literal["cad_obr", "proc"]

_COLLECTOR_CONFIGS = {
    "cad_obr": Path("apps/data-processing/src/data_processing/collectors/collector_cad_obr/config.yaml"),
    "proc": Path("apps/data-processing/src/data_processing/collectors/collector_proc/config.yaml"),
}


def _is_normalizador_output(md_path: Path) -> bool:
    """
    Verifica se um .md em staging foi gerado pelo yaml-normalizador-juridico.
    Critérios: frontmatter contém created_by_skill == 'yaml-normalizador-juridico'.
    """
    try:
        content = md_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return False
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False
        import yaml
        fm = yaml.safe_load(parts[1]) or {}
        return fm.get("created_by_skill") == "yaml-normalizador-juridico"
    except Exception:
        return False


def _cleanup_staging_nova_esteira(staging: Path) -> int:
    """
    No ramo da nova esteira jurídica, remover do staging os .md que NÃO foram
    gerados pelo yaml-normalizador-juridico, garantindo que o collect consuma
    somente os artefatos normalizados.
    Retorna número de arquivos removidos.
    """
    removed = 0
    for md_file in staging.glob("*.md"):
        if not _is_normalizador_output(md_file):
            md_file.unlink()
            console.print(f"  [dim]Removido do staging (não-normalizado)[/dim] {md_file.name}")
            removed += 1
    console.print(f"  [dim]Staging limpo: {removed} arquivo(s) não-normalizado(s) removido(s)[/dim]")
    return removed


class PipelineRunner:
    def __init__(
        self,
        input_path: Path,
        collector: CollectorName,
        output_path: Path,
        *,
        skip_clean: bool = False,
        skip_analyze: bool = False,
        use_nova_esteira_juridica: bool = False,
    ) -> None:
        self.input_path = input_path
        self.collector = collector
        self.output_path = output_path
        self.skip_clean = skip_clean
        self.skip_analyze = skip_analyze
        self.use_nova_esteira_juridica = use_nova_esteira_juridica

    def run(self) -> PipelineResult:
        result = PipelineResult(
            input_path=self.input_path,
            collector=self.collector,
            output_path=self.output_path,
        )

        console.rule("[bold blue]data-processing pipeline[/bold blue]")

        staging = self.output_path / "staging"

        # Stage 2: clean
        if not self.skip_clean:
            console.rule("[cyan]Stage: clean[/cyan]")
            try:
                run_clean_stage(input_path=self.input_path, output_path=staging)
            except Exception as exc:
                result.ok = False
                result.errors.append(f"clean: {exc}")
                console.print(f"[red]Clean stage failed: {exc}[/red]")
                return result
        else:
            staging = self.input_path

        # Stage 3: analyze ou nova esteira jurídica (mutualmente exclusivos)
        if self.use_nova_esteira_juridica:
            # Ramo da nova esteira: bypass do analyze heurístico
            console.rule("[cyan]Stage: nova_esteira_juridica[/cyan]")
            try:
                gerados = run_nova_esteira_juridica_stage(
                    input_md_path=staging,
                    staging_path=staging,
                )
                if gerados == 0:
                    console.print(
                        "[yellow]Nenhum .md normalizado gerado pela nova esteira — "
                        "coleta poderá não encontrar arquivos.[/yellow]"
                    )
                else:
                    # Isolar staging: remover .md não-normalizados para que o
                    # collect consuma SOMENTE os artefatos da nova esteira.
                    _cleanup_staging_nova_esteira(staging)
            except Exception as exc:
                result.ok = False
                result.errors.append(f"nova_esteira_juridica: {exc}")
                console.print(f"[red]Nova esteira jurídica falhou: {exc}[/red]")
                return result
        elif not self.skip_analyze:
            # Ramo baseline: analyze heurístico
            console.rule("[cyan]Stage: analyze[/cyan]")
            try:
                run_analyze_stage(input_path=staging, output_path=staging)
            except Exception as exc:
                result.ok = False
                result.errors.append(f"analyze: {exc}")
                console.print(f"[red]Analyze stage failed: {exc}[/red]")
                return result

        # Stage 4: collect
        console.rule("[cyan]Stage: collect[/cyan]")
        config_path = _COLLECTOR_CONFIGS.get(self.collector)
        if not config_path:
            result.ok = False
            result.errors.append(f"Unknown collector: {self.collector}")
            return result

        try:
            run_collect_stage(collector=self.collector, config_path=config_path, staging_dir=staging)
        except Exception as exc:
            result.ok = False
            result.errors.append(f"collect: {exc}")
            console.print(f"[red]Collect stage failed: {exc}[/red]")
            return result

        # Stage 5: validate
        console.rule("[cyan]Stage: validate[/cyan]")
        console.print("[dim]Schema + contract validation runs inside each collector job.[/dim]")

        # Stage 6: load — index registry update
        console.rule("[cyan]Stage: load[/cyan]")
        try:
            from ..loaders.index_registry import IndexRegistry
            registry = IndexRegistry()
            registry.register(
                source_id=str(self.input_path),
                collector=self.collector,
                output_path=str(self.output_path),
                status="ok",
            )
            console.print(f"[green]Registry updated for:[/green] {self.input_path}")
        except Exception as exc:
            console.print(f"[yellow]Registry update skipped: {exc}[/yellow]")

        console.rule("[bold green]Pipeline complete[/bold green]")
        return result
