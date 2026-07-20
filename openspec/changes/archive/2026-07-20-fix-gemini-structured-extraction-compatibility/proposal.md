## Why

A extração `extr-peticao-processo` está falhando de forma reprodutível com `400 INVALID_ARGUMENT` na primeira chamada estruturada ao Gemini (evidência real em `var/artifacts/gemini-debug/`, execução de 2026-07-20 para o processo `4000153-37.2026.8.26.0136/SP`). A causa raiz identificada é que o sanitizador de schema (`GeminiLLMClient._normalize_schema` / `_sanitize`, em `packages/shared-llm/gemini_client.py`) produz branches de `anyOf` compostos apenas por `{"required": [...]}`, sem a chave `type` — isso reflete o idioma "ao menos um destes campos" do schema canônico (`platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json:149-156`), mas o modo de saída estruturada do Gemini rejeita nós de schema sem `type`. Todos os demais usos de `anyOf` no projeto (em `packages/shared-schemas/defs/common.schema.json`) já declaram `type` em cada branch, então esse é um caso isolado não coberto pela sanitização atual.

Como consequência direta desse erro, toda extração cai no fallback "livre" (schema embutido no prompt, sem `response_schema`), que é uma tentativa extensa e propensa a truncamento para documentos grandes — os artefatos de debug mostram `JSONDecodeError: Unterminated string` nesse caminho. Hoje o sistema só escala para a extração por blocos depois de duas tentativas livres mal-sucedidas (chamada inicial + retry de reparo), o que é lento e reativo. Corrigir a causa raiz do 400 e tornar a escalada para blocos mais rápida e previsível quando há risco de truncamento reduz falhas e latência sem alterar o schema canônico da skill.

**Atualização (rodada 2, mesmo dia)**: a correção da sanitização (remover branches `anyOf` só com `required`) foi validada por teste unitário, mas o teste operacional real com `extr-peticao-processo` continuou reproduzindo `400 INVALID_ARGUMENT` na chamada estruturada inicial — ou seja, o schema completo real tem complexidade/incompatibilidade adicional com `response_schema` além do `anyOf` já corrigido, ainda não identificada com certeza (sem acesso à API para depurar interativamente). Em vez de perseguir cada construção incompatível uma a uma de forma reativa, a mudança passa a incluir uma decisão de **preflight determinística**: antes de qualquer chamada ao Gemini, avaliar a complexidade estrutural do schema sanitizado (tamanho, quantidade de propriedades top-level, quantidade de nós) e, se exceder limiares calibrados a partir da diferença real medida entre o schema completo (conhecido por falhar) e os schemas por bloco (conhecidos por funcionar operacionalmente), pular a chamada estruturada e o fallback livre e ir direto para a extração por blocos — eliminando o `400` de forma determinística, sem depender de identificar a causa exata.

## What Changes

- Corrigir `_sanitize` em `packages/shared-llm/gemini_client.py` para remover, de qualquer combinador (`anyOf`/`oneOf`/`allOf`), branches compostos somente por `required` (sem `type`, `properties`, `items`, `enum` ou `format`) — sem alterar o schema canônico em `platform/skills/extr-peticao-processo/assets/`. A restrição de negócio continua sendo aplicada pela validação local pós-geração contra o schema rico completo.
- Adicionar um preflight de compatibilidade com `response_schema` em `generate_structured`, executado sobre o schema sanitizado **antes de qualquer chamada ao Gemini** (nem a chamada estruturada, nem o fallback livre): quando o schema excede os limiares de complexidade calibrados empiricamente, pular ambas as chamadas e ir direto para `_execute_extraction_in_blocks`, registrando no log que a decisão foi tomada em preflight, e não por erro da API.
- Adicionar uma avaliação de risco de truncamento antes da tentativa de fallback livre em `generate_structured` (para os casos em que o preflight considera o schema compatível, mas a chamada estruturada falha por outro motivo), usando sinais já disponíveis (tamanho do conteúdo de entrada, quantidade de campos obrigatórios no schema solicitado) para decidir se a tentativa livre extensa deve ser pulada.
- Preservar o comportamento atual (chamada estruturada → fallback livre com retry → blocos) para os casos em que o schema é compatível e o risco de truncamento é baixo, para não alterar o caminho já validado por `openspec/specs/peticao-block-fallback-robustness/spec.md`.
- Não alterar o provider (Gemini) nem o modelo configurado.

## Capabilities

### New Capabilities
- `gemini-fallback-escalation`: define como `GeminiLLMClient.generate_structured` avalia risco de truncamento e decide entre a tentativa de fallback livre (com retry) e a escalada direta para extração por blocos, para schemas já considerados compatíveis pelo preflight.
- `gemini-response-schema-preflight`: define a decisão determinística de preflight que avalia se o schema sanitizado é compatível com `response_schema` antes de qualquer chamada ao Gemini, e a escalada direta para blocos quando não for.

### Modified Capabilities
- `gemini-schema-alignment`: adicionar requisito de que branches de combinadores (`anyOf`/`oneOf`/`allOf`) compostos somente por `required`, sem `type` inferível, sejam removidos durante a sanitização (em vez de receberem um `type` inventado), para que o Gemini não rejeite a chamada estruturada com `400 INVALID_ARGUMENT`.

## Impact

- Código: `packages/shared-llm/gemini_client.py` (`_normalize_schema`/`_sanitize`, `_assess_response_schema_compatibility`, `generate_structured`).
- Testes: `tests/test_gemini_schema_sanitizer.py` (casos para branches `anyOf` só com `required`; casos para a decisão de escalada de fallback; casos para o preflight de compatibilidade).
- Sem alteração em: schema canônico da skill (`platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json`), `packages/shared-schemas/local_resolver.py`, provider/modelo configurado, lógica interna de `_execute_extraction_in_blocks` já coberta por `peticao-block-fallback-robustness`.
- Artefatos de debug em `var/artifacts/gemini-debug/` continuam sendo gerados como hoje, servindo de evidência para validar a correção.
