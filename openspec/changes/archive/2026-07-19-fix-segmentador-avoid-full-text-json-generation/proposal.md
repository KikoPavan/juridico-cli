## Why

O `run_segmentador_stage` hoje pode exigir que o LLM devolva a íntegra da peça dentro de um JSON volumoso; com Gemini, isso expõe a etapa a truncamento, reparo inválido e até ao fallback genérico de extração devolver uma estrutura incompatível com `{metadata, pecas}`. A segmentação precisa limitar o modelo a decisões compactas e reconstruir deterministicamente o conteúdo e a rastreabilidade a partir do Markdown original.

## What Changes

- Fazer o LLM produzir somente descritores compactos de segmentação, sem copiar o texto integral das peças no JSON.
- Materializar em Python o texto completo de cada peça a partir do Markdown original e dos limites/anchors retornados.
- Usar `judicial_locator` como fonte determinística para identidade judicial, paginação e anchors, preservando os marcadores no texto reconstruído.
- Adicionar fallback determinístico de peça única para entradas com um único grupo de localizadores e classificação segura inferível por heading, `document_code` ou nome do arquivo.
- Rejeitar como resultado final do segmentador qualquer fallback genérico com estrutura incompatível com `{metadata, pecas}`.
- Manter a validação final pelo schema canônico `platform/skills/segmentador-juridico/assets/output-schema.json`.
- Cobrir a regressão com `Petição Inicial_evento_1.md` ou fixture mínima equivalente e executar testes focados, Ruff, `git diff --check` e `openspec validate --all --strict`.
- Fora de escopo: alterar `extr-peticao-processo`, `md-clean-markdown`, `md-frontmatter-yaml`, OCR ou o provider Gemini.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `segmentador-juridico-output-schema`: passa a exigir geração compacta pelo LLM, materialização determinística do texto, validação do envelope e fallback seguro de peça única.
- `legal-pipeline-traceability`: passa a exigir que o segmentador derive e preserve identidade, páginas e anchors diretamente dos `judicial_locator` disponíveis no Markdown de origem.

## Impact

Afeta principalmente `run_segmentador_stage` e seus helpers em `apps/data-processing`, o contrato/prompt da skill `platform/skills/segmentador-juridico` e os testes da nova esteira. Não muda o formato final validado do Envelope de Processo nem os providers e skills declarados fora de escopo. A implementação deve consultar `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md`.
