## Why

`GeminiLLMClient._execute_extraction_in_blocks` (`packages/shared-llm/gemini_client.py:465`) implementa hoje uma única estratégia de Extração por Blocos (blocos `A`–`E5`, prompts, corte de conteúdo e fallback determinístico `_apply_deterministic_fallback_e1_e2`) inteiramente acoplada ao formato de `extr-peticao-processo`. Ela é chamada incondicionalmente por `generate_structured` (preflight incompatível ou erro de chamada estruturada/fallback livre) para **qualquer** skill, sem considerar `bundle_id` ou `schema_ref`. No teste operacional real de `extr-contestacao-processo`, isso produziu um JSON com campos de petição inicial (`peticao_identification`, `valor_da_causa`, `fatos`, `pedidos`, etc.), rejeitado pela validação final (`unevaluatedProperties: false` do schema de contestação). Nenhum JSON foi persistido — a proteção pós-extração funcionou — mas a extração de contestação por blocos está de fato inoperante, e qualquer outra skill que caia em blocos (decisão, procuração, etc.) sofrerá o mesmo problema. Adicionalmente, foi observado `page_marker: "[]"` em âncoras do relatório de validação, indicando que a consolidação/fallback pode corromper o marcador de página em vez de preservar uma referência válida.

## What Changes

- Extrair a lógica atual de blocos (`A`–`E5`, prompts, corte por seção de pedidos, fallback determinístico E1/E2) para uma `PeticaoBlockStrategy` isolada, sem alterar seu comportamento funcional já validado.
- Introduzir um mecanismo explícito de seleção de estratégia (`BLOCK_STRATEGIES` ou equivalente) chaveado por `bundle_id`/`schema_ref`, thread­ando `bundle_id` desde `DataExtractorApp.run_extraction` (`apps/data-processing/src/data_processing/extractor.py`) através de `generate_structured(..., bundle_id=...)` até o ponto de decisão de blocos.
- Implementar `ContestacaoBlockStrategy`, com blocos derivados das propriedades reais de `platform/skills/extr-contestacao-processo/assets/contestacao_processo.schema.json` (`process_number`, `parties`, `representations`, `contestacao_identification`, `preliminares`, `merito`, `provas_e_requerimentos`, `pedidos_finais`, `anchors`) e das regras de `SKILL.md`, sem reutilizar nenhum campo exclusivo de petição inicial.
- Fazer a seleção de estratégia falhar de forma controlada (exceção específica, sem chamar `PeticaoBlockStrategy` como fallback genérico e sem persistir JSON) quando o `bundle_id` não tiver estratégia de blocos registrada.
- Garantir que a validação final de cada estratégia (contra o schema completo da skill) ocorra antes de qualquer retorno, preservando a regra de "nenhum JSON inválido é persistido".
- Adicionar sanitização/verificação do `page_marker` de âncoras na consolidação (compartilhada entre estratégias) para que ele nunca seja um valor vazio ou inválido como `"[]"`.
- **BREAKING** (interno, não de API pública): a assinatura de `GeminiLLMClient.generate_structured` passa a aceitar `bundle_id` opcional; chamadores que dependem de blocos para skills sem estratégia registrada passam a receber uma exceção controlada em vez de um resultado incorreto silencioso.

## Capabilities

### New Capabilities
- `block-extraction-strategy-selection`: mecanismo de seleção de estratégia de Extração por Blocos por `bundle_id`/`schema_ref`, com falha controlada para skills sem estratégia registrada e sanitização de `page_marker` na consolidação.
- `contestacao-block-extraction`: estratégia de blocos específica para `extr-contestacao-processo`, produzindo somente propriedades permitidas pelo `contestacao_processo.schema.json`.

### Modified Capabilities
- `peticao-block-fallback-robustness`: o comportamento existente (blocos `A`–`E5`, localização estrutural da seção de pedidos, fallback determinístico E1/E2, ausência de conteúdo hardcoded de caso real) passa a ser exposto como `PeticaoBlockStrategy`, selecionada explicitamente por `bundle_id`, em vez de ser o caminho incondicional de `_execute_extraction_in_blocks`. Nenhum requisito de comportamento observável muda para `extr-peticao-processo`.

## Impact

- **Código afetado**: `packages/shared-llm/gemini_client.py` (refatoração de `_execute_extraction_in_blocks` em estratégias); `apps/data-processing/src/data_processing/extractor.py` (passagem de `bundle_id` para `generate_structured`).
- **Não afetado / preservado**: preflight de compatibilidade (`_assess_response_schema_compatibility`), provider/modelo Gemini, schemas canônicos (`*.schema.json`), resolução local de `$ref` (`packages/shared-schemas/local_resolver.py`), roteamento de extratores registrados.
- **Testes**: `tests/test_gemini_schema_sanitizer.py` (cobertura existente de blocos de petição, deve continuar passando) ganha casos novos para seleção de estratégia, contestação e skill sem estratégia; validação determinística via `platform/skills/extr-contestacao-processo/scripts/validate_output.py`.
- **Escopo explícito**: apenas `extr-peticao-processo` e `extr-contestacao-processo` recebem estratégia implementada nesta etapa; demais extratores (`extr-decisao-processo`, `extr-procuracao`, `extr-mandato-processo`, `extr-cabecalho-processo`, etc.) recebem falha controlada, não estratégia de petição.
