## Why

A extração da petição inicial via skill `extr-peticao-processo` está sendo concluída com ressalvas nos blocos `E1` (`pedidos`) e `E2` (`pedidos_individualizados`) no caso real `Petição Inicial_evento_1.md`. A investigação dos artefatos de debug do run de 2026-07-18 (`var/artifacts/gemini-debug/block_E1_*`, `fallback_raw_response.txt`) mostra que tanto a chamada de fallback consolidada quanto a chamada de fallback do bloco E1 retornam JSON **truncado a poucas centenas de caracteres** (char ~689 e ~1107) mesmo com `max_output_tokens=8192` configurado — evidência de que o orçamento de tokens está sendo consumido antes do texto de saída ser escrito (compatível com tokens de "thinking" do modelo `gemini-3-flash-preview`, que não tem `thinking_config` configurado hoje). Além disso, a estratégia de fallback por blocos (`_execute_extraction_in_blocks`) tem páginas-alvo (13/14/15) e conteúdo mínimo obrigatório (nomes como "Banco do Brasil", número de processo `0003453-81.2003.8.26.0136`) **fixados no código e no fallback determinístico local**, tornando o mecanismo dependente de um caso específico em vez de localizar a seção "DOS PEDIDOS" de forma genérica.

Como consequência, quando o bloco falha, o fallback determinístico de última instância pode devolver texto de um caso real anterior como "valor padrão" em vez de indicar ausência de dados — o que viola a diretriz de não gerar dados padrão quando o conteúdo está presente no Markdown.

## What Changes

- Investigar e corrigir a causa da truncagem prematura das chamadas Gemini nos blocos `E1`/`E2` do fallback por blocos de `extr-peticao-processo` (orçamento de tokens/`thinking_config` do modelo `gemini-3-flash-preview`), garantindo que o JSON final não seja cortado no meio de uma string.
- Corrigir o bug de sanitização de schema em `GeminiLLMClient._normalize_schema` (`packages/shared-llm/gemini_client.py`): o passo `_sanitize` recursa em `properties` e `items`, mas **não recursa nos subschemas de `anyOf`**, deixando chaves não suportadas (ex.: `pattern`, `minLength`, `maxLength`) vazarem para o Gemini dentro de branches de `anyOf` — candidato à causa raiz do erro 400 `INVALID_ARGUMENT` na chamada estruturada inicial com `response_json_schema`.
- Generalizar a localização da seção "DOS PEDIDOS"/tutela de urgência nos blocos `E1`-`E4` de `_execute_extraction_in_blocks`, removendo a dependência de números de página fixos (13/14/15) e de conteúdo de caso específico ("Banco do Brasil", processo `0003453-81.2003.8.26.0136`) nas instruções de prompt.
- Corrigir o fallback determinístico local (`_apply_deterministic_fallback_e1_e2`) para que, na ausência de correspondência textual, **não** devolva texto fixo de um caso real anterior como valor padrão — deve refletir a ausência de dados extraídos com segurança.
- Adicionar teste com o caso real (ou fixture equivalente) `Petição Inicial_evento_1.md`, cobrindo `document_type`, `peticao_identification`, `process_number`, `parties`, `representations`, `valor_da_causa`, `fatos`, `fundamentos_legais`, `teses_juridicas`, `pedidos`, `tutela_urgencia`, garantindo ausência de ressalvas em `E1`/`E2`.

## Capabilities

### New Capabilities
- `peticao-block-fallback-robustness`: cobre o comportamento do mecanismo de fallback por blocos (`_execute_extraction_in_blocks`) usado exclusivamente por `extr-peticao-processo` — localização genérica de seções do documento, orçamento de tokens suficiente para completar blocos E1-E5 sem truncamento, e ausência de conteúdo hardcoded de caso específico no fallback determinístico.

### Modified Capabilities
- `gemini-schema-alignment`: nova exigência de que o sanitizador de schema (`_normalize_schema`/`_sanitize`) processe recursivamente os subschemas dentro de combinadores `anyOf`, com o mesmo filtro de chaves aplicado a `properties`/`items`.

## Impact

- `packages/shared-llm/gemini_client.py` — `generate_structured`, `_normalize_schema`/`_sanitize`, `_execute_extraction_in_blocks`, `_apply_deterministic_fallback_e1_e2`. Este arquivo é compartilhado por todas as skills de extração (`extr-peticao-processo`, `extr-contestacao-processo`, `extr-decisao-processo`); mudanças no caminho de sanitização de schema e no orçamento de tokens/`thinking_config` do fallback de schema único são globais e exigem checagem de regressão nas outras skills (sem alterá-las).
- `platform/skills/extr-peticao-processo/` — possivelmente `assets/peticao_processo.schema.json` (se a causa raiz do 400 estiver em uma construção específica do schema) e testes (`scripts/test_schema_validation.py` ou novo teste dedicado).
- Nenhuma mudança em `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml`, OCR, `extr-contestacao-processo` ou `extr-decisao-processo`.
