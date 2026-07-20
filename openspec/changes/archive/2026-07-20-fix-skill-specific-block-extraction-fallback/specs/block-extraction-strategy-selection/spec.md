## ADDED Requirements

### Requirement: Block Extraction Strategy Selected By Bundle ID
`GeminiLLMClient.generate_structured` SHALL selecionar a estratégia de Extração por Blocos a partir do `bundle_id` recebido explicitamente do chamador (repassado desde `DataExtractorApp.run_extraction`), consultando um registro explícito de estratégias (`BLOCK_STRATEGIES` ou mecanismo equivalente). A seleção NÃO MUST inferir a estratégia a partir do conteúdo do schema, do nome de arquivo ou de qualquer heurística implícita.

#### Scenario: Bundle ID with registered strategy resolves that strategy
- **WHEN** `generate_structured` é chamado com `bundle_id="extr-contestacao-processo"` e o preflight ou uma falha de chamada aciona a extração por blocos
- **THEN** a estratégia resolvida e executada é a estratégia registrada para `extr-contestacao-processo`, não a de `extr-peticao-processo`

#### Scenario: Different bundle IDs never share a strategy instance implicitly
- **WHEN** `generate_structured` é chamado em sequência para `bundle_id="extr-peticao-processo"` e depois para `bundle_id="extr-contestacao-processo"` com o mesmo schema básico de entrada
- **THEN** cada chamada produz um resultado consolidado cujo conjunto de chaves corresponde exclusivamente aos campos permitidos pelo schema do `bundle_id` daquela chamada

### Requirement: Unregistered Skill Fails Safely Without Falling Back to Petição Strategy
Quando o `bundle_id` não possuir estratégia de blocos registrada, o sistema SHALL levantar um erro controlado e específico antes de qualquer chamada ao Gemini para blocos, e NÃO MUST executar `PeticaoBlockStrategy` (ou qualquer outra estratégia registrada) como comportamento padrão.

#### Scenario: Skill without block strategy raises a controlled error
- **WHEN** `generate_structured` precisa escalar para blocos e `bundle_id` não está presente em `BLOCK_STRATEGIES`
- **THEN** o sistema levanta uma exceção específica identificando o `bundle_id` sem estratégia disponível, sem invocar `PeticaoBlockStrategy` nem qualquer outra estratégia registrada

#### Scenario: No JSON is persisted when strategy is unavailable
- **WHEN** a exceção de estratégia indisponível é levantada durante `DataExtractorApp.run_extraction`
- **THEN** nenhum arquivo de resultado é escrito em `var/output/extracted/` para essa execução

### Requirement: Bundle ID Threaded From Extraction Entry Point
`DataExtractorApp.run_extraction` SHALL repassar o `bundle_id` já resolvido pelo `SkillDispatcher` para `GeminiLLMClient.generate_structured` como parâmetro explícito, e `generate_structured` SHALL aceitar esse parâmetro como opcional para preservar compatibilidade com chamadores legados que não o fornecem.

#### Scenario: Extractor passes bundle_id explicitly
- **WHEN** `DataExtractorApp.run_extraction(bundle_id, input_filename)` executa uma extração que aciona blocos
- **THEN** `generate_structured` recebe esse mesmo `bundle_id` e o usa para resolver a estratégia

#### Scenario: Legacy caller without bundle_id still runs single-strategy tests
- **WHEN** um chamador de teste invoca `generate_structured(messages, schema=schema)` sem informar `bundle_id`
- **THEN** a chamada não quebra por erro de assinatura; se blocos forem necessários sem `bundle_id` resolvível, o sistema falha de forma controlada em vez de assumir uma estratégia padrão

### Requirement: Final Consolidated Result Validated Against Full Skill Schema
Cada estratégia de blocos SHALL validar o JSON consolidado final contra o schema completo da skill correspondente antes de retorná-lo, e o resultado inválido NÃO MUST ser retornado como sucesso nem persistido.

#### Scenario: Valid consolidated result passes and is returned
- **WHEN** uma estratégia de blocos consolida um JSON que satisfaz o schema completo da skill
- **THEN** o resultado é retornado normalmente ao chamador

#### Scenario: Invalid consolidated result raises instead of returning
- **WHEN** o JSON consolidado por uma estratégia de blocos viola o schema completo da skill
- **THEN** a estratégia levanta um erro descrevendo as violações, em vez de retornar o objeto inválido

### Requirement: Anchor Page Marker Is Never Reduced To Empty Brackets
A consolidação de blocos SHALL garantir que o campo `page_marker` de qualquer âncora no resultado final contenha uma referência de página ou locator não vazia, e NÃO MUST conter o valor literal `"[]"` nem uma string vazia.

#### Scenario: LLM-provided malformed page_marker is corrected during consolidation
- **WHEN** a resposta de um bloco contém uma âncora com `page_marker` igual a `"[]"` ou vazio
- **THEN** a consolidação substitui esse valor pela melhor referência de página conhecida no momento (marcador de página ativo ou locator estrutural), e o `page_marker` final não é `"[]"` nem vazio

#### Scenario: Valid page_marker from the LLM is preserved unchanged
- **WHEN** a resposta de um bloco contém uma âncora com `page_marker` válido (ex.: `"3"`, `"[[Pág. 3]]"`)
- **THEN** a consolidação preserva esse valor sem alterá-lo
