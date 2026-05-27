## Why

A skill `md-clean-markdown` já teve seu `PAGE_MARKER_RE` atualizado (change arquivado 2026-05-09) para reconhecer `[[Pág. N]]`, mas as referências, exemplos e testes da skill ainda usam conteúdo fictício ou sintético que não representa o output real de `pdf-to-md`. Não há um teste E2E com Markdown real, e o arquivo de saída limpo em `var/output/md-clean-markdown/` está idêntico ao de entrada, indicando que o pipeline real nunca foi validado ponta a ponta.

## What Changes

- Substituir `references/exemplo_entrada.md` por conteúdo real extraído de `var/output/pdf-to-md/arquivo_escaneado.md`, mantendo fidelidade ao output da skill anterior
- Substituir `references/exemplo_saida.md` pelo resultado real da execução de `clean_markdown.py` sobre o novo exemplo de entrada
- Adicionar fixture de teste real (`tests/fixtures/` ou similar) baseada em recorte representativo do output de `pdf-to-md`
- Adicionar teste E2E que executa `clean_markdown.py` + `validate_output.py --strict --source` contra o fixture real
- Regenerar `arquivo_escaneado_limpo.md` em `var/output/md-clean-markdown/`
- Atualizar `test_clean_markdown.py` com casos que exercitem características reais do output de pdf-to-md (headings por linha curta, OCR artifacts, texto jurídico)
- Garantir que `validate_output.py --strict --source` passe sem erros contra o fixture real
- Verificar que `run_example.sh` completa sem erros com os novos exemplos

## Capabilities

### New Capabilities

- `real-output-validation`: Validação do cleaner contra Markdown real produzido por `pdf-to-md`, com fixtures representativas e teste E2E obrigatório

### Modified Capabilities

- `md-clean-markdown`: Contrato de exemplos de referência passa a ser baseado em output real de pdf-to-md (não em conteúdo fictício); testes passam a cobrir características reais do output (OCR artifacts, headings por linha curta, texto jurídico com `[[Pág. N]]`)

## Impact

- `platform/skills/md-clean-markdown/references/exemplo_entrada.md` — substituído por conteúdo real
- `platform/skills/md-clean-markdown/references/exemplo_saida.md` — substituído por resultado real
- `platform/skills/md-clean-markdown/scripts/test_clean_markdown.py` — novos testes com fixture real
- `platform/skills/md-clean-markdown/scripts/` — novo diretório `tests/fixtures/` com fixture representativa
- `var/output/md-clean-markdown/arquivo_escaneado_limpo.md` — regenerado
- `var/output/md-clean-markdown/manual_procedimentos_limpo.md` — pode precisar regeneração
- Nenhuma alteração em `pdf-to-md`, `md-frontmatter-yaml`, `platform/skill-runtime/`
