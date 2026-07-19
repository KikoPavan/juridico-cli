## 1. Restaurar o schema

- [x] 1.1 Criar `platform/skills/segmentador-juridico/assets/output-schema.json`
      como JSON Schema Draft 7, cobrindo `metadata` (obrigatórios:
      `processo_id`, `total_pecas`, `gerado_por` como `const`, `timestamp`,
      `source_file`, `total_pages`, `schema_version`; opcional: `ocr_quality`)
      e `pecas[]` (obrigatórios conforme `references/variable-dictionary.md`
      §2: `piece_id`, `document_type`, `document_type_confidence`,
      `pages_start`, `pages_end`, `pages_total`, `title`, `summary`,
      `impacto_sentenca_proposto`, `text_excerpt`, `text`, `anchors`,
      `observacoes`, `source_file`, `source_path`, `source_sha256`,
      `process_group_id`, `origin_piece_index`, `relevancia_estimada`),
      com `additionalProperties: true` dentro de cada item de `pecas[]`.
- [x] 1.2 Replicar em `output-schema.json` os enums `document_type` e
      `document_type_confidence` e os padrões (`piece_id`, `source_sha256`)
      já usados em `scripts/validate_output.py::validate_manual`, para que
      as duas validações (jsonschema + manual) nunca divirjam.
- [x] 1.3 Setar `"$schema": "http://json-schema.org/draft-07/schema#"` no
      arquivo criado.

## 2. Validar compatibilidade com os contratos existentes

- [x] 2.1 Validar `assets/example-output.json` contra o novo
      `output-schema.json` com `jsonschema.Draft7Validator` — zero erros.
- [x] 2.2 Rodar `uv run python - <<'PY'` invocando
      `platform/skills/segmentador-juridico/scripts/validate_output.py`
      contra `assets/example-output.json` — exit code `0`.
- [x] 2.3 Conferir que `skill_registry.yaml` (`schema_ref` e `validator` de
      `segmentador-juridico`) resolve para arquivos existentes.
- [x] 2.4 Não alterar `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml`
      ou `yaml-normalizador-juridico` nesta change.
- [x] 2.5 Rodar a suíte de testes de `curador-relevancia` (se existir) e
      confirmar que nenhuma quebra é introduzida; só tocar em
      `curador-relevancia` se um teste comprovar incompatibilidade real.

## 3. Teste automatizado mínimo

- [x] 3.1 Adicionar `apps/data-processing/tests/test_segmentador_schema.py`
      com: (a) teste que carrega `output-schema.json` e valida
      `example-output.json` via `jsonschema`; (b) teste que resolve
      `schema_ref` da entrada `segmentador-juridico` em
      `platform/skill-runtime/skill_registry.yaml` e assere
      `Path(schema_ref).exists()`.
- [x] 3.2 Rodar `uv run pytest apps/data-processing/tests/test_segmentador_schema.py -v`
      e confirmar que passa.

## 4. Validação final da change

- [x] 4.1 Rodar `openspec validate --all --strict` e confirmar que passa
      sem erros.
- [x] 4.2 Rodar a suíte completa de testes de `apps/data-processing`
      (`uv run pytest apps/data-processing/tests`) e confirmar que nenhuma
      regressão foi introduzida.
