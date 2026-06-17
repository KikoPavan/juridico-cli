## Why

O caminho de saída da etapa `md-frontmatter-yaml` está inconsistente: o skill grava em `var/output/md-frontmatter-yaml/`, mas o extrator (`DataExtractorApp`) busca os arquivos enriquecidos em `var/output/processed_fm/`. Essa duplicidade de caminhos gera confusão operacional e quebra o fluxo canônico documentado.

## What Changes

- `apps/data-processing/src/data_processing/extractor.py`: corrigir caminho `input_processed_fm` de `var/output/processed_fm` para `var/output/md-frontmatter-yaml`
- Manter fallback para `var/output/processed_fm` temporariamente durante migração
- Atualizar `docs/architecture/juridico_cli_documento_mestre.md` com o fluxo canônico
- Atualizar `docs/runbooks/runbook_operacional_minimo.md` com o fluxo canônico
- **Não alterar**: provider Gemini, módulo clean, módulo convert, schema da petição
- **Não commitar**, não arquivar

## Capabilities

### New Capabilities

Nenhuma. Mudança puramente de caminho de diretório.

### Modified Capabilities

Nenhuma. A spec `md-frontmatter-yaml` não muda — apenas a implementação e documentação refletem o caminho correto.

## Impact

- `extractor.py`: troca `processed_fm` → `md-frontmatter-yaml` com fallback
- `docs/architecture/juridico_cli_documento_mestre.md`: atualizar fluxo canônico
- `docs/runbooks/runbook_operacional_minimo.md`: atualizar fluxo canônico
- Nenhuma skill, schema, provider ou módulo convert/clean é alterado
