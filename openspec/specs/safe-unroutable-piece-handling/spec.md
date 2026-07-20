# safe-unroutable-piece-handling Specification

## Purpose

Definir o tratamento seguro de peças jurídicas sem extrator profundo reconhecido, preservando-as para revisão sem inventar classificação ou roteamento.

## Requirements

### Requirement: Peça sem rota recebe curadoria segura

O `curador-relevancia` MUST identificar peças cujo `document_type` não possui encaminhamento `extr-*` reconhecido. Sem impacto de sentença confirmado, essas peças MUST NOT ser classificadas como `nuclear` apenas por `relevancia_estimada`, MUST receber impacto no máximo `acessorio`, ação `revisar` ou `resumir`, prioridade compatível e `encaminhamento: null`.

#### Scenario: Pedido de habilitação permanece não classificado e revisável
- **WHEN** uma peça `nao_classificado` possui `document_code: PED HABILIT1`, relevância estimada alta e nenhum extrator mapeado
- **THEN** o curador não a marca como nuclear, mantém `encaminhamento: null` e a encaminha para revisão ou síntese segura

#### Scenario: Impacto confirmado preserva segurança jurídica
- **WHEN** uma peça sem rota possui `impacto_sentenca_confirmado: true`
- **THEN** a proteção de preservação prevalece, mas nenhum extrator inexistente é inventado

### Requirement: Peça não roteável nunca fica pronta para extração profunda

O `yaml-normalizador-juridico` MUST resolver peças sem skill reconhecida para a rota segura existente e MUST produzir `review_status: unroutable` e `status: needs_review`, independentemente de a ação recebida ser `manter` ou `resumir`. O frontmatter MUST NOT declarar uma skill `extr-*` inexistente.

#### Scenario: Tipo não classificado não sai ready
- **WHEN** o normalizador recebe uma peça `nao_classificado` sem encaminhamento profundo
- **THEN** o frontmatter usa `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review`
