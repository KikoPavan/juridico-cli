## Why

A change `validate-md-clean-markdown-after-pdf-to-md` estabeleceu `[[Pág. N]]` como formato primário de marcador de página — substituindo `<!-- page N -->` como legado. A skill `md-frontmatter-yaml`, que consome a saída de `md-clean-markdown`, não foi auditada após essa mudança: o script `apply_frontmatter.py` remove comentários HTML ao detectar títulos H1 mas ignora `[[Pág. N]]`; os exemplos em `references/` usam apenas o formato legado; e o SKILL.md não documenta qual formato de marcador a skill recebe. Não há nenhuma spec formal para a skill em `openspec/specs/`.

## What Changes

- **`apply_frontmatter.py`**: `_detect_title()` passa a remover também marcadores `[[Pág. N]]` (regex `\[\[Pág\.\s*\d+\]\]`) antes de checar headings H1, evitando detecção falha quando o marcador aparece na mesma linha do heading.
- **`references/exemplo_entrada.md`** e **`references/exemplo_saida.md`**: atualizados para usar `[[Pág. N]]` como formato primário; `<!-- page N -->` mantido como exemplo secundário/legado.
- **`SKILL.md`**: seção "Contrato de entrada" / descrição passa a declarar explicitamente que a skill recebe arquivos com `[[Pág. N]]` (primário) e `<!-- page N -->` (legado), e que ambos são preservados integralmente.
- **Testes de validação (`run_example.sh` e exemplo de entrada)**: atualizados para incluir fixture com `[[Pág. N]]` e executar `validate_output.py --original --strict`.
- **Spec formal**: criada em `openspec/specs/md-frontmatter-yaml/spec.md`.

## Capabilities

### New Capabilities

- `md-frontmatter-yaml`: spec formal da skill — comportamento de inserção de frontmatter, preservação do corpo (incluindo marcadores de página primários e legados), contrato de detecção de metadados.

### Modified Capabilities

_(nenhuma — `page-marker-preservation` e `md-clean-markdown` não são alterados)_

## Impact

- Apenas `platform/skills/md-frontmatter-yaml/` é modificada.
- Nenhum impacto em `pdf-to-md`, `md-clean-markdown` ou `skill-runtime`.
- Nenhuma alteração de CLI/API pública da skill — mudança puramente interna a `_detect_title()`.
- Os arquivos `openspec/changes/` e `openspec/specs/md-frontmatter-yaml/` são criados/atualizados.
