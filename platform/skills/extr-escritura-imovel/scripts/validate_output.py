#!/usr/bin/env python3
"""Validate a JSON output file against the escritura_imovel schema."""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: uv add jsonschema", file=sys.stderr)
    sys.exit(2)

SCHEMA_PATH = Path(__file__).parent.parent / "assets" / "escritura_imovel.schema.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(input_path: Path, schema_path: Path) -> bool:
    schema = load_json(schema_path)
    data = load_json(input_path)

    validator = jsonschema.Draft202012Validator(schema)
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
    parser = argparse.ArgumentParser(
        description="Validate escritura_imovel JSON output against the canonical schema."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the JSON file to validate.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help=f"Path to the schema file (default: {SCHEMA_PATH}).",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    if not args.schema.exists():
        print(f"ERROR: schema file not found: {args.schema}", file=sys.stderr)
        sys.exit(2)

    ok = validate(args.input, args.schema)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
