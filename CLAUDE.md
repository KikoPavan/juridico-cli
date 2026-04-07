# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🌐 Language & Communication Rules

- **Responda exclusivamente em português do Brasil (pt-BR)**, independentemente do idioma do prompt.
- **Se o prompt estiver em outro idioma**, interprete internamente conforme necessário, mas mantenha a resposta em pt-BR.
- **Se o usuário solicitar uma tradução**, forneça a tradução pedida, mantendo em pt-BR todas as instruções, explicações e contextualizações adicionais.
- **Escreva todo o código em inglês**, incluindo nomes de variáveis, funções, classes, schemas de banco de dados, chaves de configuração e comentários.
- **Escreva mensagens de commit em inglês**, seguindo o padrão Conventional Commits.
---

## Common Commands

All commands use `uv run`. Python 3.12 is required (`.python-version` enforces this).

### Install dependencies

```bash
uv sync
```

### Lint

```bash
uv run ruff check .
uv run ruff format .
```

### Tests

```bash
uv run pytest
```

### Run apps/data-processing (canonical — unified pipeline)

> CLI canônica: `apps/data-processing/src/data_processing/cli.py`
> `apps/data-processing/main.py` é apenas um thin wrapper sobre essa CLI — não adicione lógica nele.

```bash
# Full pipeline: clean → analyze → collect → validate → load
uv run python apps/data-processing/src/data_processing/cli.py run \
  --input <dir_md> --collector <cad_obr|proc>

# Isolated clean stage
uv run python apps/data-processing/src/data_processing/cli.py clean \
  --input <dir_md>

# Isolated rule analysis stage
uv run python apps/data-processing/src/data_processing/cli.py analyze \
  --input <dir_md>

# Collectors directly (new location)
uv run python3 apps/data-processing/src/data_processing/collectors/collector_cad_obr/main.py
uv run python3 apps/data-processing/src/data_processing/collectors/collector_proc/main.py

# Tests for data-processing
uv run pytest apps/data-processing/tests/ -v
```

### Run agents (legacy — kept during migration)

```bash
# collector-proc (extracts procedural documents)
uv run python3 agents/collector-proc/main.py agents/collector-proc/config.yaml

# collector-cad_obr (CAD-OBR property registry)
uv run python3 agents/collector-cad_obr/main.py agents/collector-cad_obr/config.yaml

# firac-cli (FIRAC report generator) — short form
uv run python3 agents/firac-cli/main.py --config agents/firac-cli/config.yaml

# firac-cli — explicit inputs
uv run python3 agents/firac-cli/main.py run \
  --config-path agents/firac-cli/config.yaml \
  --processo "outputs/processo/01_collector/collector_out_processo_consolidated.json" \
  --evidence "outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json" \
  --law-pack "outputs/legal/law_pack_v1.json"

# law-cli (legal rules / normative basis)
uv run python3 agents/law-cli/main.py run \
  --processo "outputs/processo/01_collector/collector_out_processo_consolidated.json" \
  --juntada  "outputs/juntada/01_collector/collector_out_juntada_procuracao_Juraci_para_Francisco.json"

# case-law-cli (jurisprudence selection)
uv run python3 agents/case-law-cli/main.py --config agents/case-law-cli/config.yaml

# petition-cli (petition draft)
uv run python3 agents/petition-cli/main.py --config agents/petition-cli/config.yaml
```

### Run ingest pipelines

```bash
# PDF → Markdown conversion
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_doutrina --mode md_only
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_juris_stj --mode md_only
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_leis --mode md_only

# Normalize bj_leis markdown after conversion
uv run python pipelines/ingest/pdf_convert/profiles/bj_leis/normalize_md.py \
  --in outputs/ingest/bj_leis/01_md --inplace

# Markdown → RAG chunks (Qdrant indexing)
uv run python pipelines/ingest/md_rag/run.py --profile bj_doutrina
uv run python pipelines/ingest/md_rag/run.py --profile bj_juris_stj
uv run python pipelines/ingest/md_rag/run.py --profile bj_leis
```

### Top-level CLI (legacy — root main.py)

> **LEGADO.** Não use para novos fluxos. Use `apps/data-processing/src/data_processing/cli.py`.

```bash
uv run python main.py          # full pipeline: setup → transcribe → collect
uv run python main.py setup    # generate schemas only
uv run python main.py transcrever  # PDF transcription only
uv run python main.py coletar      # document collection only
```

---

## Architecture

The repository is in transition from a legacy structure to a hybrid monorepo.

### Legacy structure still present

- `agents/`
- `pipelines/`
- `artifacts/`
- `scripts/`

### Target structure in progress

- `apps/`
- `platform/`
- `packages/`
- `var/`

When migrating code, prefer the target structure defined in:
- `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md` ← **fonte canônica**
---

## Key Documentation

- `manual_User/codigos_execusao.md` — all execution commands
- `docs/antigravity/juridico-cli/03_Arquitetura_Sistema_EndToEnd_juridico-cli.md` — macro architecture
- `docs/antigravity/juridico-cli/01_PRD_Requisitos_e_Escopo.md` — requirements and scope
- `docs/antigravity/juridico-cli/05_Runbook_Operacoes_Fallbacks_e_Incidentes.md` — operations runbook

---

## Active Migration Objective

The repository is undergoing a structural migration to a hybrid monorepo.

### Target business apps

The project must be reorganized into three main apps:

- `apps/data-processing/`
- `apps/legal-research/`
- `apps/legal-core/`

### Cross-cutting platform layers

In addition to business apps, the repository must support shared platform layers:

- `platform/skill-runtime/`
- `platform/skills/`
- `platform/memory-and-experiences/`
- `platform/continuous-learning/`

### Migration rules

- Preserve current legal extraction behavior.
- `collector-cad_obr` and `collector-proc` remain LLM-based components.
- Do not simplify collectors into deterministic-only scripts.
- Keep use of `skills/`, `prompt.md`, `config.yaml`, and `io.schema.json`.
- Move `collector-cad_obr` and `collector-proc` under `apps/data-processing/`.
- Move research agents under `apps/legal-research/`.
- Move legal reasoning and drafting agents under `apps/legal-core/`.
- Shared code must be extracted into `packages/` or `platform/` when reused by more than one app.
- Runtime data must leave the repository root and move to `var/`.

### Unified data-processing pipeline goal

The `data-processing` app must unify these reusable parts:

1. Markdown conversion engine
2. Legal cleaning logic from `app_streamlit/clean_legal_docs.py`
3. Rule analysis logic from `pdf_legal_br/analisador_de_regras.py`

These parts must be incorporated as modular pipeline stages, not copied as isolated legacy apps.

### Mandatory implementation order

1. Create target directory structure
2. Create `apps/data-processing/`
3. Migrate `collector-cad_obr`
4. Migrate `collector-proc`
5. Integrate conversion engine
6. Integrate legal cleaner
7. Integrate rule analyzer
8. Create orchestrated unified pipeline
9. Update imports, configs, tests, and execution commands
10. Validate CLI execution and outputs

### Schema authority

- Bundle schemas (específicos de um agente/skill) ficam em `platform/skills/<bundle>/assets/`.
- Shared schemas (reutilizados entre dois ou mais apps) ficam em `packages/shared-schemas/`.
- Nunca duplique um schema: se já existe em `packages/shared-schemas/`, referencie; não copie.

### Fase 4 — trava explícita

**Fase 4 (limpeza e descomissionamento de legado) NÃO está autorizada por padrão.**

- Não remova, arquive nem descomissione código legado (`agents/`, `pipelines/`, `scripts/`, `main.py`) sem gate explícito do usuário.
- Não execute refatorações destrutivas, deleções de branch ou remoção de outputs sem aprovação prévia.
- Só inicie Fase 4 quando o usuário declarar explicitamente: "autorizo Fase 4".

### Non-goals

- Do not redesign legal business logic unless required by path migration.
- Do not rewrite prompts/skills unless path or loading changes require it.
- Do not change schemas semantically unless required by integration.
- Do not remove traceability anchors or JSON validation.

### Source of truth for migration

Read and follow this file before making changes:

- `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md` ← **única fonte canônica da arquitetura**

Os arquivos abaixo são **históricos** (marcados como superseded) e não devem ser usados como referência arquitetural:
- ~~`docs/architecture/juridico_cli_arquitetura_final.md`~~
- ~~`docs/architecture/juridico_cli_projeto_descritivo_v1.1.md`~~
- ~~`docs/implementation/juridico_cli_projeto_descritivo_v1.2.md`~~
- ~~`docs/antigravity/juridico-cli/espelho_estado_atual_juridico-cli.md`~~

Documento auxiliar ainda válido (pipelines operacionais):
- `docs/antigravity/juridico-cli/data_processing_pipelines.md`
