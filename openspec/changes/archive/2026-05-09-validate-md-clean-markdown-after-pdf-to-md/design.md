## Context

`md-clean-markdown` é a segunda etapa do pipeline documental. Recebe o output de `pdf-to-md` e produz Markdown limpo para `md-frontmatter-yaml`.

**Estado atual:** o script `clean_markdown.py` protege marcadores de página via `PAGE_MARKER_RE` (linha 43), que reconhece apenas `<!-- page N -->` e variantes do formato HTML comment. A função `_is_page_marker()` (linha 194) usa `re.search()` contra esse regex. Linhas reconhecidas são passadas diretamente para o output sem qualquer processamento.

**Problema:** o output real e validado de `pdf-to-md` usa `[[Pág. N]]` como marcador primário (confirmado em `var/output/pdf-to-md/arquivo_escaneado.md`). Esse formato não é reconhecido por `PAGE_MARKER_RE`, portanto não recebe proteção explícita durante a limpeza.

**Comportamento atual para `[[Pág. N]]`:**
- Quando está em linha própria: passa pelo pipeline completo (Regra 8 não dispara pois a linha tem caracteres variados, mas a proteção explícita é inexistente)
- Quando está inline no texto: a limpeza da linha pode ocorrer normalmente sem proteção do marcador
- O validador (`validate_output.py`) não verifica integridade de marcadores `[[Pág. N]]`

## Goals / Non-Goals

**Goals:**
- `[[Pág. N]]` passa a ser reconhecido como marcador primário em `PAGE_MARKER_RE`
- `<!-- page N -->` permanece suportado como formato legado
- Nenhuma regra de limpeza remove, altera ou colapsa marcadores de qualquer um dos dois formatos
- `validate_output.py` verifica que todos os marcadores presentes na entrada existem na saída
- SKILL.md, cleaning_rules.md e output_contract.md refletem o contrato correto
- Exemplos de referência usam o formato real gerado por `pdf-to-md`

**Non-Goals:**
- Alterar `pdf-to-md` ou seu formato de saída
- Alterar `md-frontmatter-yaml`
- Alterar o runtime (`platform/skill-runtime/`)
- Suporte a outros formatos de marcador não observados em produção
- Normalização de marcadores (converter de um formato para outro)

## Decisions

### Decisão 1 — Estender `PAGE_MARKER_RE` com OR

**Escolha:** adicionar alternativa `\[\[Pág\.\s*\d+\]\]` ao regex existente via `|`.

```python
PAGE_MARKER_RE = re.compile(
    r"<!--\s*page\s+\d+(\s*:\s*(empty|extraction_failed|scanned_no_ocr))?\s*-->"
    r"|\[\[Pág\.\s*\d+\]\]"
)
```

**Alternativas consideradas:**
- Regex separado: dois `_is_page_marker()` — mais verboso, sem ganho
- Normalizar `[[Pág. N]]` → `<!-- page N -->` no input: viola o princípio de não modificar conteúdo sem regra explícita; cria divergência com o formato que `md-frontmatter-yaml` vai receber

**Consequência para marcadores inline:** `re.search()` já encontra o padrão em qualquer posição da linha. Linhas com marcador inline (`"texto [[Pág. 2]]"`) também serão passadas diretamente, sem limpeza. O custo é que trailing whitespace nessas linhas não é removido. Aceitável: é preferível preservar o marcador a arriscar mutilação.

### Decisão 2 — Sem alteração na lógica de bypass

A lógica `if preserve_markers and _is_page_marker(line): ... continue` permanece idêntica. A mudança é apenas no regex. Isso garante o menor risco de regressão.

### Decisão 3 — Validação de integridade no `validate_output.py`

O validador vai:
1. Extrair todos os marcadores do arquivo de entrada usando `PAGE_MARKER_RE`
2. Verificar que cada marcador está presente no arquivo de saída
3. Reportar erro se qualquer marcador desaparecer ou for alterado

Isso converte a regra de preservação em verificação automatizada.

### Decisão 4 — Exemplos de referência substituídos

`exemplo_entrada.md` e `exemplo_saida.md` passam a usar `[[Pág. N]]` como formato primário, com `<!-- page N -->` como exemplo legado secundário. Os exemplos podem referenciar o arquivo real de `pdf-to-md` disponível em `var/`.

## Risks / Trade-offs

- **[Risco] Marcadores inline passam sem limpeza de trailing whitespace** → Mitigação: aceitável por projeto; o princípio de preservação supera a normalização estética
- **[Risco] Regex com `re.search()` pode confundir texto que coincidentemente contenha `[[Pág. N]]`** → Mitigação: o padrão `\[\[Pág\.\s*\d+\]\]` é suficientemente específico para não gerar falso positivo em prosa normal
- **[Risco] `validate_output.py` pode ter outros pontos de validação que não conhecem o novo formato** → Mitigação: inspecionar o script completo antes de implementar e adicionar o novo padrão em todos os pontos relevantes
