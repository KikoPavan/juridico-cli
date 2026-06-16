## Why

A skill `md-clean-markdown` está funcional e possui 14 testes cobrindo trailing whitespace e marcadores de página, mas 6 das 9 regras de limpeza implementadas — heading, bullet, separador, linha decorativa, blocos de código e pipeline CLI — não têm cobertura pytest. Regressões nessas regras não seriam detectadas pela suíte atual.

## What Changes

- Ampliar `platform/skills/md-clean-markdown/scripts/test_clean_markdown.py` com testes unitários e de integração para as regras não cobertas
- Nenhuma alteração no comportamento funcional da skill
- Nenhuma alteração em outros módulos do pipeline

Testes a adicionar (no arquivo existente, sem criar suíte paralela):

- `_fix_heading_space` — sem espaço, excesso de espaços, heading sem texto
- `_fix_bullet` — normalização de `*` e `+` para `-`, preservação de `*` como ênfase
- `_fix_horizontal_rule` — variantes `***`, `___`, `===`, `- - -`, linha com texto (não deve normalizar)
- `_remove_decorative_line` — remoção de `....`, `====`, preservação de linha válida
- `_extract_code_blocks` / `_restore_code_blocks` — isolamento e restauração exatos
- Pipeline E2E via CLI (`subprocess`) — `clean_markdown.py --input ... --output ...`
- `--max-blank N` customizado — verificar colapso com N=1
- `--no-markers` — marcadores tratados como texto comum
- Validação com `validate_output.py` — saída passa em todos os checks

## Capabilities

### New Capabilities

_(nenhuma — a skill não ganha capacidades novas)_

### Modified Capabilities

- `md-clean-markdown`: adicionar requisito formal de cobertura de testes para as regras de limpeza não cobertas pela suíte atual

## Impact

- Arquivo alterado: `platform/skills/md-clean-markdown/scripts/test_clean_markdown.py`
- Arquivos não alterados: `clean_markdown.py`, `validate_output.py`, `SKILL.md`, `assets/`, `references/`
- Nenhuma alteração em `pdf-to-md`, `md-frontmatter-yaml`, `stage_router.py`, `pyproject.toml`, `skill_registry.yaml`, `llm_registry.yaml`, `CLAUDE.md`
- Suíte global deve passar integralmente após a implementação
