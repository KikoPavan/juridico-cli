## Context

`apps/data-processing/src/data_processing/extractor.py::DataExtractorApp.run_extraction` valida a resposta do LLM antes de persistir (`platform/skill-runtime` fornece `schema_ref` via `SkillDispatcher.dispatch`). A validação atual é:

```python
validator_class = validators.validator_for(schema_json)
validator_class.check_schema(schema_json)
validation_errors = sorted(validator_class(schema_json).iter_errors(payload), ...)
```

Sem `registry`/`resolver`, isso usa o comportamento padrão do `referencing`/`jsonschema`: um `$ref` relativo é resolvido contra o `$id` do schema (`https://juridico-cli.local/schemas/...`) e, na ausência de um recurso pré-carregado para essa URI, a biblioteca tenta buscá-la — daí o erro `Unresolvable` observado em teste operacional real (staging → `extr-peticao-processo` → LLM → validação).

6 das 9 skills `extr-*` registradas em `skill_registry.yaml` referenciam `defs/common.schema.json` a partir de seu `schema_ref` (cabecalho, mandato, contestacao, decisao, peticao, processo). O arquivo real vive em `packages/shared-schemas/defs/common.schema.json`, cujo `$id` é `https://juridico-cli.local/schemas/defs/common.schema.json` — não existe (e não deve existir) um `assets/defs/` local por skill.

Já existem duas resoluções locais equivalentes e não reaproveitadas:
- `platform/skills/extr-processo/scripts/validate_output.py` — usa `referencing.Registry` + `ref_jsonschema.DRAFT202012.create_resource`, registra `common.schema.json` pelo seu `$id`. Padrão correto, mas é um script de skill isolado, não uma dependência central.
- `packages/shared-llm/gemini_client.py` — reimplementa três vezes (`_validate_offline`, dentro de `_execute_extraction_in_blocks`, e no fluxo principal) o mesmo mapeamento via `jsonschema.RefResolver` (API deprecada), com `store` montado manualmente. Usada apenas para validação interna/fallback, nunca para a decisão final de persistência em `extractor.py`.

## Goals / Non-Goals

**Goals:**
- Um único módulo resolve localmente qualquer `$ref` usado pelos schemas `extr-*` (relativo tipo `defs/common.schema.json#/...` e absoluto `https://juridico-cli.local/schemas/...`), sem I/O de rede.
- `extractor.py` usa esse módulo na validação que decide persistência (o ponto que hoje quebra).
- `gemini_client.py` migra suas três implementações duplicadas para o mesmo módulo, sem mudar comportamento observável (mesmas mensagens de fallback, mesmo uso em `_normalize_schema`/blocos).
- Referência não resolvível localmente falha de forma controlada e auditável (mensagem clara, sem tentativa de rede, sem persistir resultado).

**Non-Goals:**
- Não mexe em provider, modelo Gemini ou prompts (`generate_structured` continua chamando o mesmo client).
- Não trata truncamento/fallback por blocos (comportamento existente de `_execute_extraction_in_blocks` é preservado, só passa a usar o resolvedor central).
- Não altera o conteúdo de nenhum `*.schema.json`.
- Não migra os scripts `validate_output.py` de cada skill (são utilitários de desenvolvimento, fora do caminho de execução real); podem ser alinhados depois, mas não são requisito desta change.

## Decisions

### 1. Local do módulo: `packages/shared-schemas/local_resolver.py`
`packages/shared-schemas/` já é o dono canônico dos arquivos de schema compartilhados (`defs/common.schema.json`, `cadeia_obrigacoes.schema.json`). Colocar a lógica de resolução ali (não em `apps/data-processing/` nem duplicada em `shared-llm`) respeita a regra de `packages/` = componentes compartilhados e evita que `platform/skills/*` ou `apps/*` inventem sua própria resolução. `gemini_client.py` (em `packages/shared-llm/`) e `extractor.py` (em `apps/data-processing/`) importam do mesmo lugar — nenhum dos dois "possui" a lógica.

Alternativa descartada: colocar em `platform/skill-runtime/` junto ao `skill_dispatcher.py`. Rejeitada porque resolução de `$ref` de schema é sobre *schemas compartilhados*, não sobre despacho de skills; o dispatcher continua responsável só por resolver `schema_ref` (o caminho do arquivo), não pelo conteúdo interno do schema.

### 2. API do módulo: registry pré-carregado, não `retrieve` dinâmico
```python
def build_local_registry(shared_schemas_dir: Path) -> referencing.Registry
def load_validator(schema: dict, shared_schemas_dir: Path) -> jsonschema.Draft202012Validator
```
`build_local_registry` varre `shared_schemas_dir` (hoje só `defs/common.schema.json`, mas cobre qualquer schema adicionado depois com `$id` sob `https://juridico-cli.local/schemas/`) e registra cada recurso pelo seu `$id` — mesmo padrão já validado em `extr-processo/scripts/validate_output.py`. Isso resolve simultaneamente:
- `$ref: "defs/common.schema.json#/$defs/X"` (relativo, resolvido pela lib contra o `$id` do schema principal, caindo no `$id` registrado do common).
- `$ref: "https://juridico-cli.local/schemas/defs/common.schema.json#/$defs/X"` (absoluto, bate direto no registro).

Alternativa descartada: um `retrieve` *callable* que resolve URIs sob demanda lendo do disco a cada `$ref`. Mais "dinâmico", mas reintroduz superfície de I/O por referência e comportamento menos previsível para o requisito "MUST NOT acessar rede" — pré-carregar é mais simples de auditar (o conjunto de recursos disponíveis é conhecido antes de validar) e é o padrão já testado no script existente.

Sem `retrieve` configurado, o `referencing.Registry` nunca tenta rede: uma URI ausente do registry gera `Unresolvable`/`NoSuchResource` local, que o módulo converte numa exceção própria com mensagem clara (requisito de falha controlada).

### 3. Ponto de partida = diretório do `schema_ref`, com fallback ao root canônico de schemas compartilhados
O requisito "a validação deve partir do diretório do `schema_ref`" é satisfeito assim: o módulo primeiro tenta resolver um `$ref` relativo como caminho de arquivo relativo ao diretório do schema principal (cobre o caso hipotético de uma skill manter uma cópia local, ex. `assets/defs/...`); se o arquivo não existir ali, cai para o root canônico `packages/shared-schemas/` (onde `defs/common.schema.json` realmente está hoje). Isso não muda o resultado atual (nenhuma skill tem `assets/defs/`) mas mantém a ordem de busca pedida sem hardcodar a suposição "tudo vem de shared-schemas" como único caminho possível.

### 4. `RefResolver` → `referencing.Registry` em `gemini_client.py`
As três ocorrências de `RefResolver(base_uri=..., referrer=..., store=...)` são substituídas por chamadas ao módulo central (que usa `referencing.Registry`, API não deprecada do `jsonschema`). Efeito observável idêntico (mesmos erros/validação), só a implementação interna muda. `_normalize_schema` (que já faz inlining manual de `$defs` para o schema enviado ao Gemini) não muda — ela resolve `$ref` para *montar* o schema enviado à API, não para *validar* uma resposta; é uma preocupação diferente e fica fora do escopo.

### 5. Erro de referência ausente
Nova exceção `SchemaReferenceError(ValueError)` no módulo central, com a URI/caminho que faltou. `extractor.py` deixa propagar (mesmo padrão hoje usado para `ValidationError` — captura no chamador da esteira, loga, não persiste). Isso satisfaz "erro de referência ausente deve produzir falha controlada e mensagem clara" sem introduzir um novo mecanismo de erro paralelo ao já existente em `run_extraction`.

## Risks / Trade-offs

- [Risco] Pré-carregar todo `packages/shared-schemas/` no registry pode incluir arquivos não relacionados (`cadeia_obrigacoes.schema.json`) → Mitigação: registrar por `$id` real de cada arquivo (não por convenção de nome); um schema extra registrado e não referenciado é inofensivo, só ocupa um slot no dicionário em memória.
- [Risco] Migrar `gemini_client.py` de `RefResolver` para `Registry` pode mudar sutilmente mensagens de erro internas usadas em `_validate_offline`/fallback → Mitigação: testes existentes de fallback por blocos (`test_judicial_markdown_flow.py` e afins) continuam rodando como validação de regressão; nenhuma asserção deve depender do texto exato do erro do `jsonschema`.
- [Risco] Dois caminhos de import (relativo vs `load_module_from_path`) para o novo módulo, replicando a fragilidade já existente no projeto → Mitigação: não é introduzida fragilidade nova, é o mesmo padrão dual já usado por `client.py`/`gemini_client.py`; documentar isso explicitamente nas tasks para não haver ambiguidade na implementação.

## Migration Plan

Mudança é local a validação em processo, sem estado persistido ou schema de dados migrando. Deploy = merge normal; rollback = reverter o commit (nenhuma migração de dados envolvida). Nenhuma flag de feature necessária.
