## ADDED Requirements

### Requirement: Headings embutidos são isolados em linhas próprias

`clean_markdown.py` SHALL detectar e separar headings Markdown (`# texto`, `## texto`, até `######`) que apareçam embutidos no meio de uma linha (padrão `<conteúdo>\s*#+ <texto>`), inserindo uma quebra de linha `\n` imediatamente antes do `#`. Essa passagem MUST ser aplicada antes das demais regras de limpeza por linha, e MUST respeitar o isolamento de blocos de código (a função `_extract_code_blocks` deve ter sido chamada antes).

#### Scenario: heading colado após texto recebe linha própria
- **WHEN** `clean_markdown.py` processa uma linha contendo `DE CERQUEIRA CÉSAR – SP# DECLARATÓRIA DE NULIDADE`
- **THEN** o output contém `DE CERQUEIRA CÉSAR – SP` em uma linha e `# DECLARATÓRIA DE NULIDADE` na linha seguinte

#### Scenario: heading colado após ponto final recebe linha própria
- **WHEN** `clean_markdown.py` processa uma linha contendo `ajuizamento desta demanda declaratória.# DA PROCURAÇÃO SEM PODERES ESPECIAIS`
- **THEN** o output contém `ajuizamento desta demanda declaratória.` em uma linha e `# DA PROCURAÇÃO SEM PODERES ESPECIAIS` na linha seguinte

#### Scenario: heading já em linha própria não é alterado
- **WHEN** `clean_markdown.py` processa uma linha que contém apenas `# TÍTULO CORRETO`
- **THEN** o heading permanece em linha própria sem inserção de linhas extras

#### Scenario: caractere hash em texto não-Markdown é preservado
- **WHEN** `clean_markdown.py` processa uma linha contendo `processo nº 1234#56` (hash sem espaço e sem texto de heading)
- **THEN** a linha é preservada integralmente sem divisão

#### Scenario: headings dentro de blocos de código não são separados
- **WHEN** `clean_markdown.py` processa um bloco de código contendo a linha `` texto # heading ``
- **THEN** o conteúdo interno do bloco é preservado sem modificação
