## Why

Documentos compostos como `Processo.pdf` podem começar por uma capa processual que o LLM classifica corretamente como `capa_processo`, mas o enum final do segmentador rejeita esse valor e impede a persistência do envelope. O tipo precisa ser aceito de forma controlada e tratado como peça administrativa, sem acionar extração jurídica profunda.

## What Changes

- Adicionar `capa_processo` ao contrato oficial de `document_type` do `segmentador-juridico`, incluindo schema, validador manual quando aplicável e documentação da skill.
- Classificar `capa_processo` no curador como peça administrativa de baixo impacto e prioridade, usando a ação segura já suportada para conteúdo não útil à sentença.
- Garantir `encaminhamento: null` para que capas não sejam roteadas a skills `extr-*`.
- Garantir que o normalizador trate defensivamente uma capa recebida, sem quebrar nem inventar uma skill jurídica profunda.
- Adicionar regressão multipiece com capa seguida de peças processuais e verificar a geração de `envelope_segmentacao.json`.
- Executar teste real com `Processo.md` quando a fixture operacional estiver disponível, além dos testes focados e validações estáticas.
- Manter fora de escopo `pdf-to-md`, `md-clean-markdown`, extratores `extr-*` e provider Gemini.
- Consultar `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md` durante a implementação.

## Capabilities

### New Capabilities

- `process-cover-piece-handling`: define a curadoria administrativa, o não encaminhamento para extração profunda e o comportamento seguro do normalizador para `capa_processo`.

### Modified Capabilities

- `segmentador-juridico-output-schema`: passa a aceitar `capa_processo` como tipo documental oficial em envelopes segmentados.

## Impact

- Skills afetadas: `platform/skills/segmentador-juridico`, `platform/skills/curador-relevancia` e, apenas para tolerância segura, `platform/skills/yaml-normalizador-juridico`.
- Contratos afetados: enum de `document_type`, documentação de variáveis e regras determinísticas de curadoria/roteamento.
- Testes afetados: schema do segmentador, curadoria, normalização segura e regressão multipiece/`Processo.md`.
- Sem novas dependências, APIs externas, runtimes ou mudanças nos componentes explicitamente fora de escopo.
