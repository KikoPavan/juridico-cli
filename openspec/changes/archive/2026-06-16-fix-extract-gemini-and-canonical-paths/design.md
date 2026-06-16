## Context

O `DataExtractorApp` em `extractor.py` é o orquestrador V1.1 do pipeline de extração
estruturada. Ele:

1. Lê um arquivo Markdown de `var/staging/` (hardcoded)
2. Despacha o bundle via `SkillDispatcher.dispatch()`, que resolve o perfil LLM
3. Cria um cliente LLM via `LLMClientFactory.create_client()` — sem usar o perfil
4. Envia o texto para o LLM com schema JSON
5. Salva o resultado em `var/output/`

O `llm_registry.yaml` já mapeia `high_reasoning` → `gemini_api`/`gemini-3-flash-preview`.
O `skill_registry.yaml` já mapeia `extr-peticao-processo` → `high_reasoning`.
O `LLMClientFactory.create_client()` já aceita `provider_override` como parâmetro.

O único ponto de falha é que `extractor.py:98` não passa o provider resolvido para a factory.

## Goals / Non-Goals

**Goals:**
- Extract lê de `var/output/processed/` (já existe no disco)
- Extract usa Gemini conforme profile do bundle
- Extract salva JSON em `var/output/extracted/` (pasta canônica nova)
- Help do CLI reflete caminhos reais
- `clean --output` default aponta para `var/output/processed`

**Non-Goals:**
- Não alterar `convert`
- Não alterar pipeline `run` (stage_router.py)
- Não alterar registros de skills ou LLMs
- Não alterar skills canônicas
- Não alterar `.env`
- Não alterar testes existentes
- Não criar pasta temporária de teste
- Não fazer commit
- Não arquivar

## Decisions

### D1: Entrada do extract → `var/output/processed/`

Substituir `staging` por `input_clean` apontando para `var/output/processed/`.
O nome `staging` é semanticamente enganoso — não é temporário, é o diretório de
Markdown limpo e processado.

Pipeline `run` não é afetado: usa `stage_router.py` com paths explícitos.

### D2: Provider LLM → usar `llm_profile` do dispatcher

Em `extractor.py:98`, extrair o provider do `llm_profile`:

```python
provider = dispatch_result["llm_profile"]["execution_class"]["provider"]
client = LLMClientFactory.create_client(provider_override=provider)
```

Se o `llm_profile` não tiver `execution_class.provider`, fallback para `LLM_PROVIDER`
do ambiente (comportamento atual preservado).

Nenhum outro consumidor do `LLMClientFactory` será afetado porque continuam chamando
`create_client()` sem argumento, mantendo o comportamento via `.env`.

### D3: Saída JSON → `var/output/extracted/`

Adicionar `output_extracted: var/output/extracted` ao `self.dirs`.

Justificativa: segue o padrão `var/output/<dominio>/` já usado por outras skills
(`proc/`, `cad_obr/`, `md-frontmatter-yaml/`, etc.). `var/output/proc/` foi
descartado porque não existe no disco e é específico de domínio processual,
enquanto `extract` é genérico.

### D4: `cli.py` help do `extract --input`

Corrigir de `"Nome do arquivo em var/input/md/ para processar"` para
`"Nome do arquivo limpo em var/output/processed/ para extrair"`.

### D5: `cli.py` default do `clean --output`

Mudar de `Path("var/staging")` para `Path("var/output/processed")`.

Breaking change leve documentado. Usuários que dependem do default antigo precisam
passar `--output var/staging` explicitamente.

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| Breaking change no `clean` sem `--output` | Documentar no help e na saída do comando |
| `var/output/extracted/` não existir | `os.makedirs` no `__init__` cria automaticamente |
| Provider ausente no `llm_profile` | Fallback para `LLM_PROVIDER` do ambiente (comportamento atual) |
| pipeline `run` esperar `var/staging` | `stage_router.py` usa paths explícitos, não defaults do CLI |
| Alguém depender de `var/staging` para outro propósito | Manter `var/staging/` existindo; apenas mudar defaults |

## Open Questions

**Q1: Modelo Gemini a usar?**

Há divergência entre as definições atuais:

| Fonte | Modelo | Status na Matriz de Versões |
|---|---|---|
| `gemini_client.py:21` (default) | `gemini-2.5-flash` | Não registrado |
| `llm_registry.yaml:37` | `gemini-3-flash-preview` | Não registrado |
| `project_version_matrix.md:86` | `A definir` | Nenhum modelo validado formalmente |

**Decisão pendente de validação:** durante a task T7 (validação real), testar
primeiro `gemini-3-flash-preview` (conforme registry). Se falhar, usar
`gemini-2.5-flash` (default do client). Se a troca for necessária, alterar
apenas `llm_registry.yaml` — não alterar o default do `gemini_client.py`.

Após validação, registrar o modelo na `project_version_matrix.md`.
