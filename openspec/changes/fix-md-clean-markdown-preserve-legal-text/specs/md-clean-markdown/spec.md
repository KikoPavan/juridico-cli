## ADDED Requirements

### Requirement: Line endings são normalizados para LF antes do processamento

`clean_markdown.py` SHALL normalizar todos os line endings do texto de entrada para `\n` (LF) imediatamente após a leitura do arquivo e antes de qualquer processamento de linha. Sequências `\r\n` (CRLF) e `\r` isolado (CR) MUST ser convertidas para `\n`. O arquivo de saída MUST usar `\n` em todas as linhas.

#### Scenario: arquivo com CRLF produz saída com apenas LF
- **WHEN** `clean_markdown.py` processa um arquivo com line endings `\r\n`
- **THEN** nenhuma linha do arquivo de saída contém `\r`

#### Scenario: linha com CR residual não corrompe caracteres seguintes
- **WHEN** o input contém `AÇÃO\r\n` (CRLF)
- **THEN** o output contém `AÇÃO\n` com o acento `Ã` intacto

---

### Requirement: Caracteres Unicode internos das linhas não são alterados

`clean_markdown.py` SHALL preservar integralmente todos os caracteres Unicode internos das linhas, incluindo letras acentuadas (`ã`, `ã`, `ç`, `é`, `ó`, etc.), cedilhas, e qualquer outro ponto de código acima de U+007F. Nenhuma operação do pipeline (trailing whitespace, heading normalization, bullet normalization, horizontal rule normalization, decorative line removal) MUST alterar os caracteres internos de uma linha de texto.

#### Scenario: AÇÃO permanece AÇÃO após limpeza
- **WHEN** `clean_markdown.py` processa uma linha contendo `AÇÃO DECLARATÓRIA`
- **THEN** o output contém `AÇÃO DECLARATÓRIA` com `Ã` (U+00C3) intacto

#### Scenario: NÃO permanece NÃO após limpeza
- **WHEN** `clean_markdown.py` processa uma linha contendo `NÃO contém`
- **THEN** o output contém `NÃO contém` com `Ã` intacto

#### Scenario: QUALIFICAÇÃO permanece QUALIFICAÇÃO após limpeza
- **WHEN** `clean_markdown.py` processa uma linha contendo `DA QUALIFICAÇÃO`
- **THEN** o output contém `DA QUALIFICAÇÃO` com `Ã` intacto

#### Scenario: PROCURAÇÃO permanece PROCURAÇÃO após limpeza
- **WHEN** `clean_markdown.py` processa uma linha contendo `DA PROCURAÇÃO`
- **THEN** o output contém `DA PROCURAÇÃO` com `Ã` intacto

#### Scenario: PRETENSÃO permanece PRETENSÃO após limpeza
- **WHEN** `clean_markdown.py` processa uma linha contendo `PRETENSÃO`
- **THEN** o output contém `PRETENSÃO` com `Ã` intacto

#### Scenario: marcadores [[Pág. N]] são preservados integralmente
- **WHEN** `clean_markdown.py` processa uma linha contendo `[[Pág. 3]]`
- **THEN** o output contém `[[Pág. 3]]` sem alteração

---

### Requirement: Validação real de ausência de corrupção após execução via CLI

Após corrigir `clean_markdown.py`, a execução do pipeline completo via `data_processing.cli clean` MUST produzir um output sem os padrões de corrupção documentados nesta change.

#### Scenario: grep por padrões corrompidos não retorna resultados
- **WHEN** o pipeline `data_processing.cli clean` processa `var/input/md/Petição Declaração de Nulidade.md`
- **THEN** o arquivo de saída não contém nenhum dos padrões: `AÇÁO`, `NÁO`, `QUALIFICAÇÁO`, `PROCURAÇÁO`, `PRETENSÁO`, `SP#`, `declaratória.#`

## MODIFIED Requirements

### Requirement: CLI end-to-end execution is covered by integration tests

`test_clean_markdown.py` SHALL contain at least one test that invokes `clean_markdown.py` as a subprocess with a real input file and verifies the output file is created and passes `validate_output.run_validation`. Additionally, the suite MUST include regression tests for each corruption pattern documented in change `fix-md-clean-markdown-preserve-legal-text`, using inline string literals (not external fixture files) to ensure self-contained coverage.

#### Scenario: CLI produces valid output from real fixture
- **WHEN** `clean_markdown.py --input <fixture> --output <tmp>` is executed via subprocess
- **THEN** exit code is 0, output file exists and is non-empty, and `validate_output.run_validation` returns 0

#### Scenario: regression - AÇÃO not corrupted
- **WHEN** `clean_lines` processes `["AÇÃO DECLARATÓRIA\n"]`
- **THEN** the output contains `AÇÃO` with `Ã` (U+00C3) unchanged

#### Scenario: regression - NÃO not corrupted
- **WHEN** `clean_lines` processes `["NÃO contém documentação\n"]`
- **THEN** the output contains `NÃO` with `Ã` unchanged

#### Scenario: regression - heading not joined to preceding text
- **WHEN** `clean_lines` processes `["DE CERQUEIRA CÉSAR – SP# DECLARATÓRIA DE NULIDADE\n"]`
- **THEN** the output does NOT contain `SP# DECLARATÓRIA` on a single line
