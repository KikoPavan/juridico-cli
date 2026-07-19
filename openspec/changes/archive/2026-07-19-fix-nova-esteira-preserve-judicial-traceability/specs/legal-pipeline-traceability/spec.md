## ADDED Requirements

### Requirement: Paginação canônica preservada na nova esteira

A nova esteira SHALL entregar `pages_start` e `pages_end` não nulos no envelope curado e no frontmatter final quando a peça possuir paginação canônica ou aliases de paginação disponíveis. Valores canônicos não nulos MUST prevalecer; quando estiverem nulos ou ausentes, `page_number_start` e `page_number_end` MUST ser usados como fallback, respectivamente.

#### Scenario: Aliases preenchem paginação nula
- **WHEN** uma peça entra com `pages_start: null`, `pages_end: null`, `page_number_start: 1` e `page_number_end: 15`
- **THEN** o envelope consumido pelo normalizador e o frontmatter final contêm `pages_start: 1` e `pages_end: 15`

#### Scenario: Paginação canônica explícita prevalece
- **WHEN** uma peça contém `pages_start: 2`, `pages_end: 4`, `page_number_start: 1` e `page_number_end: 15`
- **THEN** a esteira preserva `pages_start: 2` e `pages_end: 4`

### Requirement: Identidade judicial preservada no frontmatter final

O `yaml-normalizador-juridico` SHALL incluir no frontmatter final o identificador processual disponível como `process_number`, aceitando `processo_id` como fallback, SHALL mapear `event_id` para `event` e SHALL preservar `document_code`. Um valor explícito não nulo na peça MUST prevalecer sobre fallbacks do envelope ou do texto.

#### Scenario: Metadados do evento 1 chegam ao frontmatter
- **WHEN** a peça possui `processo_id: "4000153-37.2026.8.26.0136/SP"`, `event_id: "1"` e `document_code: "INIC1"`
- **THEN** o frontmatter final contém `process_number: "4000153-37.2026.8.26.0136/SP"`, `event: "1"` e `document_code: "INIC1"`

#### Scenario: Locator fornece fallback de identidade
- **WHEN** os campos da peça estão ausentes e o texto contém `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="1", document_code="INIC1", page="1"]]`
- **THEN** o frontmatter final contém os mesmos valores de `process_number`, `event` e `document_code`

### Requirement: Corpo normalizado mantém localizadores existentes

O `yaml-normalizador-juridico` MUST preservar no corpo do Markdown final todos os marcadores `[[judicial_locator: ...]]` já presentes no campo de texto recebido, sem remover atributos ou substituir o marcador por paginação genérica.

#### Scenario: Localizador da Petição Inicial é preservado
- **WHEN** o texto recebido contém `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="1", document_code="INIC1", page="1"]]`
- **THEN** o corpo do Markdown final contém literalmente o mesmo marcador

### Requirement: Fallback de impacto protege peças centrais

Quando `impacto_processual` estiver ausente, nulo ou tiver sido produzido apenas pelo fallback genérico, a esteira MUST NOT classificar `peticao_inicial`, `contestacao`, `decisao`, `sentenca` ou `recurso` como `irrelevante`. O fallback mínimo para esses tipos SHALL ser `relevante`, sem rebaixar uma classificação `nuclear` existente.

#### Scenario: Petição inicial sem impacto não vira irrelevante
- **WHEN** uma peça `peticao_inicial` chega à curadoria sem uma classificação de impacto confiável
- **THEN** o envelope curado e o frontmatter final usam no mínimo `impacto_processual: relevante`

#### Scenario: Classificação nuclear é preservada
- **WHEN** uma peça protegida já possui `impacto_processual: nuclear`
- **THEN** nenhuma etapa da nova esteira rebaixa essa classificação

### Requirement: Regressão da Petição Inicial cobre rastreabilidade final

O projeto SHALL possuir teste automatizado focado na nova esteira, usando a fixture `Petição Inicial_evento_1.md` ou fixture mínima sanitizada equivalente, e teste do `yaml-normalizador-juridico` que verifiquem paginação canônica, identidade judicial e preservação do localizador no Markdown final.

#### Scenario: Fixture equivalente passa pela nova esteira
- **WHEN** a fixture contém aliases de páginas 1 a 15 e o localizador judicial do evento 1 com código `INIC1`
- **THEN** o teste confirma `pages_start: 1`, `pages_end: 15` e o marcador judicial intacto no Markdown normalizado

