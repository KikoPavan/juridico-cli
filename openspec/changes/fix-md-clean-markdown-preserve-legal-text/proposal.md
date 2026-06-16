## Why

O comando `data_processing.cli clean` corrompe textos jurídicos válidos: acentos do tipo `ÃO` são convertidos para `ÁO` (`AÇÃO` → `AÇÁO`, `NÃO` → `NÁO`), e headings Markdown (`# TÍTULO`) colam ao final da linha anterior. Investigação confirmou que a causa está em `apps/data-processing/src/data_processing/cleaners/clean_legal_docs.py` — o cleaner real do pipeline. A skill `platform/skills/md-clean-markdown/scripts/clean_markdown.py` **não é chamada** pelo CLI `data_processing.cli clean` e não produz nenhuma corrupção.

## What Changes

- **Remover** a entrada `"Ã": "Á"` do dicionário de replacements em `LegalDocCleaner.fix_encoding` — esta entrada substituía o caractere `Ã` (U+00C3) válido por `Á` (U+00C1), corrompendo todas as palavras com `ÃO` no documento.
- **Corrigir** todos os padrões de remoção em `LegalDocCleaner.patterns_to_remove` que terminam com `\s*`, substituindo pelo quantificador `[ \t]*` (apenas espaço e tab horizontal). O `\s*` original consumia o `\n` após o cabeçalho removido, colando a linha seguinte (frequentemente um heading `# ...`) ao texto anterior.
- **Adicionar** testes de regressão em `apps/data-processing/tests/test_cleaners.py` cobrindo os exemplos reais de corrupção documentados nesta change.

## Capabilities

### New Capabilities

- `heading-isolation`: garantia de que headings Markdown (`# ...`) removidos por `patterns_to_remove` não colem ao texto adjacente — via uso de `[ \t]*` em vez de `\s*` como quantificador final dos padrões de remoção.

### Modified Capabilities

- `md-clean-markdown`: a spec existente recebe requisito adicional de preservação de caracteres Unicode internos e isolamento de headings. Nota: a implementação da correção ocorre em `clean_legal_docs.py` (cleaner real do pipeline), não em `clean_markdown.py`.

## Impact

- `apps/data-processing/src/data_processing/cleaners/clean_legal_docs.py` — remoção de `"Ã": "Á"` e substituição de `\s*` → `[ \t]*` nos padrões de remoção.
- `apps/data-processing/tests/test_cleaners.py` — adição de testes de regressão obrigatórios.
- `platform/skills/md-clean-markdown/` — **não alterado** (nenhum bug confirmado neste módulo pelo fluxo `data_processing.cli clean`).
- Nenhum outro módulo, skill ou arquivo de configuração é afetado.
