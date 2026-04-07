> [!NOTE]
> **DOCUMENTO AUXILIAR OPERACIONAL — MATRIZ DE IMPLANTAÇÃO**
> Registro objetivo do estado operacional real do repositório. Atualizar sempre que houver mudança de status de um componente.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Matriz de Implantação Real — `juridico-cli`

**Data:** 2026-04-04
**Base:** inspeção real do repositório + testes de carga, importação e smoke tests operacionais (Task 10)

---

## 1. Runtime — `platform/skill-runtime/`

| Componente | Caminho esperado | Existe? | Operacional? | Observação |
|---|---|---|---|---|
| Diretório runtime | `platform/skill-runtime/` | Sim | Sim | Canônico |
| Despacho de skills | `platform/skill-runtime/skill_dispatcher.py` | Sim | **Sim** | `SkillDispatcher.dispatch()` operacional; integrado ao `apps/data-processing` |
| Carregador de bundles | `platform/skill-runtime/bundle_loader.py` | Sim | **Sim** | Loader interno usado via dispatcher |
| Registro de skills | `platform/skill-runtime/skill_registry.yaml` | Sim | Sim | Carrega OK; chave raiz `skills` |
| Registro de LLMs | `platform/skill-runtime/llm_registry.yaml` | Sim | Sim | Carrega OK; chaves `execution_classes`, `profiles` |

### Status após Task 8 (2026-04-03)

`skill_dispatcher.py` foi corrigido e é o caminho canônico real. Bugs resolvidos:

| Bug (resolvido) | Correção aplicada |
|---|---|
| Import plana `from bundle_loader import BundleLoader` | Substituído por `_load_module_from_path` com path absoluto |
| `self.skill_reg["bundles"]` | Corrigido para `self.skill_reg["skills"]` |
| `self.llm_reg["models"]` | Corrigido para `self.llm_reg["profiles"]` |
| `_load_yaml` duplicado | Removida a duplicata |
| `route_and_execute` skeleton | Substituído por `dispatch(bundle_id)` funcional |

`apps/data-processing/extractor.py` integrado: usa `SkillDispatcher` — não contorna mais o dispatcher.

---

## 2. Camada de skills — `platform/skills/`

| Componente | Caminho esperado | Existe? | Registrado? | Operacional? | Observação |
|---|---|---|---|---|---|
| Regras transversais | `platform/skills/_shared/extraction-base.md` | Sim | N/A | Sim | Injetada pelo `bundle_loader` |
| Regras processuais | `platform/skills/_shared/proc-core.md` | Sim | N/A | Sim | Referenciada pelos bundles `extr-*` |
| extr-cabecalho-processo | `platform/skills/extr-cabecalho-processo/` | Sim | Sim | Sim | SKILL.md presente |
| extr-contestacao-processo | `platform/skills/extr-contestacao-processo/` | Sim | Sim | Sim | SKILL.md presente |
| extr-contrato-social | `platform/skills/extr-contrato-social/` | Sim | Sim | Sim | SKILL.md presente |
| extr-decisao-processo | `platform/skills/extr-decisao-processo/` | Sim | Sim | Sim | SKILL.md presente |
| extr-escritura-hipotecaria | `platform/skills/extr-escritura-hipotecaria/` | Sim | Sim | Sim | SKILL.md presente |
| extr-escritura-imovel | `platform/skills/extr-escritura-imovel/` | Sim | Sim | Sim | SKILL.md presente |
| extr-mandato-processo | `platform/skills/extr-mandato-processo/` | Sim | Sim | Sim | SKILL.md presente |
| extr-peticao-processo | `platform/skills/extr-peticao-processo/` | Sim | Sim | Sim | SKILL.md presente |
| extr-processo | `platform/skills/extr-processo/` | Sim | Sim | Sim | SKILL.md presente |
| extr-procuracao | `platform/skills/extr-procuracao/` | Sim | Sim | Sim | SKILL.md presente; `load_bundle` testado: OK (prompt 8136 chars) |
| extr-dummy | `platform/skills/extr-dummy/` | Sim | **Não** | Parcial | Existe no disco; sem entrada em `skill_registry.yaml` |
| jus-breve | `platform/skills/jus-breve/` | Sim | **Não** | Parcial | Existe no disco; sem entrada em `skill_registry.yaml` |
| jus-diagnose | `platform/skills/jus-diagnose/` | Sim | **Não** | Parcial | Existe no disco; sem entrada em `skill_registry.yaml` |
| legal-data-extractor | `platform/skills/legal-data-extractor/` | Sim | **Não** | Parcial | Existe no disco; sem entrada em `skill_registry.yaml` |
| pdf | `platform/skills/pdf/` | Sim | **Não** | Parcial | Existe no disco; sem entrada em `skill_registry.yaml` |
| skill-creator | `platform/skills/skill-creator/` | Sim | **Não** | Parcial | Ferramenta de criação de skills; sem entrada em `skill_registry.yaml` |

> **Resumo skills:** 10/16 registradas e operacionais via registry. 6 existem no disco mas não são despacháveis pelo runtime atual.

---

## 3. App canônico — `apps/data-processing/`

| Componente | Caminho esperado | Existe? | Operacional? | Observação |
|---|---|---|---|---|
| CLI canônica | `apps/data-processing/src/data_processing/cli.py` | Sim | **Sim** | `--help` funciona; comandos: `run`, `clean`, `analyze`, `convert`, `extract` |
| Orchestrator | `apps/data-processing/src/data_processing/orchestrator/` | Sim | Sim | `pipeline_runner.py`, `stage_router.py`, `contracts.py` presentes |
| Collectors | `apps/data-processing/src/data_processing/collectors/` | Sim | Sim | `collector_cad_obr` e `collector_proc` presentes |
| Converters | `apps/data-processing/src/data_processing/converters/` | Sim | Sim | `gemini_ocr`, `markdown_engine` presentes |
| Cleaners | `apps/data-processing/src/data_processing/cleaners/` | Sim | Sim | `clean_legal_docs.py` presente |
| Rule analysis | `apps/data-processing/src/data_processing/rule_analysis/` | Sim | Sim | `analisador_de_regras.py` presente |
| Validation | `apps/data-processing/src/data_processing/validation/` | Sim | Sim | `contract_validation.py`, `output_checks.py` presentes |
| Loaders | `apps/data-processing/src/data_processing/loaders/` | Sim | Sim | `qdrant_loader.py`, `json_store.py`, `index_registry.py` presentes |
| Extractor | `apps/data-processing/src/data_processing/extractor.py` | Sim | Sim | Usa `SkillDispatcher` (caminho canônico) |
| Testes | `apps/data-processing/tests/` | Sim | **Sim** | 20/20 passando |

> **Nota:** `run --collector` aceita `cad_obr` ou `proc`. Output default: `var/output/`. CLI operacional para uso local.

---

## 4. Packages compartilhados — `packages/`

| Pacote | Caminho | Existe? | Tem conteúdo? | Observação |
|---|---|---|---|---|
| shared-schemas | `packages/shared-schemas/` | Sim | Sim | `cadeia_obrigacoes.schema.json` + `defs/common.schema.json` |
| shared-llm | `packages/shared-llm/` | Sim | Sim | `__init__.py` + `client.py` |
| shared-core | `packages/shared-core/` | Sim | **Vazio** | Diretório criado, sem código |
| shared-utils | `packages/shared-utils/` | Sim | **Vazio** | Diretório criado, sem código |
| shared-legal | `packages/shared-legal/` | Sim | **Vazio** | Diretório criado, sem código |

---

## 5. I/O operacional — `var/`

| Subdiretório | Existe? | Operacional? | Observação |
|---|---|---|---|
| `var/input/` | Sim | Sim | Subdiretórios: `json`, `md`, `raw` |
| `var/output/` | Sim | Sim | Tem output de teste: `result_extr-contrato-social_test_social.json` |
| `var/staging/` | Sim | Sim | Presente |
| `var/logs/` | Sim | Sim | Presente |
| `var/cache/` | Sim | Sim | Presente |
| `var/artifacts/` | Sim | Sim | Presente |
| `var/backups/` | Sim | Sim | Presente |
| `var/input/proc` | **Não** | N/A | Path default nos SKILL.md (`extr-*`); criado sob demanda em runtime |
| `var/output/proc` | **Não** | N/A | Path default nos SKILL.md (`extr-*`); criado sob demanda em runtime |

---

## 6. Previstos no canônico — não implementados

| Componente | Caminho esperado | Status | Observação |
|---|---|---|---|
| App legal-research | `apps/legal-research/` | Não criado | Previsto em seção 4 do canônico v2 |
| App legal-core | `apps/legal-core/` | Não criado | Previsto em seção 4 do canônico v2 |
| App orchestrator-cli | `apps/orchestrator-cli/` | Não criado | Previsto em seção 4 do canônico v2 |
| Infraestrutura Docker | `infra/` | **Implementado** | Task 9 — `infra/docker/`, `infra/qdrant/`, `infra/env/` — ver seção 8 |
| memory-and-experiences | `platform/memory-and-experiences/` | Criado (vazio) | Sem conteúdo operacional |
| continuous-learning | `platform/continuous-learning/` | Criado (vazio) | Sem conteúdo operacional |

---

## 7. Legado congelado — existe, não é autoridade

| Diretório | Existe? | Usado em produção? | Observação |
|---|---|---|---|
| `agents/` (8 subdiretórios) | Sim | Manutenção | Congelado; não usar como referência arquitetural |
| `pipelines/cad_obr/` | Sim | Manutenção | Congelado |
| `pipelines/ingest/` | Sim | Manutenção | Congelado |
| `outputs/` (raiz) | Sim | Legado | I/O legado; usar `var/` para novos fluxos |
| `data/` | Sim | Legado | Dados de entrada legado |
| `input/` (raiz) | Sim | Legado | Legado; usar `var/input/` |
| `logs/` (raiz) | Sim | Legado | Legado; usar `var/logs/` |

---

## 8. Infraestrutura — `infra/`

> **Docker local = Docker Desktop (Windows + WSL2).**
> Não usar Docker Engine puro como referência para este projeto.

### Status após Task 9 (2026-04-04)

| Arquivo | Caminho | Existe? | Operacional? | Observação |
|---|---|---|---|---|
| Compose local | `infra/docker/docker-compose.yml` | **Sim** | **Sim** | Serviços: `juridico-qdrant` + `juridico-llama-cpp` (profile `local-llm`) |
| Config Qdrant | `infra/qdrant/config.yaml` | **Sim** | Sim | Montado em `/qdrant/config/production.yaml` |
| Env template | `infra/env/.env.example` | **Sim** | Sim | Copiar para `infra/env/.env` antes de subir |
| Env real | `infra/env/.env` | Não commitado | — | Ignorado via `.gitignore`; criado pelo operador |

### Definição de cada serviço

| Serviço | Imagem | Porta | Variáveis obrigatórias | Status validação |
|---|---|---|---|---|
| Gemini API | — (sem container) | — | `GEMINI_API_KEY` | **Testado — operacional** |
| llama.cpp | `ghcr.io/ggml-org/llama.cpp:server` | 8080 | `LLAMA_MODELS_PATH`, `LLAMA_MODEL_FILE` | **Testado — operacional** |
| Qdrant | `qdrant/qdrant:v1.16.0` | 6333 (REST), 6334 (gRPC) | — | **Testado — operacional** |

### Comandos mínimos de operação

```bash
# Subir apenas Qdrant (padrão)
docker compose --env-file infra/env/.env -f infra/docker/docker-compose.yml up -d

# Subir Qdrant + llama.cpp (requer .gguf — verificar pré-flight antes)
bash scripts/check_llama_ready.sh
docker compose --env-file infra/env/.env -f infra/docker/docker-compose.yml --profile local-llm up -d

# Parar
docker compose -f infra/docker/docker-compose.yml down

# Verificar
docker compose -f infra/docker/docker-compose.yml ps
curl http://localhost:6333/healthz      # Qdrant
curl http://localhost:8080/health       # llama.cpp (após ativar --profile local-llm)
```

---

## 9. Resumo executivo

| Bloco | Status | Detalhe |
|---|---|---|
| `skill_dispatcher.py` | **Operacional** | `SkillDispatcher.dispatch()` funcional; 5 bugs corrigidos (Task 8) |
| `bundle_loader.py` | **Operacional** | Loader interno; chamado via dispatcher |
| `skill_registry.yaml` | **Operacional** | 10 skills registradas, todas com path correto |
| `llm_registry.yaml` | **Operacional** | Carrega com estrutura correta |
| `apps/data-processing/` CLI | **Operacional** | CLI funciona; 20 testes passando |
| Skills `extr-*` (10) | **Operacionais** | Todas registradas, com SKILL.md, resolúveis via bundle_loader |
| Skills não registradas (6) | **Parcial** | Existem no disco, não despacháveis pelo runtime |
| `packages/` (3 de 5) | **Parcial** | shared-core, shared-utils, shared-legal são diretórios vazios |
| `var/` | **Operacional** | Estrutura presente; `var/input/proc` e `var/output/proc` criados sob demanda |
| `infra/` (Qdrant) | **Operacional e testado** | qdrant v1.16.0 rodando, qdrant-client OK (Task 10) |
| `infra/` (llama.cpp) | **Operacional e testado** | `Llama-3.2-3B-Instruct-Q4_K_L.gguf` carregado; `/health` + `/v1/models` validados (Task 12) |
| Gemini API | **Operacional e testado** | `gemini-2.5-flash` e `gemini-2.5-pro` confirmados via `client.models.list()` |
| `apps/legal-*` | **Não implementado** | Previstos no canônico, não existem no repo |
