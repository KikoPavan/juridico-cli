# Adopt Outlines for structured schema generation

## Objective

Integrate Outlines into the project architecture as a controlled tool for structured generation based on schemas.

## Scope

This change defines how Outlines will be used to support:

- structured JSON generation;
- schema-constrained LLM outputs;
- validation of outputs produced by skills;
- reduction of malformed or free-form LLM responses;
- stronger contracts between functional modules.

## Out of scope

This change does not:

- replace JSON Schema as the canonical contract format;
- replace the skill runtime;
- replace existing validators;
- define final production usage before operational validation;
- change application code immediately.

## Official references

- docs/architecture/juridico_cli_documento_mestre.md
- docs/reference/project_version_matrix.md
- openspec/config.yaml

## Decision

Outlines will be treated as an auxiliary structured-generation layer.

Schemas remain the canonical contracts.  
Outlines helps LLMs produce outputs that conform to those contracts.
