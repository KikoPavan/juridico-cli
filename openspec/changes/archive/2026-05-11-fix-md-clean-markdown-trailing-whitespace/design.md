## Context

`_fix_trailing_whitespace` usa `line.rstrip(" \t")` sobre a string completa, incluindo `\n`. Como `\n` não está no charset de rstrip, o método para imediatamente sem tocar nos espaços que precedem `\n`. A linha retorna intacta.

Adicionalmente, o check `line.endswith("  \n")` incorretamente classifica qualquer linha com 2+ espaços antes de `\n` como forced-break Markdown, impedindo a remoção legítima de trailing whitespace nesse subconjunto.

## Goals / Non-Goals

**Goals:**
- `_fix_trailing_whitespace` remove espaços/tabs antes de `\n`.
- Preserva `  \n` (exactly 2 trailing spaces = forced-break Markdown).
- Preserva comportamento de linhas sem `\n` final.

**Non-Goals:**
- Não alterar nenhuma outra função do arquivo.
- Não alterar `PAGE_MARKER_RE`, `validate_output.py`, ou qualquer outra skill.

## Decisions

**Separar `\n` antes de `rstrip`**

```python
newline = "\n" if line.endswith("\n") else ""
body = line[:-1] if newline else line
if body.endswith("  "):
    return line  # forced-break Markdown — preservar
stripped = body.rstrip(" \t")
result = stripped + newline
```

Alternativa descartada: regex `re.sub(r"[ \t]+\n", "\n", line)` — menos legível e não trata o caso sem `\n` final uniformemente.

## Risks / Trade-offs

- Risco mínimo: mudança localizada em uma única função.
- Linhas com exatamente 2 espaços antes de `\n` continuam preservadas (forced-break); com 3+ espaços não há forced-break Markdown válido, e os espaços serão removidos — comportamento correto.
