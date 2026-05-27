# real-output-validation Specification

## Purpose
TBD - created by archiving change validate-md-clean-markdown-after-pdf-to-md. Update Purpose after archive.
## Requirements
### Requirement: Fixture representativa de pdf-to-md
A implementação de `md-clean-markdown` MUST incluir uma fixture representativa de saída gerada por `pdf-to-md`, contendo marcadores de página, texto jurídico útil e ruídos típicos de conversão.

#### Scenario: Fixture contém características reais do pdf-to-md
- **GIVEN** uma saída Markdown produzida por `pdf-to-md`
- **WHEN** a fixture for criada para testes de `md-clean-markdown`
- **THEN** ela MUST conter ao menos dois marcadores no formato `[[Pág. N]]`
- **AND** MUST conter texto jurídico útil
- **AND** MUST conter ruído ou boilerplate típico de conversão

### Requirement: Preservação de marcadores em fixture real
A limpeza executada por `md-clean-markdown` MUST preservar todos os marcadores válidos no formato `[[Pág. N]]` existentes na entrada.

#### Scenario: Limpeza preserva marcadores de página
- **GIVEN** uma fixture com marcadores `[[Pág. 1]]` e `[[Pág. 2]]`
- **WHEN** `md-clean-markdown` processar o conteúdo
- **THEN** a saída MUST manter os marcadores `[[Pág. 1]]` e `[[Pág. 2]]`
- **AND** MUST manter a ordem original dos marcadores

### Requirement: Validação --strict --source contra fixture
A change MUST permitir validação estrita do contrato OpenSpec e dos testes associados à fixture real ou equivalente.

#### Scenario: OpenSpec valida a change em modo estrito
- **GIVEN** a change `validate-md-clean-markdown-after-pdf-to-md`
- **WHEN** o comando `openspec validate validate-md-clean-markdown-after-pdf-to-md --strict` for executado
- **THEN** a validação MUST passar sem erros de especificação

### Requirement: Exemplos de referência baseados em output real
A documentação ou os testes da skill `md-clean-markdown` MUST conter exemplo de referência baseado em saída real ou equivalente de `pdf-to-md`.

#### Scenario: Exemplo demonstra entrada e saída esperadas
- **GIVEN** um exemplo de entrada derivado de `pdf-to-md`
- **WHEN** o exemplo for usado para validar `md-clean-markdown`
- **THEN** ele MUST demonstrar a preservação de `[[Pág. N]]`
- **AND** MUST demonstrar remoção de ruído sem perda de conteúdo jurídico útil

### Requirement: Teste com características reais de pdf-to-md
A skill `md-clean-markdown` MUST possuir teste automatizado cobrindo características reais ou equivalentes de saída do `pdf-to-md`.

#### Scenario: Teste automatizado cobre saída representativa
- **GIVEN** uma fixture representativa de saída do `pdf-to-md`
- **WHEN** os testes de `md-clean-markdown` forem executados
- **THEN** o teste MUST verificar preservação de marcadores `[[Pág. N]]`
- **AND** MUST verificar remoção de ruído dominante
- **AND** MUST verificar que texto jurídico útil permanece na saída

