"""
Inter-stage contract validation.

Validates that data crossing from one pipeline stage to the next
conforms to the contracts defined in contracts/*.schema.json.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from .schema_validation import validate_against_schema

_CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"


def _contract_path(name: str) -> Path:
    return _CONTRACTS_DIR / name


def validate_normalized_doc(doc: Dict) -> Tuple[bool, List[str]]:
    """Validate output of converters/ stage."""
    return validate_against_schema(doc, _contract_path("normalized_doc.schema.json"))


def validate_ingestion_job(job: Dict) -> Tuple[bool, List[str]]:
    """Validate input to collectors/ stage."""
    return validate_against_schema(job, _contract_path("ingestion_job.schema.json"))


def validate_extraction_result(result: Dict) -> Tuple[bool, List[str]]:
    """Validate output of collectors/ stage."""
    return validate_against_schema(result, _contract_path("extraction_result.schema.json"))
