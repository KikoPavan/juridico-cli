## Context

`platform/skill-runtime/skill_registry.yaml` declara, para `segmentador-juridico`:

```yaml
schema_ref: "platform/skills/segmentador-juridico/assets/output-schema.json"
validator: "platform/skills/segmentador-juridico/scripts/validate_output.py"
```

`stage_router.py` (`run_segmentador_stage`, linha ~489) lê `schema_ref` e falha
com `FileNotFoundError` se o arquivo não existir — o arquivo nunca foi
commitado, mesmo sendo referenciado por quatro fontes independentes:
`SKILL.md`, `references/variable-dictionary.md`,
`scripts/validate_output.py` (validação manual, usada como fallback quando
`jsonschema` não está instalado) e `assets/example-output.json` (exemplo de
referência). Essas quatro fontes já descrevem o mesmo contrato de forma
consistente o suficiente para derivar o JSON Schema sem ambiguidade.

## Goals / Non-Goals

**Goals:**
- Restaurar `assets/output-schema.json` como JSON Schema Draft 7 (mesmo
  draft usado por `jsonschema.Draft7Validator` em `validate_output.py`).
- Fazer o schema refletir o contrato já documentado em
  `variable-dictionary.md` e `SKILL.md` (v1.1.0), sem introduzir campos ou
  regras novas.
- Garantir compatibilidade tripla: `output-schema.json` valida
  `example-output.json`; `validate_output.py --schema output-schema.json
  example-output.json` passa (validação `jsonschema` + manual, sem conflito
  entre as duas); `openspec validate --all --strict` passa.
- Adicionar teste automatizado mínimo que trava essa consistência.

**Non-Goals:**
- Não alterar `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml`,
  `yaml-normalizador-juridico`.
- Não alterar `curador-relevancia`, exceto se um teste comprovar
  incompatibilidade real (nenhuma foi identificada nesta análise).
- Não alterar a lógica de `run_segmentador_stage()` em `stage_router.py` —
  o bug é a ausência do arquivo, não o código que o consome.
- Não redesenhar o Envelope de Processo nem mudar `schema_version` (permanece
  `"1.1.0"`).

## Decisions

### 1. Fonte de verdade para os campos do schema
`variable-dictionary.md` §1/§2 é a fonte primária (documento explicitamente
dedicado ao contrato de campos), cruzado com `validate_output.py::validate_manual`
(o piso mínimo já reforçado em código) e `example-output.json` (deve validar
sem erro). Onde `variable-dictionary.md` marca um campo como obrigatório
(✅) e o exemplo o inclui em toda peça — caso de `impacto_sentenca_proposto`,
que a dicionário marca ✅ mas `validate_manual` não checa explicitamente —
o schema segue o dicionário (mais estrito). Isso não quebra
`validate_output.py`, pois a validação manual é um piso mínimo, não um teto:
qualquer campo exigido a mais pelo JSON Schema que já esteja presente no
exemplo não gera conflito.

### 2. Draft do JSON Schema
Draft 7, para casar com `jsonschema.Draft7Validator` usado em
`validate_with_jsonschema()`.

### 3. Estrutura do schema
- Top-level `object` com `required: [metadata, pecas]`, `additionalProperties: false`
  no nível raiz (mas `additionalProperties: true` dentro de `pecas[]` para
  não quebrar campos de análise adicionais já presentes no exemplo, como
  `confianca_classificacao`, `sinais_relevancia`, `flags`, `data_documento`,
  `autor`, que `variable-dictionary.md` marca como opcionais ❌).
- `metadata`: obrigatórios `processo_id, total_pecas, gerado_por, timestamp,
  source_file, total_pages, schema_version`; `ocr_quality` opcional (enum
  `high|medium|low|unknown`). `gerado_por` fixado via `const: "segmentador-juridico"`.
- `pecas`: `array`, `minItems: 1`, `items` com os campos obrigatórios do
  §2 do dicionário (identificação, localização, conteúdo, proveniência,
  `relevancia_estimada`) e os enums de `document_type` (§3) e
  `document_type_confidence` (§4) replicados do dicionário e de
  `validate_manual` (`valid_types`, `valid_confidence`), para manter as três
  fontes sincronizadas.
- `anchors`: `array`, `minItems: 1`, `items: {label: string, page: integer >=1}`,
  igual à validação manual.
- `piece_id`: `pattern: "^peca_\\d{3}[a-z]?$"`, igual à regex de
  `validate_manual`.
- `source_sha256`: `pattern: "^[a-fA-F0-9]{64}$"`.

### 4. Teste mínimo
Criar teste em `apps/data-processing` (pytest) que:
1. Carrega `output-schema.json` e `example-output.json`.
2. Valida via `jsonschema.Draft7Validator` (mesma lib usada em produção).
3. Invoca `validate_output.py` como subprocesso (ou importa suas funções)
   contra `example-output.json` e assere exit code 0.
4. Lê `skill_registry.yaml`, resolve `schema_ref` da entrada
   `segmentador-juridico` e assere que o path existe em disco — trava
   especificamente a regressão que motivou esta mudança.

## Risks / Trade-offs

- [Risco] Divergência futura entre `variable-dictionary.md` e o schema, se
  alguém editar um sem o outro → Mitigação: o teste mínimo (item 4) falha
  sempre que `example-output.json` deixar de validar, forçando atualização
  conjunta.
- [Risco] `additionalProperties: false` no nível de `pecas[]` poderia
  quebrar campos de análise legítimos e opcionais já usados pelo
  `curador-relevancia` → Mitigação: manter `additionalProperties: true`
  dentro de `pecas[]` (decisão 3), restringindo o `false` apenas ao
  objeto raiz.
- [Risco] `jsonschema` pode não estar instalado no ambiente de execução,
  caso em que `validate_output.py` cai para validação manual apenas →
  Não é um risco novo desta mudança; o teste mínimo cobre ambos os
  caminhos (import direto do `jsonschema` no teste + subprocess do
  validador).

## Migration Plan

Mudança aditiva (arquivo novo). Não há dado em produção a migrar. Rollback
trivial: remover o arquivo restaura o estado atual (quebrado).

## Open Questions

Nenhuma pendente — os quatro documentos de contrato já convergem o
suficiente para derivar o schema sem decisão do usuário.
