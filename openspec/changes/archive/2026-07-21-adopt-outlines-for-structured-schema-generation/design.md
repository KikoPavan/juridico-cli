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

## Integration placement decision

If operational integration is authorized after the deferred validation gate, the
Outlines adapter belongs in `packages/shared-llm/`, behind the existing shared LLM
interface. It must not be embedded in a specific skill script because structured
generation is a reusable LLM capability and skill-specific extraction strategies
must remain unchanged.

This decision does not authorize implementation or add Outlines as a project
dependency. Until the deferral in `deferred.md` is lifted, the validated prototype
remains isolated from production code.

Any future skill that opts into the shared adapter must still be dispatched by
`platform/skill-runtime/skill_dispatcher.py`, registered in
`platform/skill-runtime/skill_registry.yaml`, and use an LLM profile from
`platform/skill-runtime/llm_registry.yaml`. The adapter is not a dispatcher,
registry, validator, or parallel runtime.

Generation constraints are auxiliary. Every produced value must still be checked
by the existing validator against the canonical schema; no canonical schema is
owned, copied, or redefined by the adapter.

## Version control

The version and operational status of Outlines must be registered in:

docs/reference/project_version_matrix.md
