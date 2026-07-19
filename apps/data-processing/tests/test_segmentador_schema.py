"""Tests for the segmentador-juridico output schema and its registry reference."""

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = PROJECT_ROOT / "platform" / "skills" / "segmentador-juridico"
SCHEMA_PATH = SKILL_DIR / "assets" / "output-schema.json"
EXAMPLE_PATH = SKILL_DIR / "assets" / "example-output.json"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate_output.py"
REGISTRY_PATH = PROJECT_ROOT / "platform" / "skill-runtime" / "skill_registry.yaml"


def test_example_output_validates_against_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    errors = list(jsonschema.Draft7Validator(schema).iter_errors(example))
    assert not errors, [e.message for e in errors]


def test_validate_output_script_passes_on_example():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(EXAMPLE_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_skill_registry_schema_ref_resolves_to_existing_file():
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = registry["skills"]["segmentador-juridico"]

    schema_ref = PROJECT_ROOT / entry["schema_ref"]
    validator = PROJECT_ROOT / entry["validator"]

    assert schema_ref.exists(), f"schema_ref não encontrado: {schema_ref}"
    assert validator.exists(), f"validator não encontrado: {validator}"
