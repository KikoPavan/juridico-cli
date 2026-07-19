## ADDED Requirements

### Requirement: Aliases de paginação são canonicalizados

O contrato do `segmentador-juridico` SHALL aceitar `page_number_start` e `page_number_end` como aliases opcionais de paginação. Antes de entregar uma peça ao `curador-relevancia`, a esteira MUST preencher `pages_start` a partir de `page_number_start` e `pages_end` a partir de `page_number_end` quando o respectivo campo canônico estiver ausente ou nulo. Um valor canônico não nulo MUST prevalecer sobre seu alias.

#### Scenario: Resposta do modelo com aliases é canonicalizada
- **WHEN** a resposta segmentada contém `page_number_start: 1`, `page_number_end: 15`, `pages_start: null` e `pages_end: null`
- **THEN** a peça validada entregue ao curador contém `pages_start: 1` e `pages_end: 15`

#### Scenario: Alias não sobrescreve valor canônico
- **WHEN** a resposta contém `pages_start: 2` e `page_number_start: 1`
- **THEN** a peça validada mantém `pages_start: 2`

### Requirement: Schema transporta metadados judiciais disponíveis

O schema de saída do `segmentador-juridico` SHALL permitir que cada peça e seus anchors transportem `process_number` ou `processo_id`, `event_id` ou `event`, `document_code` e `page` quando disponíveis, para consumo pelas etapas seguintes.

#### Scenario: Peça segmentada transporta identidade do documento
- **WHEN** a segmentação conhece processo `4000153-37.2026.8.26.0136/SP`, evento `1` e código `INIC1`
- **THEN** a saída validada mantém esses valores em campos aceitos pelo contrato e disponíveis ao curador

