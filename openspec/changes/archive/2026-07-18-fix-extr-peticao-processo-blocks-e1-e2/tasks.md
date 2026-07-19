## 1. Diagnóstico confirmatório

- [x] 1.1 Instrumentar `generate_structured` para persistir em disco (debug dir) a mensagem completa do erro 400 `INVALID_ARGUMENT` da chamada estruturada inicial (schema completo), reproduzir com `Petição Inicial_evento_1.md` e confirmar se a causa é a falta de sanitização recursiva de `anyOf` ou outra construção do schema.
- [x] 1.2 Confirmar via `finish_reason`/uso de tokens logado que a truncagem de E1/E2 é causada por consumo do orçamento de `max_output_tokens` por tokens de "thinking" do `gemini-3-flash-preview` (não por outro erro).

## 2. Correção da sanitização de schema (`gemini-schema-alignment`)

- [x] 2.1 Corrigir `GeminiLLMClient._normalize_schema._sanitize` (`packages/shared-llm/gemini_client.py`) para recursar nos subschemas de `anyOf`, aplicando o mesmo filtro de `allowed_keys` usado em `properties`/`items`.
- [x] 2.2 Validar que o schema sanitizado de `peticao_processo.schema.json` não perde chaves preservadas hoje (`additionalProperties`, `format`, `minItems`, `maxItems`, `minimum`, `maximum`, tipos nullable) — rodar `platform/skills/extr-peticao-processo/scripts/test_schema_validation.py`.
- [x] 2.3 Rodar a extração real de `Petição Inicial_evento_1.md` e confirmar se a chamada estruturada inicial (schema completo) deixa de falhar com 400, ou se o fallback ainda é necessário mas agora sem o vazamento de chaves.

## 3. Orçamento de tokens/thinking para blocos E1/E2

- [x] 3.1 Definir `thinking_config` explícito (orçamento de raciocínio limitado) nas chamadas Gemini usadas por `generate_structured`/`_execute_extraction_in_blocks`, aplicado de forma que não reduza o orçamento hoje usado por `extr-contestacao-processo`/`extr-decisao-processo`.
- [x] 3.2 Corrigir o no-op em `tokens_to_use = 8192 if block_name in ("E1", "E2") else max_tokens` (linha ~397) para efetivamente aumentar o teto de saída visível dos blocos E1/E2 além do default, já que hoje o valor é idêntico ao default e não representa reforço real.
- [x] 3.3 Reexecutar a extração de `Petição Inicial_evento_1.md` e confirmar que as respostas brutas de E1 e E2 não são mais truncadas (sem `Unterminated string`/`Expecting ',' delimiter` por corte de token).

## 4. Generalização da localização de pedidos/tutela

- [x] 4.1 Implementar localização por marcador estrutural (cabeçalho tipo "DOS PEDIDOS"/"DO PEDIDO"/"DOS REQUERIMENTOS") no Markdown para o recorte de conteúdo dos blocos `E1`-`E4`, substituindo `target_pages = [13, 14, 15]` fixo.
- [x] 4.2 Garantir fallback para o documento completo quando o marcador estrutural não for encontrado.
- [x] 4.3 Remover do prompt de `E1`/`E2`/`E3` as instruções "MINIMUM MANDATORY ITEMS" que citam nomes de partes e número de processo de um caso real específico, substituindo por instruções genéricas de granularidade e formato.
- [x] 4.4 Corrigir `_apply_deterministic_fallback_e1_e2` para retornar lista vazia (não texto de caso real hardcoded) quando nenhuma linha correspondente for encontrada no Markdown.

## 5. Testes

- [x] 5.1 Criar teste (fixture baseada em `Petição Inicial_evento_1.md` ou equivalente anonimizado) que roda a extração completa de `extr-peticao-processo` e garante ausência de `_failed_blocks` (ou lista vazia).
- [x] 5.2 No mesmo teste, validar presença mínima de: `document_type`, `peticao_identification`, `process_number`, `parties`, `representations`, `valor_da_causa`, `fatos`, `fundamentos_legais`, `teses_juridicas`, `pedidos`, `tutela_urgencia`.
- [x] 5.3 Validar que o JSON final continua conforme `assets/peticao_processo.schema.json` (reutilizar/estender `scripts/validate_output.py`).
- [x] 5.4 Validar que os anchors (`kind`, `page_marker`, `quote`) são preservados nos itens extraídos de `pedidos`/`pedidos_individualizados`.
- [x] 5.5 Rodar testes focados de `extr-peticao-processo` (`platform/skills/extr-peticao-processo/scripts/test_schema_validation.py` e o novo teste do item 5.1).
- [x] 5.6 Rodar testes existentes relacionados a `extr-contestacao-processo` e `extr-decisao-processo` (sem alterá-los) como checagem de regressão do caminho compartilhado de `gemini_client.py`.

## 6. Validação final

- [x] 6.1 Rodar `openspec validate --all --strict` e corrigir eventuais problemas de formatação das specs.
- [x] 6.2 Confirmar manualmente que o JSON gerado para `Petição Inicial_evento_1.md` não contém `_failed_blocks` e reúne todos os campos mínimos exigidos.
