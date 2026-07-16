## Context

The monorepo contains a skill-centric runtime (`platform/skill-runtime/`) which handles skill registration, profile selection, prompt loading, and schema exposure. The skill `jus-autoridade` has been introduced under `platform/skills/jus-autoridade/` with its own `SKILL.md`, references, schemas (in `assets/`), and validation script (`scripts/validate_structure.py`).
To make this skill fully integrated and canonical, it must be registered within `skill_registry.yaml` and the runtime must support loading and routing the skill correctly.

## Goals / Non-Goals

**Goals:**
- Register `jus-autoridade` skill in `platform/skill-runtime/skill_registry.yaml` pointing to its workspace path, `high_reasoning` profile, schema, and validator.
- Ensure the `SkillDispatcher` resolves `jus-autoridade` and loads its system prompt, profile configuration, and metadata.
- Validate that the output structure of `jus-autoridade` adheres to the JSON schemas (`authority_output_schema.json` and `precedent_analysis_schema.json`) and the validation script executes successfully on output samples.
- Add test coverage for testing the integration of the `jus-autoridade` skill routing and validation.

**Non-Goals:**
- Altering the core business logic of the existing `jus-autoridade` skill documents.
- Changing dispatcher logic for unrelated skills.

## Decisions

### 1. Registry Definition
Register `jus-autoridade` in `platform/skill-runtime/skill_registry.yaml` with the following configuration:
```yaml
  jus-autoridade:
    path: "platform/skills/jus-autoridade"
    profile: "high_reasoning"
    schema_ref: "platform/skills/jus-autoridade/assets/authority_output_schema.json"
    validator: "platform/skills/jus-autoridade/scripts/validate_structure.py"
```
*Alternatives considered:* None. This mirrors the existing registry patterns (e.g. `segmentador-juridico` and `curador-relevancia`).

### 2. Integration and Validation Verification
Ensure the validation script `platform/skills/jus-autoridade/scripts/validate_structure.py` works seamlessly. In our integration tests, we will invoke the validation script programmatically or via subprocess to verify output validation.
*Alternatives considered:* Writing generic JSON Schema checks. However, using the local `validate_structure.py` ensures adherence to custom legal domain validations implemented specifically for `jus-autoridade`.

## Risks / Trade-offs

- [Risk] Missing test coverage for the validator script.
  → Mitigation: Add tests in `tests/` that call the validator script with mock outputs (both valid and invalid) to verify that it correctly flags structural issues.
- [Risk] JSON serialization/deserialization differences between local validator runtimes.
  → Mitigation: Use the standard `subprocess` or programmatic import validation mechanism consistent with other validator test cases in the project.
