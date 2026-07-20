## Why

O `segmentador-juridico` aceita a segmentação compacta de documentos compostos, mas pode falhar ao materializar uma peça posterior, como `peca_003` de `Processo.pdf`, mesmo quando o Markdown contém localizadores judiciais suficientes. Como a falha ocorre antes da persistência, o envelope retornado pelo LLM também se perde e impede a auditoria do diagnóstico.

## What Changes

- Persistir um envelope bruto de debug assim que uma segmentação compacta válida for obtida, antes da materialização final.
- Materializar cada peça exclusivamente a partir do Markdown original, usando uma cadeia determinística de estratégias: intervalo por `judicial_locator`, aliases de paginação, anchors, intervalo até a próxima peça e fallback por página quando houver localizadores suficientes.
- Recortar todo o intervalo entre os localizadores inicial e final para peças com `pages_start` e `pages_end`, preservando os marcadores `judicial_locator` e tolerando páginas de separação (`event_separator`).
- Produzir erro diagnóstico por peça com identidade, tipo documental, limites, anchors e inventário dos localizadores disponíveis, sem perder o artefato bruto.
- Adicionar regressão mínima com três peças que comprove a materialização de `peca_003`, a persistência do envelope e a preservação dos localizadores.
- Manter fora de escopo `pdf-to-md`, `md-clean-markdown`, extratores e provider Gemini; não haverá geração ou inferência de texto ausente.
- Consultar como referências oficiais `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md` durante a implementação.

## Capabilities

### New Capabilities

<!-- Nenhuma capacidade nova. -->

### Modified Capabilities

- `segmentador-juridico-output-schema`: tornar a materialização determinística de peças múltiplas robusta, ordenada e diagnosticável, com persistência prévia do envelope compacto.
- `legal-pipeline-traceability`: garantir que intervalos multipiece preservem os localizadores judiciais de origem, inclusive diante de páginas separadoras.

## Impact

- Código afetado: orquestração da etapa `segmentador-juridico`, especialmente `run_segmentador_stage` e `_materialize_piece` em `apps/data-processing`.
- Artefatos afetados: novo envelope bruto/debug e o existente `envelope_segmentacao.json` final.
- Testes afetados: regressões focadas da nova esteira em `apps/data-processing/tests`, com fixture Markdown multipiece mínima e resposta compacta controlada.
- Sem mudança de API externa, dependências, conversão/limpeza de Markdown, extratores ou integração Gemini.
