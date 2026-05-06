# Tasks — Adopt Outlines for structured schema generation

## 1. Documentation

- [ ] Add Outlines to `docs/reference/project_version_matrix.md`
- [ ] Add the architectural role of structured schema generation to the Documento Mestre
- [ ] Confirm that Outlines is described as auxiliary, not as a replacement for schemas or validators

## 2. Validation planning

- [ ] Identify one schema-bound skill suitable for initial validation
- [ ] Define a minimal JSON Schema for the validation test
- [ ] Define expected valid and invalid outputs

## 3. Technical validation

- [ ] Check the current installable version of Outlines
- [ ] Register the validated version in `docs/reference/project_version_matrix.md`
- [ ] Create a minimal local test using one schema and one LLM profile
- [ ] Confirm that malformed outputs are rejected or constrained

## 4. Runtime integration

- [ ] Decide whether Outlines integration belongs in `packages/` or inside a specific skill script
- [ ] Ensure no parallel skill runtime is created
- [ ] Ensure skill execution still passes through `platform/skill-runtime/`

## 5. Acceptance criteria

- [ ] Outlines is documented in the version matrix
- [ ] Outlines is documented architecturally as structured-generation support
- [ ] No code is changed before validation
- [ ] No runtime replacement is introduced
- [ ] Schemas remain the canonical contracts
