## Why

A nova esteira jurídica já produz Markdown normalizado, mas a coleta ainda pode inferir extratores inexistentes, ignorar o caminho real de staging e persistir respostas do LLM sem validar o schema da skill. O despacho precisa tornar o frontmatter aprovado e o registro canônico de skills uma fronteira segura antes de qualquer chamada ao LLM ou gravação de resultado.

## What Changes

- Adicionar um fluxo seguro para despachar somente Markdown normalizado com `status: ready`, `review_status: approved` e `skill_key` explícito iniciado por `extr-`.
- Tratar `REVISAR_MANUAL`, estados de revisão, `skill_key` ausente e skills não registradas como descartes auditáveis, sem chamada ao LLM e sem falha global do pipeline.
- Remover da nova esteira a inferência de bundle a partir de `document_type`; o `skill_key` do frontmatter será sua única rota válida.
- Resolver a skill exclusivamente pelo `SkillDispatcher` e pelo registro canônico `platform/skill-runtime/skill_registry.yaml`.
- Permitir que a extração leia explicitamente o caminho real do Markdown encontrado no staging, preservando chamadas legadas que fornecem apenas `input_filename`.
- Validar a resposta estruturada do LLM contra o `schema_ref` da skill antes de persistir; respostas inválidas não serão registradas como resultados válidos nem consideradas sucesso.
- Adicionar testes determinísticos com dispatcher e cliente LLM falsos para seleção, rejeição, caminho de entrada, validação, persistência e compatibilidade legada.
- Fora de escopo: Outlines, runtime paralelo, migração de diretórios ou módulos funcionais e mudanças desnecessárias nos mapas ou collectors legados.

## Capabilities

### New Capabilities

- `safe-normalized-extraction-dispatch`: Define a seleção segura de Markdown normalizado, resolução exclusiva de extratores registrados, leitura pelo caminho real de staging, validação do resultado pelo schema da skill e compatibilidade com chamadas legadas.

### Modified Capabilities

Nenhuma.

## Impact

- Código principal afetado: `apps/data-processing/src/data_processing/orchestrator/stage_router.py`, `DataExtractorApp` e pontos mínimos do runtime de extração necessários para aceitar caminho explícito e validar schema.
- Contratos canônicos consultados: `platform/skill-runtime/skill_dispatcher.py`, `platform/skill-runtime/skill_registry.yaml` e o `schema_ref` retornado pelo dispatcher.
- Testes afetados: suíte de `apps/data-processing/tests`, sem chamadas reais ao Gemini.
- Documentos oficiais a consultar durante a implementação: `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md`.
- Compatibilidade: a assinatura legada `run_extraction(bundle_id, input_filename)` permanece funcional; a nova entrada explícita é aditiva.
