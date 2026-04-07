"""
Contracts between pipeline stages.

Each stage produces a typed result consumed by the next stage.
Contracts are dataclasses — no external dependencies required.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ConversionResult:
    """Output of the converters/ stage (PDF → Markdown)."""

    input_path: Path
    output_path: Path
    ok: bool = True
    error: Optional[str] = None


@dataclass
class CleaningResult:
    """Output of the cleaners/ stage."""

    input_path: Path
    output_path: Path
    reduction_pct: float = 0.0
    ok: bool = True
    error: Optional[str] = None


@dataclass
class RuleAnalysisResult:
    """Output of the rule_analysis/ stage."""

    input_path: Path
    rules_found: int = 0
    ok: bool = True
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Aggregate result of a full pipeline run."""

    input_path: Path
    collector: str
    output_path: Path
    conversions: List[ConversionResult] = field(default_factory=list)
    cleanings: List[CleaningResult] = field(default_factory=list)
    rule_analyses: List[RuleAnalysisResult] = field(default_factory=list)
    ok: bool = True
    errors: List[str] = field(default_factory=list)
