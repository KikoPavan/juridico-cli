## ADDED Requirements

### Requirement: Deterministic Preflight Before Any Gemini Call
[GeminiLLMClient.generate_structured](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L72) MUST avaliar, através de [GeminiLLMClient._assess_response_schema_compatibility](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L84), se o schema sanitizado é compatível com o modo `response_schema` do Gemini **antes de fazer qualquer chamada ao Gemini** (nem a chamada estruturada inicial, nem o fallback livre). A avaliação MUST ser determinística e basear-se apenas no schema sanitizado (tamanho em bytes, quantidade de propriedades top-level, quantidade de nós), sem depender de uma chamada à API para ser decidida.

#### Scenario: Compatible schema proceeds to the structured call
- **WHEN** o schema sanitizado está dentro dos limiares de complexidade configurados (`_SCHEMA_PREFLIGHT_SIZE_BYTES_THRESHOLD`, `_SCHEMA_PREFLIGHT_TOP_PROPERTIES_THRESHOLD`, `_SCHEMA_PREFLIGHT_NODE_COUNT_THRESHOLD`)
- **THEN** `generate_structured` tenta a chamada estruturada inicial com `response_json_schema` normalmente

#### Scenario: Incompatible schema skips the structured call entirely
- **WHEN** o schema sanitizado excede qualquer um dos limiares de complexidade configurados
- **THEN** `generate_structured` NÃO MUST chamar `generate_content` com esse schema completo; nenhuma chamada estruturada nem chamada de fallback livre é feita para esse schema

### Requirement: Incompatible Schemas Escalate Directly to Block Extraction
Quando o preflight considera o schema sanitizado incompatível, `generate_structured` MUST chamar `_execute_extraction_in_blocks` diretamente, sem tentar a chamada estruturada inicial nem o fallback livre.

#### Scenario: Real extr-peticao-processo schema escalates to blocks without a 400
- **WHEN** `generate_structured` é chamado com o schema canônico completo de `extr-peticao-processo` (conhecido por exceder os limiares de preflight)
- **THEN** a extração é concluída via `_execute_extraction_in_blocks`, e nenhuma chamada a `generate_content` usa o schema completo como `response_json_schema`

#### Scenario: No incompatible call ever reaches the Gemini client
- **WHEN** o preflight decide que o schema é incompatível
- **THEN** a primeira chamada real a `generate_content` feita pelo cliente já é uma chamada de bloco com um schema reduzido (dentro dos limiares de preflight), nunca o schema completo

### Requirement: Preflight Decision Is Logged Distinctly From API Errors
Quando o preflight decide escalar para blocos por incompatibilidade, o sistema MUST registrar um log que identifique essa decisão como resultado do preflight (avaliação de complexidade antes da chamada), e NÃO MUST gravar o arquivo de erro da chamada estruturada (`structured_call_error.txt`) para esse caso, já que nenhuma chamada foi de fato tentada nem falhou.

#### Scenario: Preflight skip is logged as a preflight decision, not an API failure
- **WHEN** o preflight decide que um schema é incompatível e escala para blocos
- **THEN** o log registrado menciona explicitamente que a decisão foi tomada em preflight (por complexidade do schema), e não que uma chamada à API falhou

#### Scenario: No structured_call_error.txt is written for a preflight skip
- **WHEN** o preflight decide que um schema é incompatível e escala para blocos
- **THEN** nenhum arquivo `structured_call_error.txt` é criado em `var/artifacts/gemini-debug/` como resultado dessa decisão

### Requirement: Preflight Does Not Change Canonical Schemas, Provider, or Model
A avaliação de preflight e a escalada para blocos MUST operar inteiramente sobre o schema sanitizado já existente e o cliente Gemini já configurado. Elas NÃO MUST alterar nenhum schema canônico de skill, e NÃO MUST alterar o provider (Gemini) ou o modelo configurado em [GeminiLLMClient.__init__](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L79).

#### Scenario: Canonical schema file is untouched
- **WHEN** o preflight escala um schema para extração por blocos
- **THEN** o arquivo do schema canônico da skill em `platform/skills/*/assets/*.schema.json` permanece byte-a-byte idêntico

#### Scenario: Provider and model stay the same
- **WHEN** o preflight escala um schema para extração por blocos
- **THEN** a chamada de bloco usa o mesmo `self.client` (Gemini) e o mesmo `self.model_name` já configurados na instância, sem trocar de provider ou modelo

### Requirement: Final Result Still Validated Against the Local Rich Schema
A escalada por preflight para a extração por blocos NÃO MUST alterar a validação local final: o JSON consolidado produzido pelos blocos MUST continuar sendo validado contra o schema rico completo antes de ser considerado um resultado válido, da mesma forma que já ocorre em `_execute_extraction_in_blocks` para escaladas reativas.

#### Scenario: Block-mode result from a preflight skip validates like any other block-mode result
- **WHEN** o preflight escala um schema para blocos e os blocos produzem um JSON consolidado que satisfaz o schema rico completo
- **THEN** esse resultado passa na validação local (`local_resolver.load_validator`) da mesma forma que passaria se a extração por blocos tivesse sido acionada reativamente após uma falha de API
