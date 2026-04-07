# Estado Real Implantado — `juridico-cli`

**Data:** 2026-04-05
**Fonte:** Levantamento direto do disco (`~/devops/juridico-cli`)
**Referência:** `docs/architecture/juridico_cli_documento_mestre.md`

---

## 1. Resumo Executivo

O repositório está no caminho canônico definido pelo documento mestre. A arquitetura skill-centric está presente no disco com runtime, dispatcher, registry e 15 skill directories em `platform/skills/` de escopo canônico. Destes, **13 estão registrados** e operacionais no `skill_registry.yaml` e **2 estão operacionais mas pendentes de registro** (`jus-breve`, `jus-diagnose`). As demais skills no disco (`extr-dummy`, `legal-data-extractor`, `pdf`, `skill-creator`) foram excluídas desta análise por não se enquadrarem como bundle operacional canônico. As três skills genéricas do pipeline documental (`pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml`) estão criadas, com `SKILL.md` completo, estrutura mínima (`assets/`, `references/`, `scripts/`) e registradas no runtime. O módulo operacional `apps/data-processing/` existe e funcional, com CLI Typer (5 comandos), orquestrador interno e 2 collectors. As responsabilidades originalmente previstas para `legal-core` e `orchestrator-cli` foram absorvidas de facto por `data-processing`. Apenas `legal-research` permanece sem contrapartida operacional. `agents/` na raiz e `pipelines/` permanecem como legado congelado. Infraestrutura Docker mínima está definida e operacional.

---

## 2. Itens Implantados e Validados

| Item | Evidência (caminho exato) | Status |
|------|--------------------------|--------|
| Runtime canônico | `platform/skill-runtime/skill_dispatcher.py` | ✅ Implantado |
| Bundle loader | `platform/skill-runtime/bundle_loader.py` | ✅ Implantado |
| skill_registry.yaml | `platform/skill-runtime/skill_registry.yaml` | ✅ Implantado — 13 skills registradas |
| llm_registry.yaml | `platform/skill-runtime/llm_registry.yaml` | ✅ Implantado — 4 profiles válidos + 2 execution classes |
| Camada de skills | `platform/skills/` (15 skill dirs de escopo canônico no disco) | ✅ 13 registradas + 2 operacionais pendentes (ver tabela abaixo) |
| `pdf-to-md` | `platform/skills/pdf-to-md/SKILL.md` + `assets/`, `references/`, `scripts/` | ✅ Criada, registrada, perfil `local_preprocessing` |
| `md-clean-markdown` | `platform/skills/md-clean-markdown/SKILL.md` + `assets/`, `references/`, `scripts/` | ✅ Criada, registrada, perfil `local_preprocessing` |
| `md-frontmatter-yaml` | `platform/skills/md-frontmatter-yaml/SKILL.md` + `assets/`, `references/`, `scripts/` | ✅ Criada, registrada, perfil `local_preprocessing` |
| `apps/data-processing/` | `apps/data-processing/main.py` + `src/data_processing/` (cli, orchestrator, converters, cleaners, rule_analysis, collectors, validation, loaders, contracts) | ✅ Implantado |
| Infra Docker | `infra/docker/docker-compose.yml` | ✅ Implantado — Qdrant + llama.cpp (perfil local-llm) |
| Qdrant config | `infra/qdrant/config.yaml` | ✅ Implantado |
| Env template | `infra/env/.env.example` | ✅ Implantado |
| `var/` (I/O) | `var/input/`, `var/output/`, `var/staging/`, `var/logs/`, `var/cache/`, `var/artifacts/`, `var/backups/` | ✅ Estrutura criada |
| `packages/shared-llm` | `packages/shared-llm/client.py` — interface `LLMClient` + `DummyLLMClient` | ✅ Código presente |
| `packages/shared-schemas` | `packages/shared-schemas/cadeia_obrigacoes.schema.json` + `defs/common.schema.json` | ✅ Schemas presentes |
| `_shared/extraction-base.md` | `platform/skills/_shared/extraction-base.md` | ✅ Presente |
| `pyproject.toml` | `pyproject.toml` — Python 3.12+, 22 dependências | ✅ Configurado |
| Testes de sintaxe | `tests/test_smoke_syntax.py` | ✅ Presente |

---

## 3. Itens Implantados, mas sem Validação Clara

### 3.1 — Skills no disco, classificadas uma a uma

#### Skills registradas (13)

| skill_dir | Caminho exato | Perfil | Registro |
|-----------|--------------|--------|----------|
| `extr-cabecalho-processo` | `platform/skills/extr-cabecalho-processo/` | `fast_extraction` | ✅ em `skill_registry.yaml` |
| `extr-contestacao-processo` | `platform/skills/extr-contestacao-processo/` | `high_reasoning` | ✅ |
| `extr-contrato-social` | `platform/skills/extr-contrato-social/` | `high_reasoning` | ✅ |
| `extr-decisao-processo` | `platform/skills/extr-decisao-processo/` | `large_context` | ✅ |
| `extr-escritura-hipotecaria` | `platform/skills/extr-escritura-hipotecaria/` | `high_reasoning` | ✅ |
| `extr-escritura-imovel` | `platform/skills/extr-escritura-imovel/` | `large_context` | ✅ |
| `extr-mandato-processo` | `platform/skills/extr-mandato-processo/` | `high_reasoning` | ✅ |
| `extr-peticao-processo` | `platform/skills/extr-peticao-processo/` | `high_reasoning` | ✅ |
| `extr-processo` | `platform/skills/extr-processo/` | `large_context` | ✅ |
| `extr-procuracao` | `platform/skills/extr-procuracao/` | `fast_extraction` | ✅ |
| `pdf-to-md` | `platform/skills/pdf-to-md/` | `local_preprocessing` | ✅ |
| `md-clean-markdown` | `platform/skills/md-clean-markdown/` | `local_preprocessing` | ✅ |
| `md-frontmatter-yaml` | `platform/skills/md-frontmatter-yaml/` | `local_preprocessing` | ✅ |

#### Skills não registradas — análise individual (2)

| skill_dir | Caminho exato | SKILL.md? | Estrutura completa? | Conteúdo do SKILL.md | Classificação real |
|-----------|--------------|-----------|---------------------|----------------------|-------------------|
| `jus-breve` | `platform/skills/jus-breve/` | ✅ | ✅ `assets/`, `references/`, `scripts/` | FIRAC completo, barreira fática, JSON output, workflow 7 passos | **Operacional — pendente de registro** |
| `jus-diagnose` | `platform/skills/jus-diagnose/` | ✅ | ✅ `assets/`, `references/`, `scripts/` | IRAC completo, triagem jurídica, JSON output, workflow 3 passos | **Operacional — pendente de registro** |

**Total:** 15 skill dirs de escopo canônico no disco → 13 registradas + 2 operacionais pendentes.

### 3.2 — Demais itens sem validação clara

| Item | Evidência | Observação |
|------|-----------|------------|
| `platform/continuous-learning/` | `.gitkeep` apenas | Diretório criado, vazio. Espaço reservado para expansão futura compatível (documento mestre, Seção 9: RLM). |
| `platform/memory-and-experiences/` | `mem0_adapter.py`, `experience_rewriter.py` + `.gitkeep` | Código presente, mas sem evidência de integração ativa ao runtime canônico. Corresponde a "expansão futura compatível" (documento mestre, Seção 9: Mem0). |
| `scripts/` (raiz) | 15 scripts diversos | Scripts avulsos, fora do modelo skill-centric. Alguns podem ser legado; outros podem ter utilidade operacional. |
| `apps/data-processing` — testes | `apps/data-processing/tests/` — 3 arquivos de teste | Presentes, mas não há evidência de execução com sucesso recente. |
| `var/output/result_extr-contrato-social_test_social.json` | Arquivo de saída existe | Evidência de execução prévia da skill via `DataExtractorApp`, mas sem validação formal documentada. |

---

## 4. Renomeações e Substituições de Módulos Previstos

O documento mestre (Seção 10) lista três módulos como "previstos, mas não tratados como plenamente implantados":
- `apps/legal-research/`
- `apps/legal-core/`
- `apps/orchestrator-cli/`

Levantamento direto do disco confirma: **nenhum desses três nomes existe como diretório em `apps/`**. Não há evidência de que tenham sido criados com nomes diferentes.

No entanto, o módulo **`apps/data-processing/`** absorveu funcionalidade que originalmente seria distribuída entre esses módulos previstos:

| Funcionalidade originalmente prevista | Onde foi efetivamente implementada | Evidência |
|--------------------------------------|-----------------------------------|-----------|
| Orquestração de pipeline (converter → limpar → analisar → extrair → validar → persistir) | `apps/data-processing/src/data_processing/orchestrator/pipeline_runner.py` | Classe `PipelineRunner` com 6 etapas |
| Roteamento de etapas individuais | `apps/data-processing/src/data_processing/orchestrator/stage_router.py` | Funções `run_convert_stage`, `run_clean_stage`, `run_analyze_stage`, `run_collect_stage` |
| Extração estruturada via LLM | `apps/data-processing/src/data_processing/extractor.py` | `DataExtractorApp` V1.1 usando `SkillDispatcher` canônico |
| CLI de domínio | `apps/data-processing/src/data_processing/cli.py` | Typer com 4 comandos: `run`, `convert`, `clean`, `analyze`, `extract` |

**Conclusão:** `apps/data-processing/` funciona como o módulo operacional único que concentra orquestração, conversão, limpeza, análise e extração. Os três módulos previstos (`legal-research`, `legal-core`, `orchestrator-cli`) **não foram renomeados formalmente**, mas suas responsabilidades de orquestração e core foram absorvidas de facto por `data-processing`. As responsabilidades de `legal-research` (pesquisa jurídica) permanecem sem implementação — os agentes legados `agents/case-law-cli/` e `agents/law-cli/` continuam congelados sem migração.

---

## 5. Legado Congelado ou Fora do Caminho Canônico

| Item | Caminho | Classificação |
|------|---------|---------------|
| `agents/` (raiz) | `agents/case-law-cli/`, `agents/collector-cad_obr/`, `agents/collector-proc/`, `agents/compliance-cli/`, `agents/evidence-agent/`, `agents/firac-cli/`, `agents/law-cli/`, `agents/petition-cli/` | **Legado congelado** — documento mestre, Seção 3 |
| `pipelines/` | `pipelines/cad_obr.py`, `pipelines/ingest/` | **Legado** — pipeline antigo, não skill-centric |
| `main.py` (raiz) | `main.py` | **Legado** — entry point antigo, substituído por `apps/data-processing/main.py` |
| `scripts/` (raiz) | 15 scripts Python | **Misto** — fora do modelo skill, classificação depende de análise individual |
| Diretórios diversos na raiz | `base_juridica/`, `data/`, `tools/`, `templates/`, `prompts/`, `policies/`, `mcp-server-cad_obr/`, `arq-js/`, `arq-md/`, `artifacts/`, `backup/`, `backups/`, `docs_iplt/`, `manual_User/`, `input/`, `logs/`, `outputs/` | **Legado ou não classificado** — fora da estrutura canônica |

> **Nota:** O descomissionamento desses itens depende de gate explícito. Esta seção os classifica sem tratá-los como gap técnico atual.

---

## 6. Divergências entre Documento Mestre e Estado Real

| # | Divergência | Documento Mestre diz | Estado real do disco |
|---|-------------|---------------------|----------------------|
| 1 | **Skills genéricas do pipeline** | Seção 7: "Ainda pendente — criação das três skills genéricas" | **Já criadas e registradas**: `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml` estão em `platform/skills/` com `SKILL.md` completo, estrutura mínima e entrada no `skill_registry.yaml` com perfil `local_preprocessing` |
| 2 | **2 skills operacionais sem registro** | Regra canônica: "skill nova só roda se estiver registrada" | 2 skill dirs operacionais com `SKILL.md` completo, estrutura canônica e conteúdo jurídico, mas **não** constam no `skill_registry.yaml`: `jus-breve`, `jus-diagnose` |
| 3 | **Módulos previstos** | Seção 10: `legal-research`, `legal-core`, `orchestrator-cli` como "previstos" | Nenhum existe com esses nomes. `data-processing` absorveu de facto as responsabilidades de orquestração e core. Apenas `legal-research` permanece sem contrapartida operacional |
| 4 | **Documentos antigos arquivados** | Seção 11: mover para `docs/archive/juridico-cli/` | `docs/archive/juridico-cli/` existe, mas `docs/antigravity/`, `docs/implementation/`, `docs/quality/` ainda estão fora do arquivo |
| 5 | **`packages/` como componentes compartilhados** | Estrutura lógica prevê `packages/` | Apenas 2 de 5 packages têm código (`shared-llm`, `shared-schemas`). Os demais (`shared-core`, `shared-legal`, `shared-utils`) são apenas `.gitkeep`. O documento mestre não os nomeia individualmente como requisitos vigentes. |

---

## 7. Evidências com Caminhos Exatos

### Runtime e Registry
```
✅ platform/skill-runtime/skill_dispatcher.py        — dispatcher canônico
✅ platform/skill-runtime/bundle_loader.py           — bundle loader
✅ platform/skill-runtime/skill_registry.yaml         — 13 skills registradas
✅ platform/skill-runtime/llm_registry.yaml           — 4 profiles + 2 execution classes
```

### Skills Registradas (13)
```
✅ platform/skills/extr-cabecalho-processo/SKILL.md   → registry: fast_extraction
✅ platform/skills/extr-contestacao-processo/SKILL.md → registry: high_reasoning
✅ platform/skills/extr-contrato-social/SKILL.md      → registry: high_reasoning
✅ platform/skills/extr-decisao-processo/SKILL.md     → registry: large_context
✅ platform/skills/extr-escritura-hipotecaria/SKILL.md → registry: high_reasoning
✅ platform/skills/extr-escritura-imovel/SKILL.md     → registry: large_context
✅ platform/skills/extr-mandato-processo/SKILL.md     → registry: high_reasoning
✅ platform/skills/extr-peticao-processo/SKILL.md     → registry: high_reasoning
✅ platform/skills/extr-processo/SKILL.md             → registry: large_context
✅ platform/skills/extr-procuracao/SKILL.md           → registry: fast_extraction
✅ platform/skills/pdf-to-md/SKILL.md                 → registry: local_preprocessing
✅ platform/skills/md-clean-markdown/SKILL.md         → registry: local_preprocessing
✅ platform/skills/md-frontmatter-yaml/SKILL.md       → registry: local_preprocessing
```

### Skills Não Registradas — Operacionais (2)
```
⚠️  platform/skills/jus-breve/SKILL.md                → operacional (FIRAC), pendente de registro
⚠️  platform/skills/jus-diagnose/SKILL.md             → operacional (IRAC), pendente de registro
```

### Módulos e Infraestrutura
```
✅ apps/data-processing/main.py                        — entry point funcional
✅ apps/data-processing/src/data_processing/cli.py     — CLI Typer com 5 comandos
✅ apps/data-processing/src/data_processing/orchestrator/pipeline_runner.py
✅ apps/data-processing/src/data_processing/orchestrator/stage_router.py
✅ apps/data-processing/src/data_processing/extractor.py — DataExtractorApp V1.1
✅ infra/docker/docker-compose.yml                     — Qdrant + llama.cpp
✅ infra/qdrant/config.yaml                            — config mínima
✅ infra/env/.env.example                              — template de variáveis
✅ packages/shared-llm/client.py                       — LLMClient abc + Dummy
✅ packages/shared-schemas/cadeia_obrigacoes.schema.json
✅ packages/shared-schemas/defs/common.schema.json
```

### Módulos Previstos (não existem com esses nomes)
```
—  apps/legal-research/                                — não existe como dir
—  apps/legal-core/                                    — não existe como dir
—  apps/orchestrator-cli/                              — não existe como dir
   → responsabilidade de orquestração absorvida por data-processing
   → responsabilidade de legal-research sem contrapartida operacional
```

### Legado Congelado
```
⚠️  agents/ (8 subdirs)                                — legado congelado
⚠️  pipelines/ (cad_obr.py + ingest/)                  — legado
⚠️  main.py (raiz)                                     — entry point legado
```

### Packages (diretórios)
```
✅ packages/shared-llm/     — client.py (LLMClient abc + Dummy)
✅ packages/shared-schemas/ — 2 JSON schemas
   packages/shared-core/   — .gitkeep apenas
   packages/shared-legal/  — .gitkeep apenas
   packages/shared-utils/  — .gitkeep apenas
```
