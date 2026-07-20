## Why

O teste operacional da esteira `Markdown normalizado → extr-peticao-processo → Gemini → validação local do JSON` avançou além da referência externa já corrigida (`local-schema-reference-resolution`), mas falhou com `Referência de schema não resolvível localmente: '#/$defs/PeticaoIdentification'`. A causa raiz: `packages/shared-llm/gemini_client.py` chama `load_validator(schema, shared_schemas_dir, shared_schemas_dir)` — passando o diretório de schemas compartilhados no lugar do caminho real do schema. `build_local_registry` só registra recursos lidos do disco a partir desse diretório; como o schema de `extr-peticao-processo` não mora em `packages/shared-schemas/`, seu próprio documento (e o `$id` usado como `base_uri`) nunca entra no registry, e qualquer `$ref` interno (`#/$defs/...`) fica órfão. Isso bloqueia toda validação offline no caminho de fallback/blocos do Gemini, que é onde a maior parte das extrações reais passa.

## What Changes

- Corrigir `packages/shared-schemas/local_resolver.py` para registrar o próprio documento de schema recebido em memória (o argumento `schema`) sob seu `base_uri` efetivo, além dos arquivos lidos do disco — assim a resolução de `#/$defs/...` funciona independentemente de o `schema_path` informado apontar para o diretório correto do schema.
- Garantir que a resolução de JSON Pointer cubra corretamente segmentos escapados (`~0`, `~1`) e cadeias de referência (schema raiz → arquivo externo → fragmento interno).
- Adicionar cobertura de teste para o cenário exato que causou a falha (chamada com `schema_path` = diretório de schemas compartilhados, como faz `gemini_client.py`), para fragmentos internos em schema externo, para cadeias de referência, e para segmentos JSON Pointer escapados.
- Nenhuma mudança de comportamento para os chamadores existentes (`gemini_client.py`, `DataExtractorApp`): mesmas assinaturas, mesmos contratos de erro.

## Capabilities

### New Capabilities
(nenhuma)

### Modified Capabilities
- `local-schema-reference-resolution`: o resolvedor local passa a preservar o schema raiz (documento em memória) como recurso resolvível no registry, cobrindo resolução de `#/$defs/...` mesmo quando o `schema_path` informado pelo chamador não é o diretório real do schema; e passa a cobrir explicitamente JSON Pointer com segmentos escapados e cadeias de referência entre schemas locais.

## Impact

- Código afetado: `packages/shared-schemas/local_resolver.py` (fix central), sem alteração de assinatura pública.
- Chamadores preservados sem alteração de contrato: `packages/shared-llm/gemini_client.py` (`_validate_offline`, `_execute_extraction_in_blocks`), `apps/data-processing/src/data_processing/extractor.py` (`DataExtractorApp.run_extraction`).
- Testes afetados: `apps/data-processing/tests/test_local_schema_reference_resolution.py` (novos casos), `apps/data-processing/tests/test_safe_normalized_extraction_dispatch.py` (deve continuar passando sem alteração).
- Nenhum arquivo `*.schema.json` é alterado.
