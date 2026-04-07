"""
JSON persistence layer.

Saves validated extraction results and normalized documents to disk
following the project's existing output path conventions.
"""

import json
from pathlib import Path
from typing import Any


def save_json(data: Any, output_path: str | Path, *, indent: int = 2) -> Path:
    """
    Persist data as JSON to output_path.
    Creates parent directories as needed.
    Returns the resolved path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return path


def load_json(input_path: str | Path) -> Any:
    """Load JSON from a file. Raises FileNotFoundError if missing."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
