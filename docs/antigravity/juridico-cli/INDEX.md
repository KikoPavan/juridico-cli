---
document_type: context_index
project: juridico-cli
scope: canonical_context_for_antigravity
version: v1
updated_at: 2026-01-28
principles:
  - run_first_refine_later
  - process_first_firac_core
  - evidence_optional_enrichment
canonical_paths:
  firac:
    - outputs/relatorio_firac.json
    - outputs/relatorio_firac.md
  cad_obr_dataset_v1: outputs/cad_obr/04_reconciler/dataset_v1/*.jsonl
  cad_obr_duckdb: artifacts/db/cad_obr_dataset_v1.duckdb
  evidence_pack: artifacts/evidence_packs/dataset_v1/pack_global.json
  evidence_pack_outputs_non_authoritative: outputs/cad_obr/pack_global.json
  evidence_out: outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json
  evidence_map_export_optional:
    - outputs/cad_obr/05_evidence/dataset_v1/evidence_map.json
    - outputs/cad_obr/05_evidence/dataset_v1/evidence_map_full.jsonl
read_order:
  - 01_PRD_Requisitos_e_Escopo.md
  - 02_Data_Governance_Linhagem_e_Contratos_Minimos.md
  - 03_Arquitetura_Sistema_EndToEnd_juridico-cli.md
  - 03A_Arquitetura_SubSistema_CAD_OBR_Pipelines_Evidence_FIRAC.md
  - 04_QA_Avaliacao_Criterios_de_Aceite_e_Regressao.md
  - 05_Runbook_Operacoes_Fallbacks_e_Incidentes.md
---

# juridico-cli — Context Index (Antigravity)

This folder is the **canonical context** for Antigravity when operating on `juridico-cli`.

## Scope (what this project is)
- Project type: **Python CLI + deterministic pipelines + legal agents**
- Validation style: user validates by **running the pipeline and checking outputs**, not by manual code review.
- Directive: **Run first (end-to-end), refine outputs later**.
- Core rule: **PROCESS-FIRST** — FIRAC-Core is generated from **collector-proc** outputs. CAD_OBR/Evidence is optional enrichment (FIRAC-Plus).

## Critical paths (what already runs / what must run)
### Primary (must run): FIRAC-Core (PROCESS-FIRST)
- `collector-proc` → consolidated process dossier → `firac-cli` → FIRAC report:
  - `outputs/relatorio_firac.json`
  - `outputs/relatorio_firac.md`

### Secondary (already runs): CAD_OBR deterministic pipeline
- The `collector-cad_obr` pipeline runs and produces datasets and artifacts under:
  - `outputs/cad_obr/...` (01..05)
  - `artifacts/db/...` (DuckDB)

## Architecture pack (read order)
> If any file name differs in your repo, update links below to match the real filenames in this folder.

1. **PRD / Requirements & Scope**
   - `./01_PRD_Requisitos_e_Escopo.md`
   - Purpose: objectives, non-goals, constraints, acceptance boundaries.

2. **Data Governance / Lineage / Minimum Contracts**
   - `./02_Data_Governance_Linhagem_e_Contratos_Minimos.md`
   - Purpose: dataset contracts, lineage, schema expectations, traceability.

3. **End-to-End System Architecture (juridico-cli)**
   - `./03_Arquitetura_Sistema_EndToEnd_juridico-cli.md`
   - Purpose: overall flow, modules, inputs/outputs, boundaries.

4. **CAD_OBR Subsystem Architecture (Pipelines/Evidence/FIRAC)**
   - `./03A_Arquitetura_SubSistema_CAD_OBR_Pipelines_Evidence_FIRAC.md`
   - Purpose: pipeline stages, dataset_v1 outputs, evidence packaging, FIRAC enrichment integration.

5. **QA / Acceptance Criteria / Regression**
   - `./04_QA_Avaliacao_Criterios_de_Aceite_e_Regressao.md`
   - Purpose: what “good” means, regression checks, test expectations.

6. **Runbook (Ops / Fallbacks / Incidents)**
   - `./05_Runbook_Operacoes_Fallbacks_e_Incidentes.md`
   - Purpose: operational handling, fallbacks, recovery paths.

## Workspace layout (do not confuse)
- `.agent/` = Antigravity Kit tooling (rules/skills/workflows/scripts)
- `agents/` = project agents/CLIs (collector-*, evidence-agent, firac-cli, petition-cli, compliance-cli, case-law-cli)
- `pipelines/` = deterministic pipelines
- `outputs/` = outputs
- `artifacts/` = db/packs/evidence artifacts

## “Run first, refine later” policy (operational)
When the user explicitly instructs “run everything without adjustments; refine later”:
- Prefer runnable plans with minimal questions.
- Only ask 0–1 operational risk question (paths/env/overwrite risk).
- Keep outputs stable; do not “cleanup” or remove anything outside the workspace.

## Evidence contract (Stage 3 -> Stage 4)
### Canonical Evidence output (Stage 3)
- Canonical (short + always parseable): `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json`
- Deep trace goes to annexes (jsonl/md), not inside the short JSON.

### Evidence map export (Stage 3.5) — OPTIONAL (bridge/view only)
- Optional export/view for integrations that prefer claims/supports:
  - `evidence_map.json`
  - `evidence_map_full.jsonl`
- This export MUST NOT gate FIRAC-Core.

### FIRAC rule (Stage 4)
- FIRAC-Core MUST run from PROCESSO outputs (collector-proc consolidated dossier), even if CAD_OBR Evidence outputs do not exist.
- FIRAC-Plus MAY enrich FIRAC when Evidence exists (prefer `evidence_out.json`; use `evidence_map.json` only as optional export/view).
- FIRAC MUST NOT read **only** `evidence_map.json`.

## Evidence pack location (canonical + non-authoritative compat)
- Canonical pack (source of truth): `artifacts/evidence_packs/dataset_v1/pack_global.json`
- Compat/non-authoritative copy (if present): `outputs/cad_obr/pack_global.json`

Rule: agents and plans MUST use the canonical pack. Any outputs copy is ignored unless it is byte-identical to the canonical pack.
