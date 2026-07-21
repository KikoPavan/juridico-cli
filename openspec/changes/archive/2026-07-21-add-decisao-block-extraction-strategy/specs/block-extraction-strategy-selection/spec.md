## MODIFIED Requirements

### Requirement: Block Extraction Strategy Selected By Bundle ID
`GeminiLLMClient.generate_structured` SHALL selecionar a estratégia de Extração por Blocos a partir do `bundle_id` recebido explicitamente do chamador (repassado desde `DataExtractorApp.run_extraction`), consultando um registro explícito de estratégias (`BLOCK_STRATEGIES` ou mecanismo equivalente). O registro SHALL associar `extr-peticao-processo`, `extr-contestacao-processo` e `extr-decisao-processo` às respectivas estratégias exclusivas. A seleção NÃO MUST inferir a estratégia a partir do conteúdo do schema, do nome de arquivo ou de qualquer heurística implícita.

#### Scenario: Bundle ID with registered strategy resolves that strategy
- **WHEN** `generate_structured` é chamado com `bundle_id="extr-contestacao-processo"` e o preflight ou uma falha de chamada aciona a extração por blocos
- **THEN** a estratégia resolvida e executada é a estratégia registrada para `extr-contestacao-processo`, não a de `extr-peticao-processo` nem a de `extr-decisao-processo`

#### Scenario: Decision bundle resolves decision strategy
- **WHEN** `generate_structured` é chamado com `bundle_id="extr-decisao-processo"` e a extração por blocos é acionada
- **THEN** a estratégia resolvida e executada é `DecisaoBlockStrategy` ou equivalente, sem executar estratégia de petição ou contestação

#### Scenario: Different bundle IDs never share a strategy instance implicitly
- **WHEN** `generate_structured` é chamado em sequência para `bundle_id="extr-peticao-processo"`, `bundle_id="extr-contestacao-processo"` e `bundle_id="extr-decisao-processo"`
- **THEN** cada chamada produz um resultado consolidado cujo conjunto de chaves corresponde exclusivamente aos campos permitidos pelo schema do `bundle_id` daquela chamada

### Requirement: Anchor Page Marker Is Never Reduced To Empty Brackets
A consolidação de blocos SHALL garantir que o campo `page_marker` de qualquer âncora no resultado final contenha uma referência de página ou locator não vazia, e NÃO MUST conter o valor literal `"[]"`, uma string vazia, um número fictício ou um locator inválido. Para a estratégia de decisão, a correção SHALL usar somente marcador real encontrado no documento; na ausência de marcador confiável, o item que exige anchor SHALL ser omitido em vez de receber default inventado. O comportamento já validado das estratégias de petição e contestação SHALL permanecer preservado.

#### Scenario: LLM-provided malformed page_marker is corrected during consolidation
- **WHEN** a resposta de um bloco de petição ou contestação contém uma âncora com `page_marker` igual a `"[]"` ou vazio
- **THEN** a consolidação aplica o comportamento compatível já existente e o `page_marker` final não é `"[]"` nem vazio

#### Scenario: Decision malformed page_marker uses only documentary evidence
- **WHEN** a resposta de um bloco de decisão contém `page_marker` vazio, `"[]"` ou locator inválido
- **THEN** a resposta parcial é rejeitada e o fallback somente produz anchor se houver marcador real aplicável no Markdown

#### Scenario: Valid page_marker from the LLM is preserved unchanged
- **WHEN** a resposta de um bloco contém uma âncora com `page_marker` válido, como `"[[Pág. 3]]"` ou um `judicial_locator` real
- **THEN** a consolidação preserva esse valor sem alterá-lo
