## Why

### Problema Real Confirmado

O comando:

```
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli extract \
  --bundle "extr-peticao-processo" \
  --input "Petição Declaração de Nulidade.md"
```

falha por duas razões independentes:

**1. Path incorreto** — o `extract` lê de `var/staging/` (hardcoded em `extractor.py:58`),
mas o help informa `var/input/md/`. O usuário precisa copiar manualmente o arquivo para
`var/staging/`. O caminho canônico real de saída do `clean` é `var/output/processed/`,
que já existe.

**2. Provider LLM errado** — o bundle `extr-peticao-processo` está mapeado em
`skill_registry.yaml` para o profile `high_reasoning`. No `llm_registry.yaml`,
`high_reasoning` aponta para `gemini_api`/`gemini-3-flash-preview`. Porém,
`extractor.py:98` chama `LLMClientFactory.create_client()` **sem argumentos**,
ignorando o profile. A factory lê `LLM_PROVIDER=local` do `.env` e tenta conectar
em `http://host.docker.internal:1234` (llama.cpp).

### Causa Raiz Detalhada

**Causa 1 — Path hardcoded incorreto:**
- `extractor.py:31`: `staging` = `var/staging`
- `extractor.py:58`: lê de `var/staging/<input_filename>`
- `cli.py:82`: `clean --output` default `var/staging`
- `cli.py:19`: help diz `var/input/md/` mas código usa `var/staging`

**Causa 2 — Provider LLM ignorado:**
- `skill_registry.yaml:45-48`: `extr-peticao-processo` → `high_reasoning`
- `llm_registry.yaml:34-37`: `high_reasoning` → `gemini_api`/`gemini-3-flash-preview`
- `extractor.py:98`: `client = LLMClientFactory.create_client()` — sem provider_override
- `client.py:66`: lê `LLM_PROVIDER` do `.env` → `local`
- `.env:2`: `LLM_PROVIDER=local` → força llama.cpp

**Causa 3 — Saída JSON na raiz de output:**
- `extractor.py:108-109`: salva em `var/output/result_*.json`
- Não há pasta canônica dedicada para extrações estruturadas

### Arquivos que Precisam Mudar

| Arquivo | Linha | Mudança |
|---|---|---|
| `extractor.py` | 31 | `staging` → `output/processed` como entrada |
| `extractor.py` | 58 | Ler de `dirs["input_clean"]` em vez de `dirs["staging"]` |
| `extractor.py` | 98 | Passar `provider_override` do `llm_profile` |
| `extractor.py` | 32 | Adicionar `output_extracted` → `var/output/extracted` |
| `extractor.py` | 108-109 | Salvar em `dirs["output_extracted"]` |
| `cli.py` | 19 | Help corrigir para `var/output/processed/` |
| `cli.py` | 82 | Default `clean --output` → `var/output/processed` |

### Arquivos Não Alterados

- `platform/skill-runtime/skill_registry.yaml` — já correto
- `platform/skill-runtime/llm_registry.yaml` — já correto
- `platform/skills/extr-*` — skills não mudam
- `stage_router.py` — pipeline `run` não é alterado
- `.env` — não alterado
- Testes existentes
- `convert` — inalterado

### Breaking Changes

**1 breaking change leve:** o default do `clean --output` muda de `var/staging` para
`var/output/processed`. Usuários que chamam `clean` sem `--output` e depois buscam
arquivos em `var/staging/` manualmente precisarão passar `--output var/staging` explícito.
O pipeline `run` não é afetado porque usa paths explícitos em `stage_router.py`.

### Comandos Finais Esperados

```bash
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli clean \
  --input "var/input/md" \
  --output "var/output/processed"

PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli extract \
  --bundle "extr-peticao-processo" \
  --input "Petição Declaração de Nulidade_clean.md"
```

- Entrada: `var/output/processed/Petição Declaração de Nulidade_clean.md`
- Saída: `var/output/extracted/result_extr-peticao-processo_Petição...json`
- Provider: Gemini (via GEMINI_API_KEY), sem tentar llama.cpp

## What Changes

### Arquivos Alterados

- **`apps/data-processing/src/data_processing/extractor.py`**
  - Substituir diretório de entrada de `staging` para `var/output/processed`
  - Passar o `llm_profile` resolvido pelo dispatcher para o `LLMClientFactory.create_client()`
  - Alterar diretório de saída de `var/output/` para `var/output/extracted/`
  - Adicionar log com o provider efetivamente usado

- **`apps/data-processing/src/data_processing/cli.py`**
  - Corrigir help do `extract --input` de `var/input/md/` para `var/output/processed/`
  - Alterar default do `clean --output` de `var/staging` para `var/output/processed`

- **`packages/shared-llm/client.py`**
  - Nenhuma mudança necessária: o parâmetro `provider_override` já existe no `create_client()`
  - Apenas `extractor.py` precisa começar a usá-lo

### Arquivos Não Alterados

- `platform/skill-runtime/skill_registry.yaml` — já correto
- `platform/skill-runtime/llm_registry.yaml` — já correto
- `platform/skills/extr-peticao-processo/*` — skills não mudam
- `apps/data-processing/src/data_processing/orchestrator/stage_router.py` — fluxo `run` não é alterado
- Testes existentes
- `.env` — não será alterado

### Novos Diretórios

- `var/output/extracted/` — criado automaticamente pelo `DataExtractorApp.__init__`

## Capabilities

### New Capabilities

- **`extract-gemini-provider`**: o comando `extract` passa o provider resolvido pelo
  `llm_registry` para o `LLMClientFactory`, eliminando dependência de
  `LLM_PROVIDER=gemini` como pré-requisito externo. Se o profile apontar para
  `gemini_api`, usa Gemini mesmo que `.env` defina `LLM_PROVIDER=local`.

- **`extract-canonical-input-path`**: o comando `extract` localiza o arquivo de
  entrada em `var/output/processed/` (onde o `clean` já deposita seus resultados)
  sem exigir cópia manual para `var/staging`.

- **`extract-canonical-output-path`**: o JSON extraído é salvo em
  `var/output/extracted/` como pasta canônica definitiva do projeto, seguindo o
  padrão `var/output/<dominio>/` já usado por outras skills.

### Modified Capabilities

- **`clean-default-output`**: o default do `--output` do comando `clean` muda de
  `var/staging` para `var/output/processed`, alinhando o fluxo convert → clean →
  extract sem caminhos divergentes.

## Impact

### Afetados (diretamente)
- `apps/data-processing/src/data_processing/extractor.py` — 3 mudanças localizadas
- `apps/data-processing/src/data_processing/cli.py` — 2 mudanças localizadas

### Não afetados
- `convert`, `run`, `analyze` — fluxos inalterados
- `platform/skill-runtime/` — registros já estão corretos
- `platform/skills/` — skills não são alteradas
- `packages/shared-llm/client.py` — API já suporta `provider_override`
- Testes existentes
- `.env`

### Pasta nova
- `var/output/extracted/` — criada em runtime pelo `os.makedirs`

### Breaking changes
- **1 breaking change leve** no `clean`: usuários que dependem do default
  `var/staging` precisarão passar `--output var/staging` explicitamente.
  O pipeline `run` é preservado porque usa paths explícitos em `stage_router.py`.
