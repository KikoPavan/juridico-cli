# document-content-validation Specification

## Purpose

Define the requirements for deciding whether a complete judicial Markdown document contains meaningful content before structured extraction.

## Requirements

### Requirement: Validar conteúdo útil do documento completo
O sistema SHALL validar o Markdown completo, depois da limpeza e montagem do frontmatter e antes da extração JSON, removendo da contagem frontmatter, marcadores `[[judicial_locator: ...]]`, localizadores judiciais textuais e boilerplate reconhecido. Por padrão, o documento MUST conter ao menos 50 caracteres úteis, e o limite SHALL ser configurável.

#### Scenario: Documento com conteúdo jurídico suficiente é aceito
- **WHEN** após excluir metadados e boilerplate restam pelo menos 50 caracteres úteis
- **THEN** o documento MUST ser elegível para a extração JSON

#### Scenario: Limite configurado é respeitado
- **WHEN** o limite é configurado com valor diferente do padrão
- **THEN** a decisão MUST usar o valor configurado

### Requirement: Rejeitar documento sem conteúdo significativo
O sistema SHALL rejeitar documentos vazios ou compostos apenas por localizadores judiciais, frontmatter e boilerplate. A rejeição MUST usar o motivo estável `no_meaningful_content` e MUST impedir o envio do documento ao LLM de extração.

#### Scenario: Documento com apenas localizadores é rejeitado
- **WHEN** o Markdown contém somente frontmatter e marcadores `[[judicial_locator: ...]]`
- **THEN** o documento MUST ser marcado como `rejected: no_meaningful_content`
- **AND** o extrator JSON MUST NOT ser invocado

#### Scenario: Documento vazio é rejeitado
- **WHEN** após a exclusão de metadados e boilerplate não resta conteúdo útil
- **THEN** o documento MUST ser marcado como `rejected: no_meaningful_content`

### Requirement: Preservar o documento durante a validação
A validação SHALL ser uma operação de decisão e MUST NOT alterar o Markdown persistido nem remover seus marcadores ou frontmatter.

#### Scenario: Validação não modifica a entrada
- **WHEN** um documento é validado como aceito ou rejeitado
- **THEN** o conteúdo Markdown antes e depois da validação MUST ser idêntico
