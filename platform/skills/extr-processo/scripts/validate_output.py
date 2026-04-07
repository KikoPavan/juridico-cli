#!/usr/bin/env python3
"""Validate a JSON output file against the processo schema."""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
    import referencing
    import referencing.jsonschema as ref_jsonschema
except ImportError:
    print(
        "ERROR: jsonschema/referencing not installed. Run: uv add jsonschema referencing",
        file=sys.stderr,
    )
    sys.exit(2)

ASSET_SCHEMA = Path(__file__).parent.parent / "assets" / "processo.schema.json"
SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "packages" / "shared-schemas"


def build_registry(schemas_dir: Path) -> referencing.Registry:
    """Build a referencing.Registry with all shared schemas pre-loaded."""
    registry = referencing.Registry()
    common_path = schemas_dir / "defs" / "common.schema.json"
    if common_path.exists():
        common = json.loads(common_path.read_text(encoding="utf-8"))
        resource = ref_jsonschema.DRAFT202012.create_resource(common)
        uri = common["$id"]
        registry = registry.with_resource(uri, resource)
    return registry


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(input_path: Path, schema_path: Path) -> bool:
    schema = load_json(schema_path)
    data = load_json(input_path)
    registry = build_registry(SCHEMAS_DIR)
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if not errors:
        print(f"OK  {input_path} — valid against {schema_path.name}")
        return True
    print(f"FAIL  {input_path} — {len(errors)} error(s):", file=sys.stderr)
    for err in errors:
        path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
        print(f"  [{path}] {err.message}", file=sys.stderr)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate processo JSON output against the canonical schema.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--schema", type=Path, default=ASSET_SCHEMA)
    args = parser.parse_args()
    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        sys.exit(2)
    if not args.schema.exists():
        print(f"ERROR: schema not found: {args.schema}", file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if validate(args.input, args.schema) else 1)


if __name__ == "__main__":
    main()
