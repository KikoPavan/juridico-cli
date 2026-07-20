## 1. Fix no resolvedor local

- [x] 1.1 Em `packages/shared-schemas/local_resolver.py`, na função `load_validator`, registrar o documento de schema recebido em memória (`effective_schema`) como recurso do `registry` sob seu `base_uri` efetivo (via `registry.with_resource(base_uri, ...)`), aplicado **depois** de combinar os registries de disco (`schema_dir` e `shared_schemas_dir`), para que ele sempre prevaleça sobre qualquer versão lida do disco com o mesmo `$id`.
- [x] 1.2 Garantir que `_ensure_refs_resolvable` e a validação real (`validator_class(...)`) usem esse mesmo registry atualizado, preservando o comportamento existente para `$ref` relativos (`defs/common.schema.json#/...`) e por URI (`https://juridico-cli.local/...`).
- [x] 1.3 Confirmar que nenhuma chamada de rede é introduzida (nenhum `retrieve` configurado) e que `SchemaReferenceError` continua sendo levantado com mensagem legível para referência ou fragmento inexistente.
- [x] 1.4 Não alterar nenhum arquivo `*.schema.json`, não remover `$defs`, não expandir schemas manualmente, não alterar assinatura pública de `load_validator`/`build_local_registry`/`SchemaReferenceError`.

## 2. Testes de regressão e cobertura nova

- [x] 2.1 Em `apps/data-processing/tests/test_local_schema_reference_resolution.py`, adicionar teste que resolve `#/$defs/PeticaoIdentification` no próprio schema raiz de `extr-peticao-processo` com `schema_path` correto.
- [x] 2.2 Adicionar teste que reproduz o padrão de chamada de `gemini_client.py` (`load_validator(schema, shared_schemas_dir, shared_schemas_dir)`, ou seja, `schema_path` = diretório de schemas compartilhados, não o diretório real do schema) e confirma que `#/$defs/PeticaoIdentification` (e outra ref interna, ex. `#/$defs/AnchoredString`) resolve sem `SchemaReferenceError`.
- [x] 2.3 Adicionar teste para resolução de fragmento interno em schema externo carregado por `$ref` (schema local que referencia um arquivo externo cujo conteúdo tem sua própria referência interna).
- [x] 2.4 Adicionar teste para a cadeia completa: schema raiz → arquivo externo → fragmento interno.
- [x] 2.5 Adicionar teste de JSON Pointer com segmentos escapados (`~0`, `~1`) resolvendo para a chave correta em `$defs`.
- [x] 2.6 Adicionar teste confirmando que fragmento inexistente (ex.: `#/$defs/NaoExiste`) falha com `SchemaReferenceError` controlado, sem acesso à rede (reaproveitar padrão de bloqueio de socket já usado em `test_validation_never_touches_the_network`).
- [x] 2.7 Adicionar teste com estrutura de schema equivalente ao schema real de `extr-peticao-processo` (múltiplos `$defs`, `$ref` interno e `$ref` relativo para `defs/common.schema.json` combinados), cobrindo o requisito de teste 8 da proposta.
- [x] 2.8 Confirmar que os testes pré-existentes em `test_local_schema_reference_resolution.py` continuam passando sem modificação de comportamento esperado.
- [x] 2.9 Confirmar que `apps/data-processing/tests/test_safe_normalized_extraction_dispatch.py` (teste de despacho seguro) continua passando sem alteração.

## 3. Validação final

- [x] 3.1 Rodar `uv run pytest -q apps/data-processing/tests` e confirmar sucesso total.
- [x] 3.2 Rodar `uv run ruff check apps platform packages tests` e confirmar sem violações novas.
- [x] 3.3 Rodar `git diff --check` e confirmar ausência de conflitos de whitespace.
- [x] 3.4 Rodar `openspec validate --all --strict` e confirmar sucesso.
- [x] 3.5 Apresentar ao final: lista de arquivos modificados, lista de testes executados, e saída de `git status -sb`. Não commitar nem dar push.
