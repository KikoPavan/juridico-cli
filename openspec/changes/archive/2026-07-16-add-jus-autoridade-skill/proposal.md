## Why

Integrate the `jus-autoridade` skill as a canonical capability of the `juridico-cli` runtime. Currently, the project lacks a dedicated, structured mechanism for legal authority grounding using judicial precedents. Adding this skill enables the system to construct high-quality legal block text following the CREAC methodology, parse ratio decidendi, distinguish adversary precedents (distinguishing), evaluate analogical applicability, and identify precedent overruling/risk conditions with structural schema validation.

## What Changes

- Register the new skill `jus-autoridade` in `platform/skill-runtime/skill_registry.yaml` with the `high_reasoning` profile, pointing to its assets and validator.
- Enable `juridico-cli` to execute the skill using the structural JSON schemas (`precedent_analysis_schema.json` and `authority_output_schema.json`) and the validation script `validate_structure.py` already placed in `platform/skills/jus-autoridade/`.
- Ensure proper routing and runtime parsing of inputs (legal thesis, facts, user precedents, adversary precedents, objective) and output format (JSON and CREAC markdown).

## Capabilities

### New Capabilities
- `jus-autoridade`: Provides legal authority grounding using judicial precedents, ratio decidendi analysis, analogical application, distinguishing, and overruled risk classification, outputting a structured JSON and formatted CREAC markdown block.

### Modified Capabilities

## Impact

- [platform/skill-runtime/skill_registry.yaml](file:///home/kiko/devops/juridico-cli/platform/skill-runtime/skill_registry.yaml): Skill routing configuration and metadata.
- [platform/skills/jus-autoridade/](file:///home/kiko/devops/juridico-cli/platform/skills/jus-autoridade/): Integration of existing schemas and validation scripts into the runtime dispatcher.
- `tests/`: Add integration tests to verify the routing and validation of the new `jus-autoridade` skill execution.
