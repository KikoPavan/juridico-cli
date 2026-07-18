# eproc-page-structuring Specification

## Purpose

Define the requirements for extracting and serializing metadata from eproc/TJSP electronic separator pages.

## Requirements

### Requirement: Extrair metadados de páginas de separação eletrônica
O sistema SHALL reconhecer páginas de separação do eproc/TJSP e extrair, quando presentes, `process_number`, `event`, `event_title`, `date`, `user`, `user_role` e `sequence`. Campos ausentes MUST permanecer ausentes, sem valores inventados.

#### Scenario: Página completa é estruturada
- **WHEN** uma página de separação contém processo, evento, título do evento, data, usuário, papel e sequência
- **THEN** o sistema MUST extrair cada valor no campo correspondente

#### Scenario: Página parcial não gera dados fictícios
- **WHEN** uma página de separação contém apenas processo, evento e sequência
- **THEN** o sistema MUST extrair os três campos presentes
- **AND** MUST NOT preencher `event_title`, `date`, `user` ou `user_role` com valores inferidos

### Requirement: Serializar metadados no localizador judicial
O sistema SHALL serializar os metadados extraídos no marcador canônico `[[judicial_locator: ...]]`, escapando valores de modo que o marcador continue analisável e preservando a ordem canônica dos atributos.

#### Scenario: Metadados completos são serializados
- **WHEN** os metadados extraídos são processo `4000153-37.2026.8.26.0136/SP`, evento `43`, título `Contestação`, data `2026-07-17`, usuário `Maria`, papel `Advogada` e sequência `1`
- **THEN** o marcador MUST conter `process_number="4000153-37.2026.8.26.0136/SP"`, `event="43"`, `event_title="Contestação"`, `date="2026-07-17"`, `user="Maria"`, `user_role="Advogada"` e `sequence="1"`

#### Scenario: Marcador estruturado pode ser analisado novamente
- **WHEN** o sistema analisa um marcador gerado para uma página de separação
- **THEN** o dicionário resultante MUST preservar todos os campos e valores serializados

### Requirement: Página de separação não é tratada como conteúdo jurídico útil
O sistema SHALL distinguir o texto usado exclusivamente para formar o localizador judicial do corpo jurídico do documento.

#### Scenario: Separador isolado não produz corpo útil
- **WHEN** uma página contém somente dados de separação eletrônica
- **THEN** o sistema MUST produzir o localizador estruturado
- **AND** MUST NOT considerar o texto do separador como conteúdo jurídico útil
