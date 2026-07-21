# Tasks — Adopt Outlines for structured schema generation

## 1. Documentation

- [x] Add Outlines to `docs/reference/project_version_matrix.md`
- [x] Add the architectural role of structured schema generation to the Documento Mestre
- [x] Confirm that Outlines is described as auxiliary, not as a replacement for schemas or validators

## 2. Validation planning

- [x] Identify one schema-bound skill suitable for initial validation
- [x] Define a minimal JSON Schema for the validation test
- [x] Define expected valid and invalid outputs

## 3. Technical validation

- [x] Check the current installable version of Outlines
- [x] Register the validated version in `docs/reference/project_version_matrix.md`
- [x] Create a minimal local test using one schema and one LLM profile
- [x] Confirm that malformed outputs are rejected or constrained

## 4. Runtime integration

- [x] Decide whether Outlines integration belongs in `packages/` or inside a specific skill script
- [x] Ensure no parallel skill runtime is created
- [x] Ensure skill execution still passes through `platform/skill-runtime/`

## 5. Acceptance criteria

- [x] Outlines is documented in the version matrix
- [x] Outlines is documented architecturally as structured-generation support
- [x] No code is changed before validation
- [x] No runtime replacement is introduced
- [x] Schemas remain the canonical contracts
