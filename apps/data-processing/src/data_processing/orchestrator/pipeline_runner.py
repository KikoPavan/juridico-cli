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

console = Console()

CollectorName = Literal["cad_obr", "proc"]

_COLLECTOR_CONFIGS = {
    "cad_obr": Path("apps/data-processing/src/data_processing/collectors/collector_cad_obr/config.yaml"),
    "proc": Path("apps/data-processing/src/data_processing/collectors/collector_proc/config.yaml"),
}


class PipelineRunner:
    def __init__(
        self,
        input_path: Path,
        collector: CollectorName,
        output_path: Path,
        *,
        skip_clean: bool = False,
        skip_analyze: bool = False,
    ) -> None:
        self.input_path = input_path
        self.collector = collector
        self.output_path = output_path
        self.skip_clean = skip_clean
        self.skip_analyze = skip_analyze

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

        # Stage 3: analyze
        if not self.skip_analyze:
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
            run_collect_stage(collector=self.collector, config_path=config_path)
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
