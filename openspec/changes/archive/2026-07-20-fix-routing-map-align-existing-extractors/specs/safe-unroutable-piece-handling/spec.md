## MODIFIED Requirements

### Requirement: Peça não roteável nunca fica pronta para extração profunda

O `yaml-normalizador-juridico` MUST resolver peças sem skill reconhecida para `REVISAR_MANUAL` e MUST produzir `review_status: unroutable` e `status: needs_review`, independentemente de a ação recebida ser `manter` ou `resumir`. O frontmatter MUST NOT declarar uma skill `extr-*` inexistente. Essa política MUST abranger ao menos `contrato`, `escritura`, `recurso`, `laudo_pericial`, `nota_fiscal`, `boleto`, `citacao`, `intimacao` e `nao_classificado`, enquanto não houver extrator específico registrado.

#### Scenario: Tipo não classificado não sai ready
- **WHEN** o normalizador recebe uma peça `nao_classificado` sem encaminhamento profundo
- **THEN** o frontmatter usa `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review`

#### Scenario: Contrato genérico não infere contrato social
- **WHEN** o normalizador recebe `document_type: contrato`
- **THEN** o frontmatter usa `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review`

#### Scenario: Escritura genérica não infere subtipo
- **WHEN** o normalizador recebe `document_type: escritura`
- **THEN** o frontmatter usa `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review`

#### Scenario: Tipo conhecido sem extrator fica para revisão
- **WHEN** o normalizador recebe `recurso`, `laudo_pericial`, `nota_fiscal`, `boleto`, `citacao` ou `intimacao`
- **THEN** o frontmatter usa `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review`
