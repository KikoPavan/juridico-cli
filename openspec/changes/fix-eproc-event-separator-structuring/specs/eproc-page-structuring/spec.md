## MODIFIED Requirements

### Requirement: Extrair metadados de páginas de separação eletrônica
O sistema SHALL reconhecer páginas de separação do eproc/TJSP e extrair, quando presentes, `process_number`, `event`, `event_title`, `date`, `user`, `user_role` e `sequence`. Campos ausentes MUST permanecer ausentes, sem valores inventados.

#### Scenario: Página completa é estruturada
- **WHEN** uma página de separação contém processo, evento, título do evento, data, usuário, papel e sequência
- **THEN** o sistema MUST extrair cada valor no campo correspondente

#### Scenario: Página parcial não gera dados fictícios
- **WHEN** uma página de separação contém apenas processo, evento e sequência
- **THEN** o sistema MUST extrair os três campos presentes
- **AND** MUST NOT preencher `event_title`, `date`, `user` ou `user_role` com valores inferidos

#### Scenario: Rótulos agrupados são associados aos valores subsequentes
- **WHEN** a página de separação contém, em ordem, os rótulos vazios `Evento`, `Data`, `Usuário`, `Processo` e `Sequência Evento`, seguidos pelo título `DETERMINADA A CITACAO`, data `27/04/2026 13:34:24`, usuário e papel `J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO - MAGISTRADO`, processo `4000153-37.2026.8.26.0136/SP` e sequência `32`
- **THEN** o sistema MUST extrair `event="32"`, `event_title="DETERMINADA A CITACAO"`, `date="27/04/2026 13:34:24"`, `user="J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO"`, `user_role="MAGISTRADO"`, `process_number="4000153-37.2026.8.26.0136/SP"` e `sequence="32"`

### Requirement: Serializar metadados no localizador judicial
O sistema SHALL serializar os metadados extraídos no marcador canônico `[[judicial_locator: ...]]`, escapando valores de modo que o marcador continue analisável e preservando a ordem canônica dos atributos.

#### Scenario: Metadados completos são serializados
- **WHEN** os metadados extraídos são processo `4000153-37.2026.8.26.0136/SP`, evento `43`, título `Contestação`, data `2026-07-17`, usuário `Maria`, papel `Advogada` e sequência `1`
- **THEN** o marcador MUST conter `process_number="4000153-37.2026.8.26.0136/SP"`, `event="43"`, `event_title="Contestação"`, `date="2026-07-17"`, `user="Maria"`, `user_role="Advogada"` e `sequence="1"`

#### Scenario: Marcador estruturado pode ser analisado novamente
- **WHEN** o sistema analisa um marcador gerado para uma página de separação
- **THEN** o dicionário resultante MUST preservar todos os campos e valores serializados

#### Scenario: Primeiro localizador identifica a página de separação
- **WHEN** a primeira página contém o separador completo do evento 32 e já possui um localizador com `event="32"` e `page="1"`
- **THEN** o primeiro localizador MUST preservar `page="1"`, conter todos os metadados extraídos do separador e incluir `kind="event_separator"`

### Requirement: Página de separação não é tratada como conteúdo jurídico útil
O sistema SHALL distinguir o texto usado exclusivamente para formar o localizador judicial do corpo jurídico do documento.

#### Scenario: Separador isolado não produz corpo útil
- **WHEN** uma página contém somente dados de separação eletrônica
- **THEN** o sistema MUST produzir o localizador estruturado
- **AND** MUST NOT considerar o texto do separador como conteúdo jurídico útil

#### Scenario: Bloco reconhecido é reescrito de forma legível
- **WHEN** o Markdown limpo contém o separador reconhecido com rótulos vazios e valores soltos
- **THEN** o Markdown final MUST representar os metadados do separador em formato chave/valor legível
- **AND** MUST NOT manter rótulos vazios nem os respectivos valores como linhas soltas
