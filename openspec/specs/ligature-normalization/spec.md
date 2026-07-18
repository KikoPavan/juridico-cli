# ligature-normalization Specification

## Purpose

Define the requirements for expanding typographic Unicode ligatures without corrupting valid judicial text.

## Requirements

### Requirement: Expandir ligaduras tipográficas Unicode
O sistema SHALL substituir ligaduras tipográficas Unicode por suas sequências ASCII equivalentes antes das demais correções de encoding. A normalização MUST contemplar ao menos `ﬀ`, `ﬁ`, `ﬂ`, `ﬃ`, `ﬄ`, `ﬅ` e `ﬆ`, sem alterar caracteres Unicode que não sejam ligaduras mapeadas.

#### Scenario: Ligaduras conhecidas são expandidas
- **WHEN** o normalizador recebe `oﬁcial ﬂagrante oﬀício ﬃ ﬄ ﬅ ﬆ`
- **THEN** o resultado MUST ser `oficial flagrante offício ffi ffl st st`

#### Scenario: Texto Unicode legítimo é preservado
- **WHEN** o normalizador recebe `AÇÃO, NÃO e § 1º` sem ligaduras mapeadas
- **THEN** o resultado MUST permanecer idêntico à entrada

### Requirement: Normalização de ligaduras é idempotente
O sistema SHALL produzir o mesmo resultado ao aplicar a normalização uma ou mais vezes ao mesmo texto.

#### Scenario: Segunda aplicação não altera o resultado
- **WHEN** um texto contendo ligaduras é normalizado duas vezes
- **THEN** o resultado da segunda aplicação MUST ser idêntico ao da primeira
