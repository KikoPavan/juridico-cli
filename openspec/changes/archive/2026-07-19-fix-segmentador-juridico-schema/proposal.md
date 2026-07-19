## Why

A skill `segmentador-juridico` está registrada em `skill_registry.yaml` com
`schema_ref: platform/skills/segmentador-juridico/assets/output-schema.json`,
mas esse arquivo não existe no repositório. `run_segmentador_stage()` lê o
`schema_ref` do registry para invocar o LLM com saída estruturada e falha
imediatamente com `FileNotFoundError: Schema do segmentador não encontrado`.
Isso quebra a esteira `run_segmentador_stage → run_curador_stage →
run_normalizador_stage` antes mesmo de iniciar a segmentação, bloqueando
qualquer execução da nova esteira jurídica.

## What Changes

- Criar/restaurar `platform/skills/segmentador-juridico/assets/output-schema.json`
  como JSON Schema (Draft 7) formal do Envelope de Processo (`{metadata, pecas[]}`).
- Garantir que o schema seja consistente com os quatro contratos já existentes
  e não alterados nesta mudança:
  - `scripts/validate_output.py` (validação manual de campos obrigatórios)
  - `assets/example-output.json` (exemplo de referência)
  - `SKILL.md` (contrato descrito textualmente, v1.1.0)
  - `references/variable-dictionary.md` (dicionário de campos/tipos/enums)
- Adicionar teste mínimo que:
  - valida `assets/example-output.json` contra o novo `output-schema.json`;
  - garante que o arquivo referenciado por `schema_ref` no `skill_registry.yaml`
    existe em disco (evita regressão futura de referência quebrada).

## Capabilities

### New Capabilities
- `segmentador-juridico-output-schema`: contrato formal (JSON Schema) do
  Envelope de Processo produzido pela skill `segmentador-juridico`, garantindo
  que `schema_ref` do `skill_registry.yaml` resolve para um arquivo válido e
  compatível com o validador e o exemplo de referência da skill.

### Modified Capabilities
(nenhuma — não há spec existente para `segmentador-juridico` em `openspec/specs/`)

## Impact

- Código: nenhuma alteração em código Python além do teste mínimo novo.
- Arquivos: novo arquivo
  `platform/skills/segmentador-juridico/assets/output-schema.json`; novo
  teste automatizado (localização a definir em `tasks.md`).
- Sistemas afetados: `apps/data-processing/src/data_processing/orchestrator/stage_router.py`
  (`run_segmentador_stage`), e por consequência toda a esteira
  segmentador → curador-relevância → yaml-normalizador-juridico.
- Fora de escopo explícito: `pdf-to-md`, `md-clean-markdown`,
  `md-frontmatter-yaml`, `yaml-normalizador-juridico` e `curador-relevancia`
  não são alterados nesta mudança, salvo incompatibilidade comprovada por
  teste (ver `design.md`).
