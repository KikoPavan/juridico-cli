## 1. Plumbing de `bundle_id`

- [x] 1.1 Adicionar parâmetro nomeado opcional `bundle_id: str | None = None` a `GeminiLLMClient.generate_structured` (`packages/shared-llm/gemini_client.py:136`), preservando compatibilidade com chamadores que não o informam.
- [x] 1.2 Em `DataExtractorApp.run_extraction` (`apps/data-processing/src/data_processing/extractor.py:172`), repassar `bundle_id=bundle_id` na chamada a `client.generate_structured(...)`.
- [x] 1.3 Confirmar que `platform/skills/extr-peticao-processo/scripts/test_real_case_extraction.py` (chamador legado sem `bundle_id`) continua funcionando sem alteração. (Atualizado para repassar `bundle_id=dispatch_result["bundle_id"]`, já resolvido nesse script — necessário porque o caso real de petição aciona blocos e agora exige `bundle_id` para resolver a estratégia.)

## 2. Extração de `PeticaoBlockStrategy` (refatoração sem mudança de comportamento)

- [x] 2.1 Criar módulo `packages/shared-llm/block_strategies.py` com uma interface/protocolo comum para estratégias de blocos (método `execute(client, messages, schema, debug_dir, max_tokens, base_dir)`).
- [x] 2.2 Mover o corpo atual de `_execute_extraction_in_blocks` (`packages/shared-llm/gemini_client.py:465-831`) para `PeticaoBlockStrategy.execute(...)` em `block_strategies.py`, incluindo a definição de blocos `A`–`E5`, os prompts por bloco, o corte estrutural via `_locate_pedidos_section`/`_extract_pages_from_markdown`, e a chamada a `_apply_deterministic_fallback_e1_e2`.
- [x] 2.3 Ajustar as referências a métodos auxiliares (`_normalize_schema`, `_format_messages`, `_fix_anchors_and_properties`, `_apply_deterministic_fallback_e1_e2`, `_locate_pedidos_section`, `_extract_pages_from_markdown`, `_load_local_resolver_mod`) para que `PeticaoBlockStrategy` os acesse via a instância de `client` recebida, sem duplicar código.
- [x] 2.4 Rodar `uv run pytest -q tests/test_gemini_schema_sanitizer.py` e confirmar que todos os testes de blocos de petição existentes continuam passando sem alteração de asserts. (14 passed, 1 skipped — sem GEMINI_API_KEY. 5 call sites de teste que exercitam a escalada automática para blocos precisaram de `bundle_id="extr-peticao-processo"` explícito — plumbing necessário, nenhum assert alterado.)

## 3. Registro de estratégias e falha controlada

- [x] 3.1 Definir `BLOCK_STRATEGIES = {"extr-peticao-processo": PeticaoBlockStrategy, "extr-contestacao-processo": ContestacaoBlockStrategy}` em `packages/shared-llm/block_strategies.py`.
- [x] 3.2 Definir uma exceção específica (ex.: `BlockExtractionStrategyUnavailableError`) que carregue o `bundle_id` sem estratégia registrada. (Subclasse de `ValueError` para permanecer compatível com chamadores que já tratam `ValueError` como resultado incompatível não promovível, ex.: `stage_router.py`.)
- [x] 3.3 Implementar `GeminiLLMClient._dispatch_block_extraction(self, bundle_id, messages, schema, debug_dir, max_tokens, base_dir)` que resolve a estratégia em `BLOCK_STRATEGIES` por `bundle_id` e levanta a exceção do item 3.2 quando ausente, sem chamar `PeticaoBlockStrategy` como padrão.
- [x] 3.4 Substituir as quatro chamadas diretas a `self._execute_extraction_in_blocks(...)` em `generate_structured` (linhas 257, 323, 443/449, 460) por chamadas a `self._dispatch_block_extraction(bundle_id, ...)`. (5 call sites literais; `_execute_extraction_in_blocks` foi preservado como ponto de entrada legado que delega a `PeticaoBlockStrategy`, usado apenas por testes que o chamam diretamente por nome.)
- [x] 3.5 Confirmar que a exceção do item 3.2, quando levantada dentro de `DataExtractorApp.run_extraction`, propaga sem ser capturada antes do `json.dump` (linha 198 de `extractor.py`), garantindo que nenhum JSON é persistido. (Confirmado por teste dedicado: `apps/data-processing/tests/test_block_extraction_strategy_unavailable.py`.)

## 4. `ContestacaoBlockStrategy`

- [x] 4.1 Implementar `ContestacaoBlockStrategy` em `block_strategies.py`, com blocos derivados de `platform/skills/extr-contestacao-processo/assets/contestacao_processo.schema.json`: identificação (`process_number`, `parties`, `representations`, `contestacao_identification`), `preliminares`, `merito`, e `provas_e_requerimentos`/`pedidos_finais`.
- [x] 4.2 Escrever prompts por bloco derivados das seções 1–6 de `platform/skills/extr-contestacao-processo/SKILL.md`, sem citar nomes de partes/processos de caso real e sem mencionar campos exclusivos de petição inicial.
- [x] 4.3 Implementar fallback determinístico local de contestação (localização de cabeçalhos estruturais equivalentes a `PRELIMINAR(ES)`, `MÉRITO`/`NO MÉRITO`, `PEDIDOS FINAIS`/`DOS PEDIDOS`), retornando listas vazias quando a seção não for localizada, sem inventar conteúdo nem reutilizar defaults de petição.
- [x] 4.4 Validar o JSON consolidado da estratégia de contestação contra `contestacao_processo.schema.json` completo antes de retornar, reutilizando o padrão já existente de `validator_final.iter_errors(...)` + `raise ValueError(...)` em caso de erro.

## 5. Sanitização de `page_marker`

- [x] 5.1 Investigar primeiro se `page_marker: "[]"` é sintoma do mesmo bug de causa-raiz da seção 3: o loop de preenchimento de defaults do fallback antigo (`partial_json[f] = []` para qualquer campo do bloco hardcoded não tratado explicitamente, `packages/shared-llm/gemini_client.py:800`) aplica um default de tipo errado (lista vazia) a campos que no schema real deveriam ser objetos/âncoras — a separação em estratégias por skill (seção 3-4) já elimina essa classe de bug ao restringir cada estratégia aos seus próprios campos e tipos corretos; documentar essa conclusão antes de implementar sanitização adicional. Implementar helper compartilhado `_sanitize_anchor_page_marker(anchors, current_page_hint)` em `block_strategies.py` (ou módulo utilitário comum) apenas para os casos em que o próprio LLM retornar `page_marker` vazio, `"[]"`/`"[ ]"` ou sem dígitos dentro de uma âncora bem formada. (Confirmado via investigação: a causa-raiz principal é a mesma da seção 3 — separação em estratégias já resolve; `sanitize_anchor_page_marker` cobre o caso residual de o próprio LLM emitir um `page_marker` malformado.)
- [x] 5.2 Aplicar o helper na etapa de consolidação de blocos de `PeticaoBlockStrategy` e `ContestacaoBlockStrategy`, logando quando um valor recebido do LLM é substituído.
- [x] 5.3 Escrever teste unitário reproduzindo uma resposta de bloco com `page_marker: "[]"` e confirmando que o resultado consolidado final não contém esse valor.

## 6. Testes automatizados (fake client, sem chamadas reais ao Gemini)

- [x] 6.1 Adicionar teste confirmando que `bundle_id="extr-peticao-processo"` resolve `PeticaoBlockStrategy` e produz JSON válido (reuso/extensão dos testes existentes em `tests/test_gemini_schema_sanitizer.py`).
- [x] 6.2 Adicionar teste confirmando que `bundle_id="extr-contestacao-processo"` resolve `ContestacaoBlockStrategy` e que o resultado consolidado não contém nenhum de `peticao_identification`, `valor_da_causa`, `fatos`, `pedidos`, `pedidos_individualizados`, `tutela_urgencia`, `provas_requeridas`, `riscos_ou_pontos_de_atencao`.
- [x] 6.3 Adicionar teste confirmando que o resultado de contestação por blocos valida sem erros contra `contestacao_processo.schema.json` via `local_resolver.load_validator`.
- [x] 6.4 Adicionar teste chamando `platform/skills/extr-contestacao-processo/scripts/validate_output.py --input <resultado.json>` (via subprocess) sobre um resultado gerado pelo fake client, confirmando saída `OK`/código 0. (Bug pré-existente encontrado e corrigido nesse script: usava `jsonschema.RefResolver` cru, que seguia o `$id` do schema e tentava resolver `defs/common.schema.json` via rede — corrigido para usar `local_resolver.load_validator`, a mesma resolução local já usada pelo pipeline real.)
- [x] 6.5 Adicionar teste confirmando que `bundle_id` sem estratégia registrada (ex.: `"extr-procuracao"`) levanta a exceção controlada do item 3.2 e não invoca `PeticaoBlockStrategy`.
- [x] 6.6 Adicionar teste confirmando que, quando a exceção do item 3.2 é levantada, nenhum arquivo é escrito em `var/output/extracted/` (usando diretório temporário para `var_dir`).
- [x] 6.7 Adicionar teste confirmando que o `bundle_id` determina a estratégia (mesmo `messages`/schema básico por estratégia, `bundle_id` diferente produz conjuntos de chaves consolidadas mutuamente exclusivos entre petição e contestação).
- [x] 6.8 Confirmar que todos os testes usam um fake client injetado (sem chamada real a `genai.Client`/API do Gemini). (Único teste pré-existente que faz chamada real, `test_gemini_live_schema`, é guardado por skip condicional a `GEMINI_API_KEY` e não faz parte da suíte padrão sem a chave; foi ajustado para continuar funcionando com `bundle_id` quando executado.)

## 7. Validação de regressão e preservação de contratos existentes

- [x] 7.1 Rodar `uv run pytest -q apps/data-processing/tests` e confirmar 100% de aprovação, incluindo os testes de preflight, resolução local de schema e despacho seguro já existentes.
- [x] 7.2 Rodar `uv run pytest -q tests/test_gemini_schema_sanitizer.py` e confirmar 100% de aprovação (testes antigos e novos).
- [x] 7.3 Rodar `uv run ruff check apps platform packages tests` e corrigir quaisquer achados introduzidos por esta change. (All checks passed!)
- [x] 7.4 Rodar `git diff --check` para confirmar ausência de conflitos/whitespace inválido. (Sem saída, exit 0.)
- [x] 7.5 Rodar `openspec validate --all --strict` e corrigir quaisquer inconsistências nos specs desta change. (Totals: 30 passed, 0 failed.)
- [x] 7.6 Confirmar manualmente que nenhum arquivo `*.schema.json` foi alterado (`git diff --stat -- '*.schema.json'` vazio). (Confirmado — vazio.)

## 8. Validação operacional determinística

- [x] 8.1 Gerar um resultado de contestação via `ContestacaoBlockStrategy` usando o fake client de teste (ou, se disponível de forma segura, um caso real já existente em `var/`) e salvar em arquivo `resultado.json`. (Gerado com fake client, fora da suíte pytest, sem nenhum campo de petição.)
- [x] 8.2 Rodar `uv run python platform/skills/extr-contestacao-processo/scripts/validate_output.py --input <resultado.json>` e confirmar saída `OK` e código de saída `0`. (Confirmado: `OK ... — valid against contestacao_processo.schema.json`.)
- [x] 8.3 Documentar no relatório final: causa-raiz confirmada, estratégia implementada, arquivos modificados, resultados dos testes, `git status -sb`, e riscos restantes (incluindo cobertura de fallback determinístico de contestação e comportamento de skills ainda sem estratégia).
- [x] 8.4 Não arquivar esta change antes de um teste operacional real com uma contestação (fora da suíte automatizada) confirmar o comportamento esperado. (Confirmado pelo usuário: teste operacional real já realizado fora desta sessão.)
