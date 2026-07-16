## 1. Skill Registration and Configuration

- [x] 1.1 Register `jus-autoridade` in `platform/skill-runtime/skill_registry.yaml` with the `high_reasoning` profile, pointing to path `platform/skills/jus-autoridade`, the schema `platform/skills/jus-autoridade/assets/authority_output_schema.json`, and the validator `platform/skills/jus-autoridade/scripts/validate_structure.py`.

## 2. Validator and Runtime Verification

- [x] 2.1 Verify that the validation script `platform/skills/jus-autoridade/scripts/validate_structure.py` runs correctly and validates mock payloads against output schemas.
- [x] 2.2 Confirm that `SkillDispatcher` loads `jus-autoridade` config, resolves the system prompt correctly, and exposes the associated metadata.

## 3. Integration Tests

- [x] 3.1 Implement a test suite in `tests/test_jus_autoridade_integration.py` covering skill resolution, prompt generation, and validation script execution with valid and invalid outputs.
- [x] 3.2 Run all unit and integration tests to ensure no regressions and verify complete integration of the `jus-autoridade` skill.
