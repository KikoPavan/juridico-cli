## 1. Correção do bug

- [x] 1.1 Reescrever `_fix_trailing_whitespace` em `platform/skills/md-clean-markdown/scripts/clean_markdown.py` separando o `\n` terminal antes de aplicar `rstrip(" \t")` no corpo da linha, e recolocando `\n` ao final quando existir.

## 2. Testes

- [x] 2.1 Criar ou ajustar testes unitários para `_fix_trailing_whitespace` cobrindo: linha com espaços antes de `\n`, linha com tab antes de `\n`, linha com forced-break (`  \n`), linha sem `\n` final com espaços, e linha de marcador `[[Pág. N]]` (passada intacta pelo pipeline).

## 3. Validação

- [x] 3.1 Rodar testes unitários e confirmar que passam.
- [x] 3.2 Rodar `openspec validate --all --strict` e confirmar sem erros.
- [x] 3.3 Rodar `git diff --check` e confirmar sem trailing whitespace introduzido.
