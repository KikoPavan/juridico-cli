# Design — Outlines for structured schema generation

## Context

The project uses explicit contracts between modules through treated files, versioned JSONs, shared schemas and explicit input/output contracts.

LLM-based extraction and analysis must produce structured outputs that can be validated and reused by downstream modules.

## Architectural placement

Outlines belongs to the structured-generation layer.

It sits between:

- skill instructions;
- LLM execution profiles;
- schema-defined output contracts;
- validators used by the functional modules.

## Responsibilities

Outlines is responsible for supporting:

- schema-oriented JSON generation;
- constrained LLM output;
- reduction of malformed responses;
- structured extraction from legal and documental content.

## Non-responsibilities

Outlines must not:

- replace the canonical schemas;
- replace `platform/skill-runtime/`;
- replace `skill_registry.yaml`;
- replace `llm_registry.yaml`;
- create a parallel execution runtime;
- become a hard dependency before validation.

## Integration rule

A skill may use Outlines only when its output is schema-bound.

The canonical schema remains the source of truth.

## Version control

The version and operational status of Outlines must be registered in:

docs/reference/project_version_matrix.md
