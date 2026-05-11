## Why

`_fix_trailing_whitespace` em `clean_markdown.py` não remove espaços/tabs antes de `\n` porque `str.rstrip(" \t")` para ao encontrar o `\n` terminal — o corpo da linha nunca é tocado. Como resultado, linhas com trailing whitespace antes da quebra passam intactas pela limpeza e o validator (`validate_output.py`) as reporta como erro.

## What Changes

- Corrigir `_fix_trailing_whitespace` para separar a quebra de linha antes de aplicar `rstrip(" \t")` no corpo, e recolocar `\n` ao final.
- Adicionar teste unitário explícito cobrindo linha com espaços antes de `\n`.

## Capabilities

### New Capabilities
<!-- Nenhuma capacidade nova — é uma correção de bug em capacidade existente. -->

### Modified Capabilities
- `trailing-whitespace-removal`: a função `_fix_trailing_whitespace` passa a remover corretamente espaços/tabs antes de `\n`; comportamento de preservação de forced-break Markdown (`  \n`) permanece inalterado.

## Impact

- `platform/skills/md-clean-markdown/scripts/clean_markdown.py` — única função alterada: `_fix_trailing_whitespace`.
- Testes unitários da skill (existentes ou novos) para cobrir o caso de regressão.
- Sem impacto em `pdf-to-md`, `md-frontmatter-yaml`, `skill-runtime` ou marcadores `[[Pág. N]]`.
