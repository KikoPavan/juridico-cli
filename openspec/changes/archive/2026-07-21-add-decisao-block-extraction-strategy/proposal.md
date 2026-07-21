## Why

`extr-decisao-processo` já é o destino canônico de decisões, decisões interlocutórias, sentenças e despachos, mas ainda não possui estratégia própria de Extração por Blocos. Quando o modo em blocos é necessário, a skill falha de forma segura; esta mudança adiciona suporte sem contaminar o resultado com campos ou defaults de petição e contestação.

## What Changes

- Adicionar uma estratégia de blocos exclusiva de `extr-decisao-processo`, registrada e selecionada somente pelo `bundle_id` correspondente.
- Derivar blocos, schemas parciais, prompts, consolidação e fallback exclusivamente de `platform/skills/extr-decisao-processo/assets/decisao_processo.schema.json` e das instruções da skill.
- Aceitar os tipos canonicamente roteados para a skill: `decisao`, `decisao_interlocutoria`, `sentenca` e `despacho`; o valor raiz persistido permanece o `document_type` canônico do schema, `decisao_processo`.
- Preservar evidências literais de número do processo, tipo e data da decisão, magistrado/órgão julgador, partes mencionadas, relatório, fundamentos, dispositivo, resultado, determinações, prazos, obrigações e referências documentais somente por meio das propriedades permitidas pelo schema. Partes, prazos, obrigações e referências não serão criados como propriedades raiz porque o schema não as define; quando relevantes, permanecem nos trechos literais e anchors de `relatorio`, `fundamentacao`, `dispositivo` ou `determinacoes`.
- Validar cada resposta parcial quando aplicável, filtrar a consolidação pela lista de propriedades do schema e validar o JSON completo contra o schema canônico antes de retorná-lo ou persistir.
- Implementar fallback local determinístico por bloco, sem inventar fundamentos, dispositivo, determinações, prazos ou obrigações, com log explícito do bloco degradado.
- Preservar `judicial_locator` como fonte do `page_marker` e impedir marcadores vazios, `"[]"`, números fictícios ou locators inválidos.
- Cobrir seleção, isolamento entre skills, fallback, anchors, validação oficial e não regressão com fake client; manter inalteradas as estratégias de petição e contestação e a falha segura das demais skills.
- Não alterar schemas `*.schema.json`, o preflight Gemini validado ou o formato das chamadas Gemini; não ampliar o escopo para procuração, mandato ou cabeçalho.

## Capabilities

### New Capabilities

- `decisao-block-extraction`: Define extração em blocos, fallback compatível com decisão, consolidação schema-safe, preservação de evidências e validação oficial de `extr-decisao-processo`.

### Modified Capabilities

- `block-extraction-strategy-selection`: Registra `extr-decisao-processo` e exige que seu `bundle_id` selecione exclusivamente a nova estratégia, preservando as seleções existentes e a falha segura.

## Impact

- Código principal previsto: `packages/shared-llm/block_strategies.py`.
- Testes previstos: `tests/test_block_extraction_strategy_selection.py` e, somente se a separação facilitar a leitura, um teste específico em `tests/` para a estratégia de decisão.
- Contratos consultados: `platform/skills/extr-decisao-processo/SKILL.md`, seus assets e validador; `routing_map.yaml`; `skill_registry.yaml`; specs de seleção de estratégias e de `judicial_locator`.
- Documentos oficiais a consultar na implementação: `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md`.
- Sem alteração de API pública, dependências, schemas canônicos, preflight Gemini ou persistência; resultados inválidos continuam impedidos de chegar à escrita feita por `DataExtractorApp`.
