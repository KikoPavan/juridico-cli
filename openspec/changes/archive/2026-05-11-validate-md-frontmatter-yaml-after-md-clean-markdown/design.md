## Context

A skill `md-frontmatter-yaml` consome saída de `md-clean-markdown`. Após a change anterior, `md-clean-markdown` passou a usar `[[Pág. N]]` como formato primário de marcador de página. A skill `md-frontmatter-yaml` preserva o corpo integralmente (escrita direta de `frontmatter_block + body`), mas a função `_detect_title()` em `apply_frontmatter.py` só remove comentários HTML `<!-- ... -->` antes de checar headings H1 — ignorando `[[Pág. N]]`. Se um marcador aparecer na mesma linha de um heading (ex.: `[[Pág. 1]] # Título`), a detecção falha. Os exemplos de referência e o SKILL.md também não refletem o novo formato primário.

Estado atual relevante:
- `apply_frontmatter.py` linha 69: `re.sub(r"<!--[^>]*-->", "", line)` — só remove HTML comments.
- `references/exemplo_entrada.md`: usa `<!-- page N -->` exclusivamente.
- `SKILL.md`: não menciona `[[Pág. N]]`.
- `openspec/specs/md-frontmatter-yaml/`: inexistente.

## Goals / Non-Goals

**Goals:**
- Corrigir `_detect_title()` para ignorar `[[Pág. N]]` ao detectar H1.
- Atualizar exemplos de referência para usar `[[Pág. N]]` como formato primário.
- Atualizar SKILL.md para documentar ambos os formatos de marcador.
- Criar `openspec/specs/md-frontmatter-yaml/spec.md` com requisitos verificáveis.
- Rodar `validate_output.py --original --strict` com fixture contendo `[[Pág. N]]`.

**Non-Goals:**
- Alterar qualquer outro script da skill além de `apply_frontmatter.py`.
- Modificar `md-clean-markdown`, `pdf-to-md` ou `skill-runtime`.
- Adicionar campos jurídicos ou LLM.
- Converter marcadores de um formato para outro — apenas preservar.

## Decisions

### Decisão 1: Regex de remoção de marcadores em `_detect_title()`

**Escolha:** Adicionar uma segunda passagem de `re.sub()` em `_detect_title()`:
```python
clean = re.sub(r"\[\[Pág\.\s*\d+\]\]", "", clean).strip()
```
aplicada após a remoção de HTML comments.

**Alternativa descartada:** regex única que combine ambos os padrões em uma só expressão. Descartada para manter legibilidade e rastreabilidade — cada formato tem linha própria, facilitando debug futuro.

**Nota:** a remoção é apenas para fins de _detecção de título_ (variável local `clean`). O `body` escrito na saída nunca é modificado.

### Decisão 2: Formato dos exemplos de referência

**Escolha:** `exemplo_entrada.md` e `exemplo_saida.md` passam a usar `[[Pág. N]]` como formato primário nas seções de exemplo de conteúdo; `<!-- page N -->` aparece apenas em comentário explicativo como "formato legado".

**Alternativa descartada:** criar arquivo de exemplo novo em paralelo. Descartada — os arquivos existentes são suficientes e manter duplicatas gera inconsistência.

### Decisão 3: Cobertura de teste

**Escolha:** atualizar `references/exemplo_entrada.md` para conter `[[Pág. N]]` e ajustar `run_example.sh` para chamar `validate_output.py --original --strict` ao final.

**Alternativa descartada:** criar suite de testes separada com pytest. Fora do escopo desta change — a skill não tem framework de testes formal e a instrução de escopo proíbe alterar o skill-runtime.

## Risks / Trade-offs

- [Risco] Regex `\[\[Pág\.\s*\d+\]\]` pode não capturar variações de espaçamento extremas (ex.: `[[Pág.  3]]` com dois espaços) → Mitigação: `\s*` já cobre múltiplos espaços; variações documentadas na spec `page-marker-preservation` são capturadas.
- [Trade-off] `run_example.sh` passa a falhar se `validate_output.py --strict` encontrar warning → aceitável e desejado — aumenta cobertura de regressão sem alterar a CLI pública.
