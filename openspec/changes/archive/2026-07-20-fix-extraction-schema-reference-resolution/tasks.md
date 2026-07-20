## 1. Módulo central de resolução local de schema

- [x] 1.1 Criar `packages/shared-schemas/local_resolver.py` com `build_local_registry(shared_schemas_dir: Path) -> referencing.Registry`, que varre `packages/shared-schemas/**/*.schema.json` e registra cada recurso pelo seu `$id` real (não por convenção de nome de arquivo).
- [x] 1.2 Implementar `load_validator(schema: dict, schema_path: Path, shared_schemas_dir: Path) -> jsonschema.Draft202012Validator`, que resolve `$ref` relativo primeiro contra o diretório de `schema_path` e, se o arquivo não existir ali, contra `shared_schemas_dir`.
- [x] 1.3 Definir exceção `SchemaReferenceError(ValueError)` levantada quando um `$ref` não é resolvível nem localmente nem no diretório compartilhado, com mensagem incluindo a URI/caminho não resolvido.
- [x] 1.4 Garantir que nenhuma chamada de rede seja possível: não configurar `retrieve` no `Registry` e não deixar cair no comportamento padrão de retrieval remoto do `referencing`.

## 2. Integração na validação pré-persistência (`extractor.py`)

- [x] 2.1 Em `apps/data-processing/src/data_processing/extractor.py`, substituir `validators.validator_for(schema_json)(schema_json)` (linhas atuais sem resolver) pela chamada a `load_validator(...)` do módulo central, usando o diretório de `schema_path` (o `schema_ref` retornado pelo dispatcher) como base.
- [x] 2.2 Importar `local_resolver` seguindo o padrão dual já usado para `client.py`/`gemini_client.py` (import relativo com fallback para `load_module_from_path`), preservando compatibilidade com a forma atual de execução do módulo. — `packages/shared-schemas` não é um pacote Python importável (nome com hífen, sem `__init__.py`), então aplicado o mesmo padrão já usado para `client_mod`/`dispatcher_mod`: `load_module_from_path` puro, sem tentativa de import relativo.
- [x] 2.3 Propagar `SchemaReferenceError` como falha controlada: logar via `self.log(...)` e não persistir/substituir o arquivo de resultado, seguindo o mesmo tratamento já existente para `ValidationError`.

## 3. Migração de `gemini_client.py` para a resolução central

- [x] 3.1 Substituir a montagem manual de `store` + `RefResolver` em `_validate_offline` (dentro de `generate_structured`) por uma chamada a `load_validator(...)` do módulo central.
- [x] 3.2 Substituir a montagem equivalente dentro de `_execute_extraction_in_blocks` (validação de `partial_schema`) pela mesma função central.
- [x] 3.3 Substituir a montagem equivalente do validador final (`resolver_final`/`validator_final`) pela mesma função central.
- [x] 3.4 Confirmar que `_normalize_schema` (inlining de `$defs` para montar o `response_schema` enviado à API Gemini) permanece inalterado — não é validação de resposta, fica fora do escopo desta change.

## 4. Testes focados da nova implementação

- [x] 4.1 Testar que um schema principal com `$ref` relativo (`defs/common.schema.json#/$defs/NonEmptyString`) é resolvido localmente via `load_validator`.
- [x] 4.2 Testar que `$ref` absoluto (`https://juridico-cli.local/schemas/defs/common.schema.json#/$defs/NonEmptyString`) é mapeado para o mesmo arquivo local, com resultado de validação equivalente ao `$ref` relativo.
- [x] 4.3 Testar (via monkeypatch/mocking de qualquer transporte de rede, ou execução em ambiente sem rede simulado) que a validação com `$ref` compartilhado não realiza nenhuma tentativa de acesso à rede.
- [x] 4.4 Testar que uma referência inexistente (arquivo ou fragmento ausente) levanta `SchemaReferenceError` com mensagem identificando a referência, sem exceção de rede/timeout.
- [x] 4.5 Testar, usando um schema real `extr-*` com `$ref` para `defs/common.schema.json` (ex.: `extr-peticao-processo`), que uma resposta válida do LLM (fake) é persistida com sucesso em `DataExtractorApp.run_extraction`.
- [x] 4.6 Testar que uma resposta inválida para esse mesmo schema real não é persistida (mantendo o comportamento já coberto por `test_invalid_response_is_not_persisted_or_allowed_to_replace_previous_result`, agora também com `$ref` compartilhado no schema em uso).
- [x] 4.7 Rodar `apps/data-processing/tests/test_safe_normalized_extraction_dispatch.py` completo e confirmar que todos os testes existentes continuam passando sem modificação de suas asserções.

## 5. Validação final

- [x] 5.1 Rodar `uv run pytest -q apps/data-processing/tests`. — 127 passed.
- [x] 5.2 Rodar `uv run ruff check apps platform packages tests`. — All checks passed.
- [x] 5.3 Rodar `git diff --check`. — sem problemas de whitespace/conflito.
- [x] 5.4 Rodar `openspec validate --all --strict`. — 27 passed, 0 failed.
- [x] 5.5 Confirmar que nenhum `*.schema.json` foi alterado (`git diff --stat -- '*.schema.json'` vazio) e que nenhum commit/push foi realizado. — confirmado.
