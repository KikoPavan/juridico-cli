## Context

O `DataExtractorApp` em `apps/data-processing/src/data_processing/extractor.py` busca arquivos com frontmatter YAML em `var/output/processed_fm/`. O skill `md-frontmatter-yaml` grava a saída em `var/output/md-frontmatter-yaml/`. Esse desalinhamento faz o extrator não encontrar os arquivos enriquecidos quando executado após o pipeline completo.

A SKILL.md do `md-frontmatter-yaml` já documenta `var/output/md-frontmatter-yaml/` como saída canônica. O runtime de execução (scripts `run_example.sh`, `apply_frontmatter.py`) também já usam esse caminho.

## Goals / Non-Goals

**Goals:**
- Extrator localiza arquivos enriquecidos em `var/output/md-frontmatter-yaml/`
- Extrator mantém fallback para `var/output/processed/<arquivo>.md` (clean original) se o enriquecido não existir
- Documentação explicita o fluxo canônico de diretórios do pipeline
- `processed_fm` deixa de ser caminho oficial

**Non-Goals:**
- Não alterar provider Gemini
- Não alterar módulo clean
- Não alterar módulo convert
- Não alterar schema da petição
- Não renomear diretórios fisicamente (migração apenas no código)
- Não alterar SKILL.md ou scripts do skill `md-frontmatter-yaml`

## Decisions

1. **Substituir `processed_fm` por `md-frontmatter-yaml` no extrator**
   - Alinhamento com o contrato de saída da skill
   - Nome descritivo e autoexplicativo

2. **Fallback para `var/output/processed/` se enriquecido não existir**
   - Mesma lógica atual (fallback para clean original)
   - Remove o fallback para `processed_fm` que nunca deveria ter existido

3. **Adicionar seção de fluxo canônico ao documento mestre**
   - Seção específica com o encadeamento de diretórios

4. **Adicionar seção de fluxo canônico ao runbook**

## Risks / Trade-offs

- [Baixo] Se houver arquivos apenas em `var/output/processed_fm/` sem equivalentes em `var/output/md-frontmatter-yaml/`, o extrator usará fallback para `var/output/processed/` (clean), perdendo os metadados do frontmatter. Mitigação: manter fallback residual para `processed_fm` como terceira opção, removível em change futura.
