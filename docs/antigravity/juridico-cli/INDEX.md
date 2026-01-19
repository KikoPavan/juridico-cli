# juridico-cli — Context Index (Antigravity)

This folder is the **canonical context** for Antigravity when operating on `juridico-cli`.

## Scope (what this project is)
- Project type: **Python CLI + deterministic pipelines + legal agents**
- Validation style: user validates by **running the pipeline and checking outputs**, not by manual code review.
- Directive: **Run first (end-to-end), refine outputs later**.

## Critical path (what already runs)
- The `collector-cad_obr` pipeline runs and produces datasets and artifacts under:
  - `outputs/cad_obr/...`
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
   - Purpose: pipeline stages, dataset_v1 outputs, evidence packaging, FIRAC integration.

5. **QA / Acceptance Criteria / Regression**
   - `./04_QA_Avaliacao_Criterios_de_Aceite_e_Regressao.md`
   - Purpose: what “good” means, regression checks, test expectations.

6. **Runbook (Ops / Fallbacks / Incidents)**
   - `./05_Runbook_Operacoes_Fallbacks_e_Incidentes.md`
   - Purpose: operational handling, fallbacks, recovery paths.

> Note: If you keep only 5 files in this folder, remove the entry that does not exist.

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
- Canonical input for FIRAC (Stage 4): `evidence_map.json`
- Legacy (do not use for FIRAC): `evidence_out.json`
- Stage 3.5 (manual adapter): `evidence-agent adapt (evidence_out.json -> evidence_map.json (+ evidence_map_full.jsonl))`
- Stage 4 (FIRAC) must read **only** `evidence_map.json`
