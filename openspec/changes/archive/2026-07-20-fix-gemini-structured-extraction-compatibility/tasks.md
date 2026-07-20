## 1. Repro e evidência

- [x] 1.1 Confirmar localmente, a partir dos artefatos existentes em `var/artifacts/gemini-debug/` (`peticao_processo.response_schema.sanitized.json`, `structured_call_error.txt`), que o `anyOf` raiz `required`-only é o schema efetivamente rejeitado com `400 INVALID_ARGUMENT`. **Confirmado**: `structured_call_error.txt` contém `400 INVALID_ARGUMENT`; o `anyOf` raiz do schema sanitizado tem 6 branches `{"required": [...]}` sem `type`.
- [x] 1.2 Se `GEMINI_API_KEY` estiver disponível no ambiente, rodar `tests/test_gemini_schema_sanitizer.py::test_gemini_live_schema` antes da correção para registrar a falha atual como baseline. **Pulado**: `GEMINI_API_KEY` não está definido neste ambiente.

## 2. Sanitizador de schema (`gemini-schema-alignment`)

- [x] 2.1 Em `packages/shared-llm/gemini_client.py`, ajustar `_sanitize()` para remover, dentro de qualquer combinador (`anyOf`, `oneOf`, `allOf`), branches cujo único conteúdo pós-sanitização seja `required` (sem `type`, `properties`, `items`, `enum` ou `format`). (`oneOf`/`allOf` já eram inteiramente filtrados por `allowed_keys` antes da mudança; a lógica nova cobre `anyOf`, o único combinador que sobrevive à sanitização.)
- [x] 2.2 Garantir que, se todos os branches de um combinador forem removidos por esse motivo, a chave do combinador seja removida do nó pai (evitando `"anyOf": []` no schema enviado).
- [x] 2.3 Confirmar que `_scan_deep` continua passando sem alterações e que nenhuma chave proibida é reintroduzida pela mudança.
- [x] 2.4 Adicionar casos novos em `tests/test_gemini_schema_sanitizer.py` cobrindo: branch `anyOf` somente com `required` é removido; combinador misto (um branch tipado, um `required`-only) preserva o branch tipado e remove o outro; schema real de `extr-peticao-processo` sanitizado não contém mais `anyOf` `required`-only no nó raiz.
- [x] 2.5 Não alterar `platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json` nem qualquer outro schema canônico.

## 3. Validação local ainda aplica a restrição removida (`gemini-schema-alignment`)

- [x] 3.1 Adicionar um teste (mock ou usando `_validate_offline`/`local_resolver.load_validator` diretamente) que confirma: uma resposta que viola o `anyOf` original ("ao menos um destes campos") ainda falha na validação local contra o schema rico completo, mesmo com o combinador removido do schema enviado ao Gemini.

## 4. Avaliação de risco de truncamento (`gemini-fallback-escalation`)

- [x] 4.1 Em `generate_structured`, após a falha da chamada estruturada inicial e antes do fallback livre, implementar a avaliação de risco descrita no design (tamanho do Markdown de entrada + `top_properties_count` já calculado).
- [x] 4.2 Definir os limiares iniciais reaproveitando os valores empíricos já usados no código (ex.: o limiar de 12000 caracteres hoje usado em `is_truncated`), como constantes nomeadas e comentadas no módulo. (`_FALLBACK_MARKDOWN_CHARS_RISK_THRESHOLD = 12000`, `_FALLBACK_TOP_PROPERTIES_RISK_THRESHOLD = 15`.)
- [x] 4.3 Quando o risco for alto, pular a chamada de fallback livre inicial e o retry de reparo, chamando `_execute_extraction_in_blocks` diretamente, com log explicando a decisão.
- [x] 4.4 Quando o risco for baixo, preservar exatamente o fluxo atual (fallback livre → retry de reparo → blocos apenas se necessário).
- [x] 4.5 Adicionar casos novos em `tests/test_gemini_schema_sanitizer.py` (ou um novo arquivo de teste dedicado, se mais claro) cobrindo: entrada pequena mantém o caminho de fallback livre existente; entrada grande escala diretamente para blocos sem chamar o fallback livre; a decisão é determinística entre execuções com a mesma entrada.
  - Nota: o teste `test_gemini_fallback_logic_and_blocks` existente usava o schema completo real (25 propriedades, alto risco) para exercitar a esteira de fallback livre; como esse caso agora escala direto para blocos, o teste foi ajustado para refletir o novo comportamento (a cobertura da detecção de truncamento do fallback livre passou para `test_gemini_fallback_low_risk_uses_free_form_path`, com um schema pequeno).

## 5. Validação end-to-end

- [x] 5.1 Rodar a suíte completa de `tests/test_gemini_schema_sanitizer.py` e `apps/data-processing/tests/test_local_schema_reference_resolution.py`. **Resultado**: 22 passed, 1 skipped (o skip é `test_gemini_live_schema`, condicionado a `GEMINI_API_KEY`).
- [x] 5.2 Se `GEMINI_API_KEY` estiver disponível, rodar novamente `tests/test_gemini_schema_sanitizer.py::test_gemini_live_schema` e confirmar que a chamada estruturada inicial não falha mais com `400 INVALID_ARGUMENT` para o schema de `extr-peticao-processo`. **Executado operacionalmente pelo usuário fora deste ambiente** (sem `GEMINI_API_KEY` aqui): confirmou que a Decisão 1 sozinha NÃO eliminou o `400` — motivou a Decisão 3 (preflight, seção 6 abaixo). `pytest::test_gemini_live_schema` continua sem rodar neste sandbox (sem `GEMINI_API_KEY`), mas o critério operacional (sem `400` nos logs) passou a ser garantido estruturalmente pelo preflight, verificável sem a API real (ver 6.5).
- [x] 5.3 Revisar os artefatos gerados em `var/artifacts/gemini-debug/` após uma execução real, confirmando que `structured_call_error.txt` deixa de ser gerado para esse caso (ou, se ainda houver erro, que ele é de natureza diferente da já corrigida). **Resultado da rodada 2**: com o preflight (seção 6), `structured_call_error.txt` não é mais gerado para o schema completo, porque a chamada estruturada correspondente nunca é tentada — coberto por teste (`test_gemini_preflight_incompatible_schema_never_attempts_structured_or_free_form_call`).

## 6. Preflight de compatibilidade com response_schema (`gemini-response-schema-preflight`)

**Motivação**: o teste operacional real (fora deste sandbox) confirmou que, mesmo após a correção do `anyOf` (seção 2), a chamada estruturada inicial para o schema completo de `extr-peticao-processo` continuou falhando com `400 INVALID_ARGUMENT`, indicando uma causa residual não identificada com certeza. Em vez de continuar corrigindo construções específicas de forma reativa sem acesso à API para validar cada hipótese, esta seção adiciona uma decisão de preflight determinística que evita a chamada previsivelmente incompatível por completo.

- [x] 6.1 Medir empiricamente o tamanho em bytes, a quantidade de propriedades top-level e a quantidade de nós do schema sanitizado completo vs. dos nove schemas por bloco de `_execute_extraction_in_blocks`, para calibrar limiares com margem entre os dois grupos.
- [x] 6.2 Implementar `GeminiLLMClient._assess_response_schema_compatibility` (método estático) em `packages/shared-llm/gemini_client.py`, avaliando os três sinais medidos contra as novas constantes `_SCHEMA_PREFLIGHT_SIZE_BYTES_THRESHOLD`, `_SCHEMA_PREFLIGHT_TOP_PROPERTIES_THRESHOLD` e `_SCHEMA_PREFLIGHT_NODE_COUNT_THRESHOLD`.
- [x] 6.3 Em `generate_structured`, chamar o preflight antes de qualquer chamada ao Gemini (antes da chamada estruturada inicial). Quando incompatível, chamar `_execute_extraction_in_blocks` diretamente, sem tentar a chamada estruturada nem o fallback livre.
- [x] 6.4 Logar explicitamente que a decisão foi tomada em preflight (por complexidade do schema), e não por erro da API; confirmar que `structured_call_error.txt` não é criado nesse caminho (nenhuma chamada foi tentada).
- [x] 6.5 Não alterar nenhum schema canônico, nem o provider (Gemini) nem o modelo configurado — a decisão opera inteiramente sobre o schema sanitizado e o cliente já existentes.
- [x] 6.6 Preservar a validação local do resultado final contra o schema rico completo, também para extrações escaladas por preflight (não apenas para escaladas reativas).
- [x] 6.7 Adicionar testes cobrindo: schema pequeno é considerado compatível (`test_assess_response_schema_compatibility_small_schema_is_compatible`); schema completo real é considerado incompatível com o motivo explicando o sinal excedido (`test_assess_response_schema_compatibility_real_full_schema_is_incompatible`); schema incompatível nunca gera uma chamada com o schema completo, e nenhum arquivo de erro é criado (`test_gemini_preflight_incompatible_schema_never_attempts_structured_or_free_form_call`); resultado do modo por blocos acionado por preflight continua validável contra o schema rico completo (`test_gemini_block_mode_result_validates_against_full_local_schema`).
- [x] 6.8 Ajustar os testes existentes que assumiam a chamada estruturada inicial sendo tentada (e falhando) para o schema completo (`test_gemini_fallback_logic_and_blocks`, `test_gemini_fallback_escalation_is_deterministic_across_runs`), já que essa chamada agora nunca é tentada para esse schema.
- [x] 6.9 Rodar a suíte completa novamente (`tests/test_gemini_schema_sanitizer.py`, `apps/data-processing/tests/`), `ruff check`, `git diff --check` e `openspec validate --all --strict`.
