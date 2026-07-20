# gemini-fallback-escalation Specification

## Purpose
Governar quando `GeminiLLMClient.generate_structured` deve pular o fallback livre (com retry de reparo) e escalar diretamente para a extração por blocos, com base em um sinal determinístico de risco de truncamento avaliado a partir do tamanho do Markdown de entrada e da quantidade de propriedades top-level do schema — em vez de depender apenas da detecção reativa de truncamento na resposta do Gemini.

## Requirements
### Requirement: Truncation Risk Assessment Before Free-Form Fallback
Quando a chamada estruturada inicial com `response_json_schema` falhar, [GeminiLLMClient.generate_structured](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L61) MUST avaliar um sinal determinístico de risco de truncamento — baseado no tamanho do conteúdo Markdown de entrada e na quantidade de propriedades top-level requisitadas no schema — antes de decidir entre tentar o fallback livre (com retry de reparo) ou escalar diretamente para a extração por blocos.

#### Scenario: Small input takes the existing free-form fallback path
- **WHEN** a chamada estruturada falha e o Markdown de entrada e a contagem de propriedades top-level do schema estão abaixo dos limiares de risco configurados
- **THEN** o sistema executa a tentativa de fallback livre (com retry de reparo) como hoje, antes de considerar a extração por blocos

#### Scenario: Large input skips the free-form fallback path
- **WHEN** a chamada estruturada falha e o Markdown de entrada ou a contagem de propriedades top-level do schema excede os limiares de risco configurados
- **THEN** o sistema não executa a chamada de fallback livre inicial nem o retry de reparo, e chama `_execute_extraction_in_blocks` diretamente

### Requirement: Block Fallback Activation Is Predictable for High-Risk Inputs
Para entradas classificadas como alto risco de truncamento, a ativação da extração por blocos MUST depender apenas dos sinais de entrada (tamanho do Markdown, contagem de propriedades top-level do schema) avaliados antes de qualquer chamada ao Gemini, e NÃO MUST depender do resultado de tentativas anteriores de fallback livre.

#### Scenario: Same large input always escalates the same way
- **WHEN** a mesma entrada de alto risco (mesmo Markdown, mesmo schema) é processada em execuções distintas
- **THEN** a decisão de escalar diretamente para a extração por blocos é a mesma em todas as execuções, sem depender de variação na resposta do Gemini a uma tentativa livre

### Requirement: Low-Risk Path Preserves Existing Fallback Behavior
Para entradas classificadas como baixo risco de truncamento, o comportamento de fallback livre com retry de reparo, incluindo a detecção reativa de truncamento (`finish_reason == "MAX_TOKENS"`, erros de parse indicando corte, ou resposta acima do limite de tamanho), MUST permanecer inalterado em relação ao comportamento existente antes desta mudança.

#### Scenario: Existing reactive truncation detection still applies for low-risk inputs
- **WHEN** um fallback livre para uma entrada de baixo risco retorna uma resposta truncada de forma inesperada
- **THEN** o sistema aplica a mesma lógica reativa de retry de reparo e, se necessário, escalada para blocos já existente antes desta mudança
