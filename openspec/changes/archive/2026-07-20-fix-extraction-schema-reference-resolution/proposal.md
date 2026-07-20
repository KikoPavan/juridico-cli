## Why

A validação pós-extração falha em produção mesmo quando o LLM retorna um payload correto: `apps/data-processing/src/data_processing/extractor.py` instancia o validador `jsonschema` sem nenhum resolvedor local, então qualquer `$ref` relativo (`defs/common.schema.json#/$defs/...`) é resolvido contra o `$id` do schema (`https://juridico-cli.local/...`) e o `jsonschema`/`referencing` tenta buscá-lo pela rede, produzindo `Unresolvable: defs/common.schema.json#/$defs/NonEmptyString`. Isso bloqueia a persistência de extrações válidas na nova esteira (`extr-peticao-processo` e demais skills que reutilizam `defs/common.schema.json`).

Uma resolução local equivalente já existe, mas duplicada e não centralizada: `platform/skills/extr-processo/scripts/validate_output.py` usa `referencing.Registry`, e `packages/shared-llm/gemini_client.py` reimplementa o mesmo mapeamento três vezes com `jsonschema.RefResolver` (deprecado) apenas para validações internas/fallback — nenhuma das duas é usada pela validação final que decide se o resultado é persistido.

## What Changes

- Criar um módulo centralizado de resolução local de `$ref` de schema (mapeando tanto refs relativos quanto URIs `https://juridico-cli.local/schemas/...` para os arquivos reais em `packages/shared-schemas/`), sem qualquer acesso à rede.
- Fazer a validação pré-persistência em `apps/data-processing/src/data_processing/extractor.py` usar esse módulo centralizado em vez de um `Draft*Validator` sem resolvedor.
- Migrar as três implementações duplicadas de resolução local em `packages/shared-llm/gemini_client.py` para usar o mesmo módulo centralizado, preservando seu comportamento atual (validação offline/fallback por blocos).
- Referência ausente ou não resolvível localmente MUST produzir uma falha controlada (exceção com mensagem clara), nunca uma tentativa de acesso remoto nem uma persistência de resultado inválido.
- Nenhuma alteração em schemas, prompts, provider ou modelo Gemini.

## Capabilities

### New Capabilities
- `local-schema-reference-resolution`: resolução centralizada e exclusivamente local de `$ref` de JSON Schema (relativos e via `$id` `https://juridico-cli.local/...`), usada por qualquer validação de schema do pipeline, sem acesso à rede e com falha controlada para referências ausentes.

### Modified Capabilities
- `safe-normalized-extraction-dispatch`: o requirement "Resposta do LLM é validada pelo schema da skill" passa a exigir que essa validação resolva `$ref` compartilhados localmente (sem rede) antes de decidir se persiste o resultado.

## Impact

- Código: `apps/data-processing/src/data_processing/extractor.py` (validação final), `packages/shared-llm/gemini_client.py` (três resolvedores duplicados), novo módulo compartilhado em `packages/shared-schemas/`.
- Testes: `apps/data-processing/tests/test_safe_normalized_extraction_dispatch.py` (deve continuar passando), novos testes focados na resolução local de referências.
- Sem impacto em schemas (`platform/skills/extr-*/assets/*.schema.json`, `packages/shared-schemas/defs/common.schema.json`), prompts, provider ou modelo Gemini.
