## Why

O `segmentador-juridico` falha operacionalmente em documentos longos e multiparte: `Processo.pdf` gerou JSON estruturado truncado (`Unterminated string`) com cerca de 54.788 caracteres, não possuía fallback por blocos aplicável e não pôde usar o fallback determinístico limitado a um único grupo judicial. Além disso, `run_segmentador_stage()` seleciona somente o primeiro Markdown do diretório, de modo que uma falha impede um processamento completo, isolado e auditável do lote.

## What Changes

- Processar todos os Markdown elegíveis, isolando por arquivo decisões, artefatos, falhas e resultados, sem consolidar processos ou origens diferentes.
- Manter o caminho atual para entradas pequenas e detectar previamente alto risco de truncamento para acionar uma estratégia própria do segmentador baseada em páginas/janelas.
- Segmentar janelas com sobreposição controlada e consolidar deterministicamente peças que cruzem fronteiras, preservando identidade judicial, origem, ordem e limites reais.
- Ampliar o fallback determinístico para múltiplas peças somente quando marcadores estruturais confiáveis sustentarem os limites; caso contrário, encaminhar o arquivo para revisão sem materialização inventada.
- Validar cada envelope consolidado pelo schema canônico antes de materializar/promover qualquer saída final e impedir que falhas parciais contaminem arquivos bem-sucedidos.
- Produzir diagnóstico não sobrescrito por arquivo/tentativa, com estágio, estratégia, timestamp e erro de API ou parsing.
- Garantir explicitamente que o segmentador não use nem seja registrado nas estratégias de Extração por Blocos de petição, contestação ou decisão.
- Preparar uma regressão operacional manual com `Processo.pdf`, sem chamadas reais ao Gemini na suíte automatizada e sem incluir extração posterior das peças.

Fora de escopo: alterar schemas para aceitar saídas defeituosas, mudar provider/modelo Gemini, modificar estratégias `extr-*`, extrair o conteúdo jurídico das peças, arquivar a mudança ou executar automaticamente a regressão real.

## Capabilities

### New Capabilities

- `segmentador-juridico-resilient-processing`: processamento isolado de múltiplas origens, particionamento específico por páginas, consolidação determinística, fallback multiparte seguro e diagnóstico por tentativa.

### Modified Capabilities

- `segmentador-juridico-output-schema`: reforçar que documentos longos e multiparte devem produzir um envelope final canônico, completo e validado, preservando proveniência, identidade judicial e limites reais sem materialização parcial.

## Impact

- Baseline operacional: `apps/data-processing/src/data_processing/orchestrator/stage_router.py` e testes em `apps/data-processing/tests/` e `tests/`.
- Cliente compartilhado: diagnóstico contextual em `packages/shared-llm/gemini_client.py`, sem alterar provider, modelo ou estratégias de extratores.
- Contrato e documentação canônica: `openspec/specs/segmentador-juridico-output-schema/spec.md` e, se necessário durante a implementação, documentação interna da skill `platform/skills/segmentador-juridico/` sem relaxar seu schema.
- Artefatos operacionais: `var/artifacts/gemini-debug/`, com nomes/metadados exclusivos por origem e tentativa.
- Documentos oficiais a consultar na implementação: `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md`.
