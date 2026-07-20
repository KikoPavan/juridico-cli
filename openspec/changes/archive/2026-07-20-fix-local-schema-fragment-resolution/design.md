## Context

`packages/shared-schemas/local_resolver.py` expõe `load_validator(schema, schema_path, shared_schemas_dir)`. Ele constrói um `referencing.Registry` chamando `build_local_registry(schema_dir)`, que faz `rglob("*.schema.json")` **a partir do disco** sobre o diretório informado e registra cada arquivo encontrado pelo seu `$id` e por sua URI `file://`. O `base_uri` usado para resolver `$ref` vem de `schema.get("$id")` — o próprio schema em memória passado pelo chamador.

O bug: o registry nunca registra o dicionário `schema` recebido em memória como recurso — ele só registra o que consegue ler do disco em `schema_dir`. Isso funciona por coincidência em `DataExtractorApp.run_extraction` (`apps/data-processing/src/data_processing/extractor.py:178`), porque ali `schema_path` é o caminho real do arquivo do schema, então `schema_dir` é o diretório que contém esse mesmo arquivo, e o `rglob` acaba encontrando (relendo do disco) um documento com conteúdo idêntico ao `schema` em memória.

Mas em `packages/shared-llm/gemini_client.py` (`_validate_offline` linha 155, `_execute_extraction_in_blocks` linhas 561 e 694), `load_validator` é chamado como `load_validator(schema, shared_schemas_dir, shared_schemas_dir)` — o segundo argumento é o **diretório de schemas compartilhados**, não o caminho do schema real (`platform/skills/extr-peticao-processo/assets/`). Como esse schema não mora em `packages/shared-schemas/`, `build_local_registry` nunca o lê do disco, e o `base_uri` (o `$id` do schema) nunca é registrado. Qualquer `#/$defs/...` fica sem documento-base para resolver o JSON Pointer, e cai no branch de erro genérico de `SchemaReferenceError` — exatamente o erro relatado (`'#/$defs/PeticaoIdentification'`).

Reproduzido isoladamente:
```python
load_validator(schema, PETICAO_SCHEMA_PATH, SHARED_SCHEMAS_DIR)          # OK
load_validator(schema, SHARED_SCHEMAS_DIR, SHARED_SCHEMAS_DIR)           # FAIL — mesmo padrão de gemini_client.py
```

## Goals / Non-Goals

**Goals:**
- Fazer o resolvedor local registrar o próprio documento de schema (`schema`, o dict em memória recebido por `load_validator`) sob seu `base_uri` efetivo, independentemente do que existir em disco em `schema_path`.
- Preservar resolução correta de: `#/$defs/...` internos, `$ref` relativos a arquivos (`defs/common.schema.json#/...`), `$ref` por URI `https://juridico-cli.local/...`, cadeias (raiz → arquivo externo → fragmento interno), e segmentos de JSON Pointer escapados (`~0`, `~1`).
- Manter as assinaturas públicas de `load_validator`/`SchemaReferenceError` inalteradas, para que `gemini_client.py` e `DataExtractorApp` continuem funcionando sem alteração de chamada.
- Continuar recusando qualquer resolução remota (`retrieve` nunca configurado).

**Non-Goals:**
- Não corrigir os call sites de `gemini_client.py` para passarem o `schema_path` correto (embora tecnicamente também resolvesse o sintoma) — a correção fica centralizada em `local_resolver.py` conforme requisito do change, tornando o resolvedor robusto independentemente de o chamador acertar o `schema_path`.
- Não tratar truncamento de resposta do Gemini (fora de escopo, marcado explicitamente na proposta).
- Não expandir schemas manualmente nem remover `$defs`.
- Não criar validador ou runtime paralelo.

## Decisions

**Decisão 1 — Registrar o schema em memória diretamente no registry, sob seu `base_uri` efetivo.**
Em vez de depender exclusivamente de `build_local_registry(schema_dir)` (que só enxerga arquivos no disco), `load_validator` passa a construir o recurso do próprio `schema` recebido (`ref_jsonschema.DRAFT202012.create_resource(effective_schema)`) e registrá-lo no registry sob `base_uri` via `registry.with_resource(base_uri, resource)`, **antes** de rodar `_ensure_refs_resolvable`. Isso garante que o documento contra o qual o `$ref` interno (`#/...`) é resolvido é sempre o schema realmente em uso — não uma releitura incidental do disco — eliminando a dependência de que `schema_path` aponte para o diretório certo.
- Alternativa considerada: exigir que todo chamador passe o `schema_path` correto (corrigir `gemini_client.py`). Rejeitada porque o requisito 9 da mudança pede centralização em `local_resolver.py`, e essa abordagem deixaria o resolvedor frágil a qualquer novo chamador que cometa o mesmo engano.

**Decisão 2 — Manter `build_local_registry(schema_dir)` e `build_local_registry(shared_schemas_dir)` para os `$ref` relativos e por URI.**
Referências relativas a arquivo (`defs/common.schema.json#/...`) e por `$id` (`https://juridico-cli.local/...`) continuam resolvidas via os registries construídos a partir do disco, combinados com o registry do schema raiz da Decisão 1. Nenhuma mudança nessa parte — já está coberta por `test_local_schema_reference_resolution.py`.
- Alternativa considerada: substituir totalmente `build_local_registry` por resolução ad-hoc via `retrieve` callback do `referencing`. Rejeitada: exigiria repensar toda a superfície de erro controlado e reintroduziria risco de acesso à rede se mal configurado.

**Decisão 3 — Confiar na resolução de JSON Pointer da biblioteca `referencing` (já usada) para segmentos escapados (`~0`, `~1`) e cadeias de referência.**
A biblioteca `referencing` (jsonschema 4.25.1) já implementa RFC 6901 corretamente, incluindo escaping e navegação encadeada entre resources. O trabalho aqui é garantir que os *documentos* certos estejam no registry (Decisões 1 e 2); a navegação de ponteiro em si não precisa de lógica nova.
- Alternativa considerada: escrever um resolvedor de JSON Pointer manual. Rejeitada — reimplementaria algo que a biblioteca já cobre corretamente; risco maior, nenhum ganho.

**Decisão 4 — Nenhuma lógica específica para `PeticaoIdentification` ou para `extr-peticao-processo`.**
O fix atua sobre o comportamento genérico de `load_validator` para qualquer schema com `$id` e `$defs`, validado pelos testes com uma estrutura equivalente ao schema real (requisito de teste 8), não por um caso especial hardcoded.

## Risks / Trade-offs

- [Risco] Registrar o schema em memória sob `base_uri` pode colidir com uma versão em disco desatualizada do mesmo arquivo (drift entre o que está em memória e o que `build_local_registry` leria do mesmo `$id`) → Mitigação: o registro do schema em memória é feito **depois** da combinação dos registries de disco, então ele sobrepõe (via `with_resource`, que substitui o recurso da mesma URI) qualquer versão desatualizada lida do disco — o documento efetivamente validado sempre vence.
- [Risco] Um schema em memória sem `$id` usa um `base_uri` sintético (`schema_dir` como `file://` — já existente no código); registrar esse schema sintético no registry não deve conflitar com recursos legítimos do disco → Mitigação: o `base_uri` sintético já é derivado do caminho absoluto do diretório do schema (comportamento pré-existente, inalterado), mantendo unicidade.
- [Trade-off] A correção não impede que um chamador futuro continue passando um `schema_path` incorreto (como fez `gemini_client.py`) — mas isso deixa de importar para a resolução de `$ref` internos, que é o requisito central desta mudança.

## Migration Plan

Não há migração de dados. Mudança é um fix pontual em `packages/shared-schemas/local_resolver.py`, com testes adicionados em `apps/data-processing/tests/test_local_schema_reference_resolution.py`. Nenhum rollback especial além de reverter o commit, caso necessário.

## Open Questions

Nenhuma.
