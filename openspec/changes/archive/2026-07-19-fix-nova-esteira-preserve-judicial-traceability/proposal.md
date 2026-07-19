## Why

A nova esteira `segmentador-juridico → curador-relevancia → yaml-normalizador-juridico` conclui o processamento, mas perde localizadores judiciais e propaga metadados críticos nulos, impedindo relacionar com segurança o Markdown final às páginas, ao processo, ao evento e ao documento de origem. A correção é necessária para tornar a rastreabilidade judicial uma garantia do pipeline, inclusive quando o modelo retorna apenas os campos alternativos de paginação.

## What Changes

- Definir rastreabilidade mínima obrigatória ao longo da nova esteira, preservando `process_number` ou `processo_id`, `event_id` como `event`, `document_code` e marcadores `[[judicial_locator: ...]]` já presentes no texto.
- Normalizar `pages_start` e `pages_end` a partir de `page_number_start` e `page_number_end` quando os campos canônicos estiverem vazios.
- Enriquecer anchors gerados com página, processo, evento e código do documento quando esses valores estiverem disponíveis.
- Impedir que `peticao_inicial`, `contestacao`, `decisao`, `sentenca` e `recurso` recebam `impacto_processual: irrelevante` como classificação padrão.
- Adicionar regressão focada na Petição Inicial do evento 1, ou fixture mínima equivalente, cobrindo paginação e preservação do localizador no Markdown normalizado.
- Manter fora de escopo qualquer alteração em `pdf-to-md`, `md-clean-markdown`, `extr-peticao-processo` e no provider Gemini.
- Consultar, durante a implementação, `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md`.

## Capabilities

### New Capabilities

- `legal-pipeline-traceability`: Contrato ponta a ponta de preservação e normalização de paginação, identidade processual, localizadores judiciais e classificação mínima de peças protegidas na nova esteira.

### Modified Capabilities

- `judicial-locator`: Exigir que localizadores existentes no texto sobrevivam ao pipeline jurídico e que anchors derivados carreguem os atributos judiciais disponíveis.
- `segmentador-juridico-output-schema`: Aceitar os campos alternativos `page_number_start` e `page_number_end` e definir sua conversão para a paginação canônica antes das etapas consumidoras.

## Impact

- Skills afetadas: `platform/skills/segmentador-juridico`, `platform/skills/curador-relevancia` e `platform/skills/yaml-normalizador-juridico`.
- Contratos afetados: envelopes de segmentação e curadoria, anchors e frontmatter do Markdown normalizado.
- Testes afetados: teste focado da nova esteira e suíte do `yaml-normalizador-juridico`, com fixture judicial representativa.
- Não há mudança intencional nas etapas de conversão/limpeza, no extrator de petição ou na integração Gemini.
