## ADDED Requirements

### Requirement: Executar normalização de ligaduras no pipeline de limpeza
O pipeline `md-clean-markdown` SHALL expandir ligaduras tipográficas antes da correção de encoding e antes das demais transformações estruturais.

#### Scenario: Ligadura é normalizada antes da limpeza estrutural
- **WHEN** o pipeline recebe Markdown contendo `ﬁ` e `ﬂ`
- **THEN** a saída MUST conter `fi` e `fl`
- **AND** os estágios posteriores MUST receber o texto já normalizado

### Requirement: Executar recomposição antes da limpeza estrutural
O pipeline `md-clean-markdown` SHALL recompor palavras hifenizadas e linhas de prosa fragmentadas antes de normalizar headings, bullets, separadores e espaços em branco. O pipeline MUST preservar marcadores judiciais e blocos de código durante essa etapa.

#### Scenario: Ordem do pipeline preserva estrutura
- **WHEN** o Markdown contém prosa fragmentada, um heading e um marcador `[[judicial_locator: ...]]`
- **THEN** a prosa MUST ser recomposta antes das transformações estruturais
- **AND** o heading e o marcador MUST permanecer em limites de linha separados

#### Scenario: Bloco de código não é recomposto
- **WHEN** um bloco de código cercado contém linhas que satisfariam as heurísticas de recomposição
- **THEN** seu conteúdo MUST permanecer idêntico à entrada
