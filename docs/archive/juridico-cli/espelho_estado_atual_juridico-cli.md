> [!NOTE]
> **DOCUMENTO OPERACIONAL — ESPELHO DO ESTADO ATUAL**
> Reflete o estado real do repositório em 2026-04-04. Atualizar sempre que houver renomeação estrutural, adição de módulo canônico ou mudança de status do legado.
> **Fonte canônica de arquitetura:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Espelho do Estado Atual — `juridico-cli`

**Data:** 2026-04-04 (atualizado Task 12)
**Modelo arquitetural vigente:** Monorepo híbrido centrado em skills
**Runtime:** `platform/skill-runtime/` com `skill_dispatcher.py`
**LLMs oficiais:** Gemini via API · llama.cpp local em Docker Desktop
**Docker local:** Docker Desktop (Windows + WSL2)
**Stack mínima canônica:** 100% operacional e testada

---

## 1. Estrutura canônica — o que existe hoje

```
juridico-cli/
├── apps/
│   └── data-processing/          ← IMPLEMENTADO (único app existente)
│       ├── src/data_processing/
│       │   ├── cli.py             ← CLI canônica
│       │   ├── collectors/        ← collector_cad_obr, collector_proc
│       │   ├── converters/        ← gemini_ocr, markdown_engine
│       │   ├── cleaners/          ← clean_legal_docs
│       │   ├── rule_analysis/     ← analisador_de_regras
│       │   ├── validation/        ← contract_validation, output_checks
│       │   ├── loaders/           ← qdrant_loader, json_store, index_registry
│       │   ├── orchestrator/      ← pipeline_runner, stage_router, contracts
│       │   └── extractor.py
│       └── tests/
├── platform/
│   ├── skill-runtime/             ← IMPLEMENTADO E CANÔNICO
│   │   ├── skill_dispatcher.py
│   │   ├── bundle_loader.py
│   │   ├── skill_registry.yaml
│   │   └── llm_registry.yaml
│   ├── skills/                    ← IMPLEMENTADO (17 bundles)
│   │   ├── _shared/               ← extraction-base.md, proc-core.md
│   │   ├── extr-cabecalho-processo/
│   │   ├── extr-contestacao-processo/
│   │   ├── extr-contrato-social/
│   │   ├── extr-decisao-processo/
│   │   ├── extr-dummy/
│   │   ├── extr-escritura-hipotecaria/
│   │   ├── extr-escritura-imovel/
│   │   ├── extr-mandato-processo/
│   │   ├── extr-peticao-processo/
│   │   ├── extr-processo/
│   │   ├── extr-procuracao/
│   │   ├── jus-breve/
│   │   ├── jus-diagnose/
│   │   ├── legal-data-extractor/
│   │   ├── pdf/
│   │   └── skill-creator/
│   ├── memory-and-experiences/    ← diretório criado, sem conteúdo operacional
│   └── continuous-learning/       ← diretório criado, sem conteúdo operacional
├── packages/
│   ├── shared-core/
│   ├── shared-legal/
│   ├── shared-llm/
│   ├── shared-schemas/
│   └── shared-utils/
├── var/                           ← I/O operacional e runtime
│   ├── input/
│   ├── staging/
│   ├── output/
│   ├── logs/
│   ├── artifacts/
│   ├── cache/
│   └── backups/
├── infra/                         ← IMPLEMENTADO (Task 9)
│   ├── docker/
│   │   └── docker-compose.yml     ← stack Qdrant + llama.cpp para Docker Desktop
│   ├── qdrant/
│   │   └── config.yaml            ← configuração mínima do Qdrant
│   └── env/
│       └── .env.example           ← template de variáveis (copiar para .env)
└── docs/
    ├── architecture/              ← canônico v2 único
    ├── antigravity/juridico-cli/  ← auxiliares e históricos (marcados)
    └── runbooks/                  ← runbook operacional mínimo
```

---

## 2. Módulos previstos no canônico — ainda não implementados

| Módulo | Status | Observação |
|---|---|---|
| `apps/legal-research/` | Não criado | Previsto no canônico v2, seção 4 |
| `apps/legal-core/` | Não criado | Previsto no canônico v2, seção 4 |
| `apps/orchestrator-cli/` | Não criado | Previsto no canônico v2, seção 4 |
| `infra/` | **Implementado** | Task 9 — `infra/docker/`, `infra/qdrant/`, `infra/env/` |

Esses módulos são o destino da migração em andamento. Não criar sem seguir a fonte canônica.

---

## 3. Runtime vigente

| Arquivo | Função |
|---|---|
| `platform/skill-runtime/skill_dispatcher.py` | Despacha tarefa para a skill correta com o LLM adequado — `SkillDispatcher.dispatch()` operacional |
| `platform/skill-runtime/bundle_loader.py` | Carrega `SKILL.md` + regras compartilhadas de `_shared/` |
| `platform/skill-runtime/skill_registry.yaml` | Registro canônico de skills e seus caminhos |
| `platform/skill-runtime/llm_registry.yaml` | Registro canônico de providers, classes de execução e perfis |

**Convenção de nomenclatura:**
- Usar `skill_dispatcher.py` — nunca `orchestrator.py` como nome canônico
- Usar `platform/skill-runtime/` — nunca `platform/agent-core/`

---

## 4. Camada de skills vigente

Cada bundle em `platform/skills/<nome>/` contém:

| Arquivo | Propósito |
|---|---|
| `SKILL.md` | Instrução canônica de extração (sistema LLM prompt) |
| `assets/<nome>.schema.json` | Schema autoritativo do bundle |
| `assets/<nome>.consolidated.schema.json` | Schema consolidado (gerado) |
| `references/dicionario_campos.md` | Dicionário de campos |
| `scripts/validate_output.py` | Validação de output |

`SKILL.md` é o único ponto de entrada de instrução. Não há dependência de `agents/*.md` nos bundles `extr-*`.

Regras transversais compartilhadas ficam em `platform/skills/_shared/`:
- `extraction-base.md` — injetada antes de toda SKILL.md pelo `bundle_loader`
- `proc-core.md` — regras de extração de documentos processuais

---

## 5. Stack de LLM oficial

| Camada | Tecnologia | Deployment |
|---|---|---|
| API remota | Gemini (gemini-2.5-flash, gemini-2.5-pro) | External API |
| Local | llama.cpp (llama-3.2-3b-instruct) | Docker Desktop |
| Vector store | Qdrant | Docker Desktop (local) |

Perfis definidos em `llm_registry.yaml`: `fast_extraction`, `high_reasoning`, `large_context`, `local_preprocessing`.

**Docker local = Docker Desktop (Windows + WSL2).** Não usar Docker Engine puro como referência.

Referências a Haiku, Sonnet, Ollama, GPT-*, `???` são antigas e devem ser tratadas como incorretas.

---

## 6. Legado congelado

Estes diretórios existem no repositório mas **não são autoridade para novos desenvolvimentos**. Foram congelados e aguardam gate de Fase 4 para descomissionamento.

| Diretório | Conteúdo | Status |
|---|---|---|
| `agents/case-law-cli/` | Pesquisa de jurisprudência (legado) | Congelado |
| `agents/collector-cad_obr/` | Coleta CAD-OBR (legado) | Congelado |
| `agents/collector-proc/` | Coleta processual (legado) | Congelado |
| `agents/compliance-cli/` | Compliance (legado) | Congelado |
| `agents/evidence-agent/` | Evidência (legado) | Congelado |
| `agents/firac-cli/` | FIRAC (legado) | Congelado |
| `agents/law-cli/` | Base legal (legado) | Congelado |
| `agents/petition-cli/` | Petições (legado) | Congelado |
| `pipelines/cad_obr/` | Pipeline CAD-OBR (legado) | Congelado |
| `pipelines/ingest/` | Ingestão PDF→MD→RAG (parcialmente ativo) | Congelado |

> **Fase 4 não autorizada.** Só remover/descomissionar com gate explícito do usuário: "autorizo Fase 4".

---

## 7. Documentação vigente

| Documento | Tipo | Propósito |
|---|---|---|
| `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md` | **CANÔNICO** | Fonte única de verdade arquitetural |
| `docs/runbooks/runbook_operacional_minimo.md` | Auxiliar operacional | Orientação rápida para novos colaboradores |
| `docs/antigravity/juridico-cli/data_processing_pipelines.md` | Auxiliar operacional | Estágios dos pipelines de processamento |
| `docs/antigravity/juridico-cli/ Classificação_de_Schemas—juridico-cli.md` | Auxiliar operacional | Classificação e localização de schemas |
| `docs/antigravity/juridico-cli/validacao_operacional_real.md` | Auxiliar operacional | Smoke tests reais por componente (Qdrant, Gemini, dispatcher, llama.cpp) |
| `CLAUDE.md` | Instrução de agente | Comandos, regras e contexto para Claude Code |

Todos os demais documentos em `docs/antigravity/juridico-cli/` estão marcados como **HISTÓRICO** ou **AUXILIAR** com aviso explícito no topo.

---

## 8. Itens concluídos nas etapas de migração

| Etapa | O que foi feito | Status |
|---|---|---|
| Runtime skill-centric | `platform/skill-runtime/` é o diretório canônico; `skill_dispatcher.py` é o arquivo de despacho | ✓ Concluído |
| Alinhamento LLM | `llm_registry.yaml` reescrito com Gemini API + llama.cpp Docker; aliases antigos removidos | ✓ Concluído |
| SKILL.md como instrução canônica | `bundle_loader.py` carrega apenas `SKILL.md`; sem dependência de `agents/*.md` | ✓ Concluído |
| Remoção dos `agents/*.md` nos bundles `extr-*` | 10 arquivos `extr-*-agent.md` e seus diretórios `agents/` removidos de `platform/skills/` | ✓ Concluído |
| Governança documental | Única fonte canônica declarada; 7 docs marcados como histórico, 3 como auxiliar operacional | ✓ Concluído |
| `skill_dispatcher.py` operacional | 5 bugs corrigidos; `apps/data-processing/extractor.py` integrado via `SkillDispatcher` | ✓ Concluído |
| Infraestrutura mínima canônica (`infra/`) | `docker-compose.yml` (Qdrant + llama.cpp), `config.yaml`, `.env.example` criados para Docker Desktop | ✓ Concluído |
| Validação operacional (`validacao_operacional_real.md`) | Qdrant testado (v1.16.0), Gemini API testada, dispatcher 10/10 skills, llama.cpp bloqueado (sem .gguf) | ✓ Concluído |
| Pre-flight llama.cpp (`scripts/check_llama_ready.sh`) | Script detecta: .env ausente, placeholder, .gguf faltando, Docker offline. 4 cenários testados. | ✓ Concluído |
| llama.cpp ativado e testado (Task 12) | `/health` → `{"status":"ok"}` · `/v1/models` → `Llama-3.2-3B-Instruct-Q4_K_L.gguf` · stack mínima 100% operacional | ✓ Concluído |
