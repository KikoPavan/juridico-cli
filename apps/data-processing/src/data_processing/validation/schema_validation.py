"""
JSON Schema validation for pipeline outputs.

Validates any dict against a JSON Schema file using jsonschema (draft 2020-12).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jsonschema
from jsonschema import Draft202012Validator


def load_schema(schema_path: str | Path) -> Dict:
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(
    data: Any, schema_path: str | Path
) -> Tuple[bool, List[str]]:
    """
    Validate data against a JSON Schema file.
    Returns (is_valid, list_of_error_messages).
    """
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    messages = [f"{' > '.join(str(p) for p in e.path) or '(root)'}: {e.message}" for e in errors]
    return (len(messages) == 0, messages)


def validate_extraction_result(result: Dict, schema_path: str | Path) -> Tuple[bool, List[str]]:
    """
    Validate a collector's extraction result (payload) against its io.schema.json.
    Returns (is_valid, errors).
    """
    return validate_against_schema(result, schema_path)
