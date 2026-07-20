## 1. Canonical Routing Map

- [x] 1.1 Update `routing_map.yaml` so every destination is registered in `skill_registry.yaml` or is `REVISAR_MANUAL`, preserving the required valid process-piece routes and routing `sentenca` to `extr-decisao-processo`.
- [x] 1.2 Add explicit registered routes for `contrato_social`, `escritura_imovel` and `escritura_hipotecaria`.
- [x] 1.3 Configure `contrato`, `escritura`, `recurso`, `laudo_pericial`, `nota_fiscal`, `boleto`, `citacao`, `intimacao`, `nao_classificado` and defensive `capa_processo` handling as `REVISAR_MANUAL` with unroutable metadata.

## 2. Curator Alignment

- [x] 2.1 Replace the divergent destination table in `curador-relevancia/scripts/curar.py` with loading and resolution from the canonical `routing_map.yaml`, preserving `None` for removed pieces and manual-review destinations.
- [x] 2.2 Verify that generic contracts and deeds do not infer a specific extractor, specific contract/deed subtypes route correctly, and `capa_processo` remains outside deep extraction.

## 3. Automated Consistency Tests

- [x] 3.1 Add a test that reads every route and fallback from `routing_map.yaml` and fails when a `skill_key` is absent from `skill_registry.yaml`, except `REVISAR_MANUAL`.
- [x] 3.2 Add parametrized tests comparing curator and normalizer routing for common document types, treating curator `None` as equivalent to normalizer `REVISAR_MANUAL` for unroutable types.
- [x] 3.3 Add or extend normalizer behavior tests proving every unroutable type produces `review_status: unroutable` and `status: needs_review`, including when the incoming action is `manter` or `resumir`.
- [x] 3.4 Add regression coverage for every required registered route, `sentenca` fallback to the decision extractor, generic contract/deed safety, and administrative `capa_processo` handling.

## 4. Verification and Scope Control

- [x] 4.1 Run the focused curator, normalizer and data-processing routing tests and resolve all failures without modifying `pdf-to-md`, `md-clean-markdown` or any `extr-*` skill.
- [x] 4.2 Run Ruff on the changed Python files and tests and resolve all findings.
- [x] 4.3 Run `git diff --check` and resolve whitespace errors.
- [x] 4.4 Run `openspec validate --all --strict` and confirm all changes and specs pass strict validation.
