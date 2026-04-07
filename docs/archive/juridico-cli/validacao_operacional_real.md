> [!NOTE]
> **DOCUMENTO AUXILIAR OPERACIONAL — VALIDAÇÃO OPERACIONAL REAL**
> Registro dos resultados de smoke tests ponta a ponta. Atualizar a cada nova validação.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Validação Operacional Real — `juridico-cli`

**Data:** 2026-04-04 (atualizado Task 12)
**Escopo:** Tasks 10–12 — validação ponta a ponta do runtime com infraestrutura mínima
**Ambiente:** WSL2 + Docker Desktop 28.1.1

---

## 1. Resultado por componente

| Componente | Testado? | Resultado | Bloqueio |
|---|---|---|---|
| **Qdrant** (Docker Desktop) | **Sim** | **Operacional** | — |
| **Gemini API** | **Sim** | **Operacional** | — |
| **runtime / dispatcher** | **Sim** | **Operacional** | — |
| **llama.cpp** (Docker Desktop) | **Sim** | **Operacional** | — |

---

## 2. Qdrant

**Status: operacional e testado.**

```
Imagem:   qdrant/qdrant:v1.16.0
Container: juridico-qdrant
Portas:   6333 (REST), 6334 (gRPC)
Volume:   juridico-qdrant-storage (persistente)
```

**Evidências:**

```
GET http://localhost:6333/healthz → "healthz check passed"
GET http://localhost:6333/        → {"version": "1.16.0", ...}
docker compose ps → STATUS: Up (healthy)
qdrant-client 1.16.2: conectado (0 collections)
smoke_test: create → list → delete OK
```

**Correção aplicada durante validação:**

A imagem original `qdrant/qdrant:v1.13.4` era incompatível com `qdrant-client>=1.16.2`
(diferença de 3 minor versions, limite permitido é 1). Corrigida para `v1.16.0`.

---

## 3. Gemini API

**Status: operacional e testado com chamada real.**

```
SDK:      google.genai (novo SDK — google-generativeai não está instalado)
Variável: GEMINI_API_KEY (configurada no ambiente — 39 chars)
```

**Evidências:**

```
client.models.list() → 50 modelos disponíveis
Modelos canônicos confirmados:
  - models/gemini-2.5-flash  ✓
  - models/gemini-2.5-pro    ✓
```

**Observação sobre o SDK:**

O projeto usa `google.genai` (novo SDK unificado), não `google-generativeai` (SDK legado).
O `llm_registry.yaml` referencia os modelos pelo ID canônico — nenhuma mudança necessária.

---

## 4. Runtime / Dispatcher

**Status: operacional e testado — 10/10 skills resolvidas.**

```
Arquivo: platform/skill-runtime/skill_dispatcher.py
Classe:  SkillDispatcher.dispatch(bundle_id)
```

**Evidências:**

```python
d = SkillDispatcher(platform_path="platform")
result = d.dispatch("extr-procuracao")
# bundle_id       : extr-procuracao
# profile_name    : fast_extraction
# execution_class : gemini_api
# model           : gemini-2.5-flash
# system_prompt   : 8136 chars
```

**Resolução completa das 10 skills registradas:**

| Skill | Perfil | Execution class |
|---|---|---|
| extr-contrato-social | high_reasoning | gemini_api |
| extr-escritura-imovel | large_context | gemini_api |
| extr-escritura-hipotecaria | high_reasoning | gemini_api |
| extr-cabecalho-processo | fast_extraction | gemini_api |
| extr-mandato-processo | high_reasoning | gemini_api |
| extr-processo | large_context | gemini_api |
| extr-contestacao-processo | high_reasoning | gemini_api |
| extr-decisao-processo | large_context | gemini_api |
| extr-peticao-processo | high_reasoning | gemini_api |
| extr-procuracao | fast_extraction | gemini_api |

**Observação:** Todas as 10 skills mapeiam para `gemini_api`. O perfil `local_preprocessing`
(que mapeia para `llama_cpp_local`) existe no `llm_registry.yaml` mas não está atribuído
a nenhuma skill registrada atualmente — disponível para uso futuro.

---

## 5. llama.cpp (Docker Desktop)

**Status: operacional e testado. (Task 12)**

```
Imagem:    ghcr.io/ggml-org/llama.cpp:server
Container: juridico-llama-cpp
Profile:   local-llm (--profile local-llm no compose)
Porta:     8080
```

**Evidências:**

```
GET http://localhost:8080/health    → {"status":"ok"}
GET http://localhost:8080/v1/models → modelo carregado: Llama-3.2-3B-Instruct-Q4_K_L.gguf
```

**Como foi ativado:**

```bash
bash scripts/check_llama_ready.sh   # retornou PRONTO
docker compose --env-file infra/env/.env \
  -f infra/docker/docker-compose.yml \
  --profile local-llm up -d
```

**Pré-flight (Task 11 — disponível para futuras reinstalações):**

```bash
bash scripts/check_llama_ready.sh
# Verifica: .env existe · LLAMA_MODELS_PATH preenchido · .gguf existe · Docker online
```

---

## 6. Correções aplicadas durante a validação

| Arquivo | Correção |
|---|---|
| `infra/docker/docker-compose.yml` | Imagem Qdrant: `v1.13.4` → `v1.16.0` (incompatibilidade com qdrant-client 1.16.2) |
| `infra/docker/docker-compose.yml` | llama-cpp: adicionado `profiles: [local-llm]` para evitar falha de parse quando `LLAMA_MODELS_PATH` não está definido |
| `infra/docker/docker-compose.yml` | healthcheck: `CMD curl` → `CMD bash -c "echo > /dev/tcp/localhost/6333"` (curl e wget ausentes na imagem Qdrant; sh não suporta /dev/tcp) |
| `infra/env/.env.example` | Comandos de uso atualizados para refletir os perfis Docker Compose |

---

## 7. Resumo executivo de estado

| Bloco | Estado atual |
|---|---|
| Qdrant local (Docker Desktop) | **Operacional e testado** |
| Gemini API | **Operacional e testado** |
| Runtime / dispatcher (10 skills) | **Operacional e testado** |
| llama.cpp local (Docker Desktop) | **Operacional e testado** — `Llama-3.2-3B-Instruct-Q4_K_L.gguf` carregado |
| Integração Python → Qdrant | **Operacional (qdrant-client 1.16.2 + servidor v1.16.0)** |
