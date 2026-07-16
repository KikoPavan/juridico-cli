## ADDED Requirements

### Requirement: Skill Registry Entry
The system MUST register the `jus-autoridade` skill in the routing configuration to make it resolvable.

#### Scenario: Dispatching the registered skill
- **WHEN** the `SkillDispatcher` loads `skill_registry.yaml` and is requested to dispatch `jus-autoridade`
- **THEN** the dispatcher SHALL return a configuration dict with the correct path `platform/skills/jus-autoridade`, the `high_reasoning` profile, and the associated schemas and validator paths.

### Requirement: Output Structural Validation
The `jus-autoridade` output MUST be validated against its defined schemas using the provided validation script.

#### Scenario: Validation of compliant output structure
- **WHEN** the validation script `platform/skills/jus-autoridade/scripts/validate_structure.py` is invoked with a compliant output JSON (matching `authority_output_schema.json` and `precedent_analysis_schema.json`)
- **THEN** the validation script SHALL complete with exit code 0 and report no validation errors.

#### Scenario: Validation of non-compliant output structure
- **WHEN** the validation script `platform/skills/jus-autoridade/scripts/validate_structure.py` is invoked with a payload that lacks mandatory fields or violates schemas
- **THEN** the validation script SHALL complete with a non-zero exit code or return structured validation errors.

### Requirement: Output Format Compliance
The `jus-autoridade` output format MUST consist of two distinct blocks: a structured technical JSON and a formatted CREAC markdown text block.

#### Scenario: Verify both blocks in output
- **WHEN** the skill generates output
- **THEN** the output SHALL contain a valid JSON block matching `authority_output_schema.json` and a markdown text block conforming to `creac_template.md`.
