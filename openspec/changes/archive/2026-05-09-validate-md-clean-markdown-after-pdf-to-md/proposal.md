## Why

A skill `md-clean-markdown` documenta e preserva marcadores de página no formato `<!-- page N -->` (comentário HTML), mas o output real validado de `pdf-to-md` usa o formato `[[Pág. N]]`. O regex `PAGE_MARKER_RE` atual não reconhece esse padrão, deixando marcadores reais sem proteção explícita durante a limpeza e tornando a documentação, os exemplos de referência e o validador inconsistentes com o pipeline operacional.

## What Changes

- Atualizar `PAGE_MARKER_RE` em `clean_markdown.py` para reconhecer `[[Pág. N]]` como marcador primário e manter `<!-- page N -->` como formato legado suportado
- Garantir que `_is_page_marker()` cubra ambos os formatos e que nenhuma regra de limpeza toque nesses marcadores
- Atualizar `validate_output.py` para verificar integridade de marcadores `[[Pág. N]]` no arquivo de saída
- Atualizar `SKILL.md` para declarar `[[Pág. N]]` como formato primário e `<!-- page N -->` como legado
- Atualizar `assets/cleaning_rules.md` (Regra 7) para documentar ambos os formatos
- Atualizar `assets/output_contract.md` para refletir o contrato de preservação correto
- Substituir `references/exemplo_entrada.md` e `references/exemplo_saida.md` por exemplos baseados no output real de `pdf-to-md` com marcadores `[[Pág. N]]`
- Adicionar teste de validação ponta a ponta usando o arquivo real `var/output/pdf-to-md/arquivo_escaneado.md`

## Capabilities

### New Capabilities

- `page-marker-preservation`: Preservação obrigatória de marcadores de página em ambos os formatos (`[[Pág. N]]` primário + `<!-- page N -->` legado), com validação automática na saída

### Modified Capabilities

- `md-clean-markdown`: Regra 7 passa a reconhecer `[[Pág. N]]` como formato primário; contrato de entrada/saída e exemplos de referência atualizados para refletir o output real de `pdf-to-md`

## Impact

- `platform/skills/md-clean-markdown/scripts/clean_markdown.py` — regex e função de detecção
- `platform/skills/md-clean-markdown/scripts/validate_output.py` — validação de saída
- `platform/skills/md-clean-markdown/SKILL.md` — documentação da skill
- `platform/skills/md-clean-markdown/assets/cleaning_rules.md` — Regra 7
- `platform/skills/md-clean-markdown/assets/output_contract.md` — contrato formal
- `platform/skills/md-clean-markdown/references/exemplo_entrada.md` — exemplo de entrada
- `platform/skills/md-clean-markdown/references/exemplo_saida.md` — exemplo de saída
- Nenhuma dependência externa alterada; `pdf-to-md` e `md-frontmatter-yaml` permanecem fora de escopo
