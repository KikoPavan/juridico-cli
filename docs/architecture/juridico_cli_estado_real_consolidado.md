# Estado Real Consolidado — `juridico-cli`

**Data:** 2026-04-06
**Fonte:** Varredura direta do código + comparação com documentos de referência
**Referência principal:** `docs/architecture/juridico_cli_documento_mestre.md`
**Documentos comparados:**
- `docs/architecture/juridico_cli_estado_real_implantado.md` (2026-04-05)
- `docs/architecture/juridico_cli_gaps_e_proximo_passo.md` (2026-04-05)
- `docs/qwen_tasks/juridico_cli_estado_real.md`
- `docs/runbooks/runbook_operacional_minimo.md`

---

## 1. Resumo Executivo

O `juridico-cli` é um monorepo Python 3.12+ para processamento documental jurídico com LLMs, organizado em arquitetura **skill-centric**. O projeto está **majoritariamente alinhado** ao documento mestre, com runtime canônico operacional, 15 skills no disco (13 registradas), módulo `apps/data-processing/` funcional com pipeline de 6 etapas, e infraestrutura Docker configurada.

**Três componentes declarados como obrigatórios no documento mestre estão ausentes ou não funcionais:** Mem0 (adapter existe mas importa libs não instaladas), TurboQuant (nenhum código) e RLM (nenhum código). O runbook operacional contém itens desatualizados (pipeline genérico já está criado).

---

## 2. Estado Atual Implantado — Verificado no Código

### 2.1 Runtime Canônico

| Componente | Caminho | Estado | Detalhes |
|---|---|---|---|
| Skill Dispatcher | `platform/skill-runtime/skill_dispatcher.py` | ✅ Funcional | Resolve skill por bundle_id, carrega bundle via BundleLoader, retorna system_prompt + skill_config + llm_profile |
| Bundle Loader | `platform/skill-runtime/bundle_loader.py` | ✅ Funcional | Parseia SKILL.md (frontmatter YAML + body), injeta `_shared/extraction-base.md` transversal, carrega schema JSON local |
| Skill Registry | `platform/skill-runtime/skill_registry.yaml` | ✅ 13 skills registradas | 10 extr-* + 3 pipeline genérico |
| LLM Registry | `platform/skill-runtime/llm_registry.yaml` | ✅ 4 profiles + 2 execution classes | `gemini_api` (flash + pro) + `llama_cpp_local` |

**Como o dispatcher funciona (código real):**
1. Recebe `bundle_id` (ex: `extr-contrato-social`)
2. Busca config em `skill_registry.yaml`
3. Resolve profile LLM em `llm_registry.yaml`
4. BundleLoader carrega SKILL.md + extraction-base.md + schema JSON
5. Retorna dict com `system_prompt`, `skill_config`, `llm_profile`, `bundle_id`

### 2.2 Skills — Estado Real Completo

#### Registradas (13)

| Skill | Profile | Schema | Scripts funcionais | Dependência LLM |
|---|---|---|---|---|
| `extr-cabecalho-processo` | fast_extraction | ✅ header_schema.json | ❌ | LLM médio |
| `extr-contestacao-processo` | high_reasoning | ✅ contestacao_schema.json + validation_rules.md | ❌ | LLM avançado |
| `extr-contrato-social` | high_reasoning | ✅ contrato_schema.json | ⚠️ run_example.sh | LLM avançado |
| `extr-decisao-processo` | large_context | ✅ decisao_schema.json | ❌ | LLM avançado |
| `extr-escritura-hipotecaria` | high_reasoning | ✅ hipoteca_schema.json | ✅ validate_hipoteca.py | LLM avançado |
| `extr-escritura-imovel` | large_context | ✅ escritura_schema.json | ❌ | LLM avançado |
| `extr-mandato-processo` | high_reasoning | ✅ mandato_schema.json + validation_rules.json | ✅ validate_mandato.py | LLM médio-avançado |
| `extr-peticao-processo` | high_reasoning | ✅ peticao_inicial_schema.json + validation_rules.json | ❌ | LLM avançado |
| `extr-processo` | large_context | ✅ processo_schema.json + validation_rules.json | ✅ orchestrate.py + validate_processo.py | LLM avançado (orquestradora) |
| `extr-procuracao` | fast_extraction | ✅ procuracao_schema.json | ❌ | LLM médio |
| `pdf-to-md` | local_preprocessing | ❌ | ✅ 4 scripts (convert, validate, package, run) | LLM mínimo (determinístico) |
| `md-clean-markdown` | local_preprocessing | ❌ | ⚠️ run_example.sh | LLM mínimo (determinístico) |
| `md-frontmatter-yaml` | local_preprocessing | ❌ | ⚠️ run_example.sh | LLM mínimo (pode precisar de LLM leve) |

#### Não registradas — operacionais (2)

| Skill | Profile esperado | Schema | Scripts funcionais | Classificação |
|---|---|---|---|---|
| `jus-breve` | high_reasoning | ✅ breve_schema.json + validation_rules.json | ⚠️ run_example.sh | **Operacional — pendente de registro** |
| `jus-diagnose` | fast_extraction | ✅ irac_schema.json | ✅ irac_analyzer.py | **Operacional — pendente de registro** |

#### Shared

| Item | Conteúdo |
|---|---|
| `_shared/extraction-base.md` | Regra transversal injetada em todas as skills de extração |
| `_shared/proc-core.md` | Regras base para processo (presente mas uso não confirmado no loader) |

**Resumo quantitativo:** 15 skill dirs → 13 registradas + 2 operacionais pendentes. Apenas **5 de 15** têm scripts de validação funcionais. **10 dependem 100% do LLM** sem validação automatizada própria.

### 2.3 Módulo Operacional `apps/data-processing/`

| Submódulo | Arquivos | Funcionalidade Real |
|---|---|---|
| **CLI** (Typer) | `cli.py` | 5 comandos: `run`, `convert`, `clean`, `analyze`, `extract` |
| **Orchestrator** | `pipeline_runner.py` | PipelineRunner com 6 etapas: convert → clean → analyze → collect → validate → load |
| **Stage Router** | `stage_router.py` | Adapta cada etapa; conversão híbrida PyMuPDF + Gemini OCR para páginas escaneadas (< 150 chars = scanned) |
| **Extractor** | `extractor.py` | `DataExtractorApp` V1.1 — usa SkillDispatcher canônico, lê `var/input/md`, escreve `var/output/` |
| **Converters** | `converters/markdown_engine/`, `converters/gemini_ocr/` | Conversão PDF→Markdown com OCR Gemini para páginas escaneadas |
| **Cleaners** | `cleaners/clean_legal_docs.py` | `LegalDocCleaner` com batch processing |
| **Rule Analysis** | `rule_analysis/analisador_de_regras.py` | `GeradorDeRegras` — detecta frases repetidas (min_ocorrencias=2, min_comprimento=25) |
| **Collectors** | `collectors/collector_cad_obr/`, `collectors/collector_proc/` | 2 collectors com config YAML e main.py próprios |
| **Validation** | `validation/validation_cli.py`, `validation/validation_core.py` | Validação estruturada |
| **Loaders** | `loaders/index_registry.py`, `loaders/json_store.py`, `loaders/qdrant_loader.py` | Persistência e index registry |
| **Contracts** | `orchestrator/contracts.py` | `PipelineResult` |

**Dependência crítica do extractor:** `DataExtractorApp` instancia `DummyLLMClient` como cliente LLM — **não usa Gemini API real**. Isso significa que todas as extrações via `extract` CLI retornam dados dummy, não dados reais.

### 2.4 Infraestrutura Docker

**`infra/docker/docker-compose.yml`** — 2 serviços:

| Serviço | Porta | Volume | Perfil |
|---|---|---|---|
| **qdrant** (v1.16.0) | 6333 REST, 6334 gRPC | `qdrant_storage:/qdrant/storage` | default (sempre sobe) |
| **llama-cpp** (server) | 8080 | `${LLAMA_MODELS_PATH}:/models:ro` | `local-llm` (não sobe por default) |

**Qdrant config** (`infra/qdrant/config.yaml`):
- Distance: Cosine, Size: 768 (compatível com `all-MiniLM-L6-v2`)
- Coleção pré-definida: `decisoes` (payload: process_number, decision_type, doc_type, text_anchor)

**Env template** (`infra/env/.env.example`):
- `LLM_PROVIDER=gemini_api` (padrão)
- `LOCAL_LLM_ENABLED=false` (llama.cpp desabilitado por default)
- `QDRANT_URL=http://localhost:6333`, `QDRANT_COLLECTION=decisoes`
- `MEM0_ENABLED=true` mas `MEM0_API_KEY` vazio

### 2.5 Packages Compartilhados

| Package | Arquivos | Estado |
|---|---|---|
| `shared-llm` | `client.py`, `__init__.py` | ✅ `LLMClient` com Gemini API real, chamada local via requests, fallback dummy |
| `shared-schemas` | 6 schemas JSON | ✅ Sistema de anchoring (value + anchor_text + anchor_offset); schemas para proc-core-base, peticao-inicial, decisao_processo |
| `shared-core` | `.gitkeep` | ⚪ Vazio |
| `shared-legal` | `.gitkeep` | ⚪ Vazio |
| `shared-utils` | `.gitkeep` | ⚪ Vazio |

### 2.6 Dependências do Projeto (pyproject.toml)

- **Python >= 3.12**
- **22 dependências de runtime**: markitdown, google-genai, pdf2image, pdfplumber, pymupdf, typer, rich, jsonschema, langgraph, langchain-core, duckdb, qdrant-client, sentence-transformers, chardet, pypdf, reportlab, pytesseract, pillow, pandas, pyyaml, python-dotenv
- **3 dev dependencies**: pytest, ruff, types-pyyaml

**Nota crítica:** `mem0` e `turboquant` **NÃO estão listados como dependências**, mas são importados em `platform/memory-and-experiences/mem0_adapter.py`.

### 2.7 var/ — Estrutura de I/O

```
var/
├── input/{json, md, raw}/       # Entrada de dados
├── staging/                      # Staging de processamento
├── output/                       # Saídas finais (inclui staging/)
├── logs/                         # Logs de execução
├── cache/                        # Cache
├── artifacts/{index_registry.json} # Registry de índices
└── backups/                      # Backups
```

---

## 3. O que NÃO está implementado

### 3.1 Componentes Ausentes (declarados como obrigatórios no documento mestre)

| Componente | Documento Mestre | Estado Real | Impacto |
|---|---|---|---|
| **Mem0** (memória persistente) | "Camada obrigatória de memória episódica e persistente" | `mem0_adapter.py` existe mas importa `from mem0 import Memory` e `from turboquant import OnlineQuantizer` — **nenhuma das duas libs está em pyproject.toml** → código quebraria em execução | 🔴 Alto — código presente mas não executável |
| **TurboQuant** (eficiência contextual) | "Camada obrigatória de compressão e eficiência de representação contextual" | **Nenhum código, nenhum diretório, nenhuma referência** no projeto além do import fantasma no mem0_adapter | 🔴 Alto — zero implementação |
| **RLM** (inferência recursiva) | "Camada obrigatória de inferência/execução recursiva" | **Nenhum código, nenhum diretório, nenhuma referência** no projeto | 🔴 Alto — zero implementação |

### 3.2 Módulos Previstos mas Não Implementados

| Módulo Previsto | Estado Real | Observação |
|---|---|---|
| `apps/legal-research/` | ❌ Não existe | Responsabilidades de pesquisa jurídica sem contrapartida operacional. Agentes legados `agents/case-law-cli/` e `agents/law-cli/` congelados sem migração |
| `apps/legal-core/` | ❌ Não existe como diretório | Responsabilidades absorvidas de facto por `apps/data-processing/` |
| `apps/orchestrator-cli/` | ❌ Não existe como diretório | Responsabilidades absorvidas de facto por `apps/data-processing/` |

---

## 4. Legado Congelado

| Item | Caminho | Classificação |
|---|---|---|
| `agents/` (raiz) | 8 subdirs (case-law-cli, collector-cad_obr, collector-proc, compliance-cli, evidence-agent, firac-cli, law-cli, petition-cli) | **Legado congelado** — não fonte de verdade |
| `pipelines/` | `cad_obr.py`, `cad_obr/`, `ingest/` | **Legado** — pipeline antigo, não skill-centric, mas ainda contém código ativo (normalize, reconciler, pdf_convert) |
| `main.py` (raiz) | Entry point antigo | **Legado** — substituído por `apps/data-processing/main.py` |
| `scripts/` (raiz) | 15 scripts Python | **Misto** — alguns podem ser úteis (check_llama_ready.sh), outros são legado (genai_adapter.py, rag_service.py) |
| Diretórios diversos na raiz | `base_juridica/`, `data/`, `tools/`, `templates/`, `prompts/`, `policies/`, `mcp-server-cad_obr/`, `arq-js/`, `arq-md/`, `artifacts/`, `backup/`, `backups/`, `docs_iplt/`, `manual_User/`, `input/`, `logs/`, `outputs/` | **Legado ou não classificado** — fora da estrutura canônica |
| `.agent/` | ~1500 arquivos | **Tooling de terceiros** — não é parte do projeto |

---

## 5. Divergências entre Documentos e Código Real

### 5.1 Divergências Críticas

| # | O que diverge | Documento/Estado Real anterior diz | Código real mostra | Ação necessária |
|---|---|---|---|---|
| **D1** | Pipeline genérico | Runbook: "3 skills pendentes de criação" | ✅ **Já criadas, com SKILL.md completo, estrutura mínima e registradas** | Atualizar runbook |
| **D2** | `mem0_adapter.py` | Estado real (2026-04-05): "não existe" | ✅ **Existe** — mas importa `mem0` e `turboquant` que não estão em pyproject.toml | Atualizar estado real; adicionar dependências ou remover código quebrado |
| **D3** | TurboQuant | Documento mestre: "obrigatório" | ❌ Zero código — apenas import fantasma | Decidir: implementar ou remover do documento mestre |
| **D4** | RLM | Documento mestre: "obrigatório" | ❌ Zero código, zero diretório | Decidir: implementar ou remover do documento mestre |
| **D5** | `DataExtractorApp` usa LLM real | Implícito no estado real que extração funciona | ❌ Usa `DummyLLMClient` — **nunca chama Gemini API** | Corrigir extractor para usar LLMClient real com Gemini API |

### 5.2 Divergências Menores

| # | O que diverge | Documento/Estado Real anterior diz | Código real mostra |
|---|---|---|---|
| **D6** | `llama.cpp` como obrigatório | Documento mestre: parte da stack oficial | `.env.example`: `LOCAL_LLM_ENABLED=false` (opt-in) |
| **D7** | `platform/continuous-learning/` | "Expansão futura compatível" (Seção 9 do documento mestre) | `.gitkeep` apenas — consistente |
| **D8** | `platform/memory-and-experiences/` | "Expansão futura compatível" (Seção 9 do documento mestre) | `mem0_adapter.py` + `experience_rewriter.py` — **mais que stub**, mas não funcional |
| **D9** | Documentos antigos arquivados | Seção 11 do documento mestre: mover para `docs/archive/` | `docs/antigravity/`, `docs/implementation/`, `docs/quality/` ainda fora do arquivo |

---

## 6. Gaps Reais — Priorizados

### 🔴 Alta Prioridade

| Gap | Descrição | Impacto | Ação |
|---|---|---|---|
| **G1** | 2 skills operacionais sem registro (`jus-breve`, `jus-diagnose`) | Não são despacháveis pelo runtime | Adicionar ao `skill_registry.yaml` |
| **G2** | `mem0_adapter.py` importa libs não instaladas (`mem0`, `turboquant`) | Código quebraria em execução | Adicionar dependências ou remover código |
| **G3** | TurboQuant — zero código | Declarado como obrigatório, inexistente | Decidir: implementar ou remover do documento |
| **G4** | RLM — zero código | Declarado como obrigatório, inexistente | Decidir: implementar ou remover do documento |
| **G5** | `DataExtractorApp` usa `DummyLLMClient` | Extração real nunca funciona — retorna dados dummy | Integrar com `LLMClient` real e Gemini API |

### 🟡 Média Prioridade

| Gap | Descrição | Impacto | Ação |
|---|---|---|---|
| **G6** | 10 de 15 skills sem scripts de validação | Sem prova automatizada de funcionamento | Criar scripts de validação por skill |
| **G7** | Testes sem evidência de execução recente | Confiabilidade não verificável | Executar pytest e registrar resultado |
| **G8** | Runbook desatualizado (pipeline genérico já criado) | Instruções incorretas para novos operadores | Atualizar runbook |

### 🟢 Baixa Prioridade

| Gap | Descrição | Impacto | Ação |
|---|---|---|---|
| **G9** | `legal-research` sem implementação | Não é frente ativa atual | Manter como previsto |
| **G10** | Scripts avulsos na raiz | Fora do modelo skill-centric | Classificar um a um: útil, legado ou arquivar |
| **G11** | Documentos antigos fora do arquivo | Poluição visual do docs/ | Mover para `docs/archive/` |

---

## 7. Matriz de Alinhamento: Documento Mestre vs Estado Real

| Seção do Documento Mestre | Declarado | Estado Real | Alinhado? |
|---|---|---|---|
| Seção 1: Visão arquitetural (skill-centric) | Runtime + skills + apps + packages + infra | ✅ Implementado | ✅ Sim |
| Seção 2: Princípios (skill como unidade) | Skill = unidade canônica | ✅ 15 skills no disco | ✅ Sim |
| Seção 3: Estrutura lógica do repositório | apps/, platform/, packages/, var/, infra/ | ✅ Presentes | ✅ Sim |
| Seção 4: Separação de responsabilidades | apps/ vs platform/ vs packages/ | ✅ Respeitada | ✅ Sim |
| Seção 5: Módulos funcionais (4 apps previstos) | data-processing, legal-research, legal-core, orchestrator-cli | ⚠️ Apenas data-processing existe; legal-core e orchestrator-cli absorvidos; legal-research ausente | ⚠️ Parcial |
| Seção 6: Runtime canônico | dispatcher, bundle_loader, registries | ✅ Todos funcionais | ✅ Sim |
| Seção 7: Skills canônicas | platform/skills/ com SKILL.md + assets + references + scripts | ✅ 15 skills com estrutura completa | ✅ Sim |
| Seção 8: Pipeline documental base (3 skills genéricas) | pdf-to-md, md-clean-markdown, md-frontmatter-yaml | ✅ Criadas e registradas | ✅ Sim |
| Seção 9: Camada jurídica especializada | Acima da base genérica | ✅ 10 extr-* + 2 jus-* | ✅ Sim |
| Seção 10: Camada de memória (Mem0) | Obrigatória | ⚠️ Adapter existe mas não funcional | ❌ Não |
| Seção 11: Camada de eficiência (TurboQuant) | Obrigatória | ❌ Zero código | ❌ Não |
| Seção 12: Camada de inferência (RLM) | Obrigatória | ❌ Zero código | ❌ Não |
| Seção 13: Stack e infra (Docker, Qdrant, Gemini, llama.cpp) | Obrigatórios | ✅ Docker + Qdrant configurados; Gemini client funcional; llama.cpp opt-in | ✅ Sim (com ressalva) |
| Seção 15: Legado | agents/, pipelines/ fora do caminho | ✅ Classificados e congelados | ✅ Sim |

---

## 8. Conclusão

### a) Estado Atual Implantado

O projeto possui **runtime canônico funcional**, **15 skills** (13 registradas + 2 pendentes de registro), **módulo data-processing operacional** com pipeline de 6 etapas, **infraestrutura Docker configurada** e **packages compartilhados funcionais** (shared-llm, shared-schemas). O pipeline documental genérico está criado e registrado. A extração real via LLM não funciona porque o `DataExtractorApp` usa `DummyLLMClient`.

### b) Arquitetura Alvo Vigente

O documento mestre define uma arquitetura skill-centric com **Mem0**, **TurboQuant** e **RLM** como componentes obrigatórios. O código real implementa o runtime, as skills e o pipeline genérico, mas **não implementa Mem0 funcional, TurboQuant ou RLM**.

### c) Gaps Reais

Os gaps reais entre o estado implantado e a arquitetura alvo são:

1. **Mem0** — código existe mas não é executável (imports quebrados)
2. **TurboQuant** — zero código
3. **RLM** — zero código
4. **2 skills não registradas** — jus-breve, jus-diagnose
5. **Extração real não funcional** — DummyLLMClient ao invés de Gemini API
6. **10/15 skills sem validação automatizada**
7. **Documentos operacionais desatualizados** (runbook, estado real anterior)

---

## 9. Evidências com Caminhos Exatos

### Runtime e Registry
```
✅ platform/skill-runtime/skill_dispatcher.py        — dispatcher canônico funcional
✅ platform/skill-runtime/bundle_loader.py           — bundle loader funcional
✅ platform/skill-runtime/skill_registry.yaml         — 13 skills registradas
✅ platform/skill-runtime/llm_registry.yaml           — 4 profiles + 2 execution classes
```

### Skills Registradas (13)
```
✅ platform/skills/extr-cabecalho-processo/SKILL.md   → fast_extraction
✅ platform/skills/extr-contestacao-processo/SKILL.md → high_reasoning
✅ platform/skills/extr-contrato-social/SKILL.md      → high_reasoning
✅ platform/skills/extr-decisao-processo/SKILL.md     → large_context
✅ platform/skills/extr-escritura-hipotecaria/SKILL.md → high_reasoning
✅ platform/skills/extr-escritura-imovel/SKILL.md     → large_context
✅ platform/skills/extr-mandato-processo/SKILL.md     → high_reasoning
✅ platform/skills/extr-peticao-processo/SKILL.md     → high_reasoning
✅ platform/skills/extr-processo/SKILL.md             → large_context
✅ platform/skills/extr-procuracao/SKILL.md           → fast_extraction
✅ platform/skills/pdf-to-md/SKILL.md                 → local_preprocessing
✅ platform/skills/md-clean-markdown/SKILL.md         → local_preprocessing
✅ platform/skills/md-frontmatter-yaml/SKILL.md       → local_preprocessing
```

### Skills Não Registradas — Operacionais (2)
```
⚠️  platform/skills/jus-breve/SKILL.md                → operacional (FIRAC), pendente de registro
⚠️  platform/skills/jus-diagnose/SKILL.md             → operacional (IRAC), pendente de registro
```

### Módulo Operacional
```
✅ apps/data-processing/src/data_processing/cli.py     — CLI Typer com 5 comandos
✅ apps/data-processing/src/data_processing/orchestrator/pipeline_runner.py  — 6-stage pipeline
✅ apps/data-processing/src/data_processing/orchestrator/stage_router.py     — stage routing
✅ apps/data-processing/src/data_processing/extractor.py                     — DataExtractorApp V1.1
✅ apps/data-processing/src/data_processing/converters/                      — markdown_engine + gemini_ocr
✅ apps/data-processing/src/data_processing/cleaners/                        — LegalDocCleaner
✅ apps/data-processing/src/data_processing/collectors/                      — cad_obr + proc
✅ apps/data-processing/src/data_processing/loaders/                         — index_registry + json_store + qdrant
```

### Infraestrutura
```
✅ infra/docker/docker-compose.yml                     — Qdrant + llama.cpp
✅ infra/qdrant/config.yaml                            — Cosine, 768 dims, coleção decisoes
✅ infra/env/.env.example                              — template de variáveis
```

### Packages
```
✅ packages/shared-llm/client.py                       — LLMClient (Gemini + local + dummy)
✅ packages/shared-schemas/                             — 6 schemas com anchoring
   packages/shared-core/                               — .gitkeep
   packages/shared-legal/                              — .gitkeep
   packages/shared-utils/                              — .gitkeep
```

### Componentes Não Funcionais
```
⚠️  platform/memory-and-experiences/mem0_adapter.py    — importa mem0 + turboquant (não instalados)
⚠️  platform/memory-and-experiences/experience_rewriter.py — stub trivial (4 linhas)
❌  TurboQuant — nenhum código encontrado
❌  RLM — nenhum código encontrado
```

### Legado Congelado
```
⚠️  agents/ (8 subdirs)                                — legado congelado
⚠️  pipelines/ (cad_obr.py + cad_obr/ + ingest/)       — legado parcial
⚠️  main.py (raiz)                                     — entry point legado
```
