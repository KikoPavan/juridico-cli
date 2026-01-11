from typing import Any, Dict, List, Optional, TypedDict


class EvidenceState(TypedDict):
    facts: List[Dict[str, Any]]
    snippets: List[Dict[str, Any]]
    gaps: List[str]


class ReconcilerState(TypedDict):
    # Inputs
    case_id: str
    hypothesis: str
    target_property: str  # ex: "matricula:7013"

    # Internal Processing
    actors: List[str]
    time_window: Optional[Dict[str, str]]  # {start, end}

    # Accumulated Data
    evidence: EvidenceState

    # Chat/Interaction history (optional for CLI now, useful later)
    messages: List[str]

    # Final Output
    final_report_path: Optional[str]
