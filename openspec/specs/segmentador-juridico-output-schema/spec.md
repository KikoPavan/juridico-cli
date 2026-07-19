# segmentador-juridico-output-schema Specification

## Purpose

Define the requirements for the `segmentador-juridico` skill's output schema: its
resolvability by the skill registry, its contract for the Envelope de Processo
(`{metadata, pecas[]}`), and the regression coverage that protects the
reference example from drifting out of sync with the schema.

## Requirements

### Requirement: Schema de saída resolvível pelo registry
O arquivo apontado por `schema_ref` da entrada `segmentador-juridico` em
`platform/skill-runtime/skill_registry.yaml` SHALL existir em disco em
`platform/skills/segmentador-juridico/assets/output-schema.json` e SHALL
ser um JSON Schema (Draft 7) sintaticamente válido.

#### Scenario: run_segmentador_stage resolve o schema sem erro
- **WHEN** `run_segmentador_stage()` lê `schema_ref` do `skill_registry.yaml`
  para a skill `segmentador-juridico`
- **THEN** o arquivo referenciado existe e é carregado com sucesso, sem
  levantar `FileNotFoundError`

### Requirement: Contrato do Envelope de Processo
O `output-schema.json` SHALL descrever o Envelope de Processo
`{metadata, pecas[]}` conforme documentado em `SKILL.md` e
`references/variable-dictionary.md` da skill `segmentador-juridico`,
incluindo os campos obrigatórios de `metadata` (`processo_id`,
`total_pecas`, `gerado_por`, `timestamp`, `source_file`, `total_pages`,
`schema_version`) e de cada item de `pecas[]` (`piece_id`, `document_type`,
`document_type_confidence`, `pages_start`, `pages_end`, `pages_total`,
`title`, `summary`, `impacto_sentenca_proposto`, `text_excerpt`, `text`,
`anchors`, `observacoes`, `source_file`, `source_path`, `source_sha256`,
`process_group_id`, `origin_piece_index`, `relevancia_estimada`).

#### Scenario: exemplo de referência valida contra o schema
- **WHEN** `assets/example-output.json` é validado contra
  `assets/output-schema.json` usando `jsonschema.Draft7Validator`
- **THEN** a validação não produz nenhum erro

#### Scenario: validador da skill aceita o exemplo de referência
- **WHEN** `scripts/validate_output.py assets/example-output.json` é
  executado (usando o `--schema` padrão de `assets/output-schema.json`)
- **THEN** o processo termina com exit code `0` e imprime `[OK]`

### Requirement: Regressão de referência quebrada é detectável por teste
O projeto SHALL possuir um teste automatizado que falha caso o `schema_ref`
declarado no `skill_registry.yaml` para `segmentador-juridico` deixe de
apontar para um arquivo existente, ou caso `example-output.json` deixe de
validar contra `output-schema.json`.

#### Scenario: teste detecta schema ausente
- **WHEN** o arquivo `output-schema.json` é removido ou o `schema_ref` no
  registry é alterado para um caminho inexistente
- **THEN** a suíte de testes falha, sinalizando a quebra antes que
  `run_segmentador_stage()` seja executado em produção
