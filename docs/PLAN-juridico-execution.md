# PLAN-juridico-execution.md - Juridico CLI Execution Plan

> **Objective**: Load context and proceed with a runnable plan aligned with CLI-first principles, focusing on end-to-end execution and validation by artifacts.

## 1. Current State Summary (as of 2026-01-26)

**Agents Verified:**
- `collector-cad_obr`, `collector-proc`: Present (Data ingestion)
- `evidence-agent`: Present (Analysis)
- `firac-cli`: Present (Reasoning)
- `case-law-cli`, `petition-cli`, `compliance-cli`: Present (Legal drafting)

**Pipelines Verified:**
- `pipelines/cad_obr`: Primary pipeline for debt/obligation data.
- `pipelines/cad_obr.py`: Entry point.

**Outputs Verified:**
- `outputs/cad_obr/`: Contains execution artifacts.
- `outputs/reconciler_relatorio.md`: Existing output from previous runs.

**Status:** The backbone (Agents + Pipelines) is in place. The immediate goal is to verify the end-to-end flow from Ingestion to Petition.

## 2. Runnable Step Plan

This plan follows the "Run first, refine later" philosophy. We will execute the pipeline stages sequentially, validating outputs at each step.

### Stage 1: Data Ingestion & Reconciliation (CAD_OBR)
**Goal:** Ingest raw documents and normalize data into `dataset_v1`.

- **Input:** `data/cad_obr/` (Raw PDFs/MDs)
- **Agent:** `collector-cad_obr`
- **Pipeline:** `pipelines/cad_obr` (Reconciler)
- **Expected Output:**
    - `outputs/cad_obr/04_reconciler/dataset_v1/*.jsonl` (Normalized data)
    - `artifacts/db/cad_obr_dataset_v1.duckdb` (Analytical DB)
- **Verification:** Check `duckdb_info.status == "ok"` in `pack_global.json` (if generated) or file existence.

### Stage 2: Evidence Packing
**Goal:** Consolidate data into a single technical artifact for agents.

- **Pipeline:** `evidence_pack` (part of `cad_obr` pipeline)
- **Expected Output:**
    - `outputs/cad_obr/pack_global.json`
- **Verification:** Ensure JSON is parseable and contains entries for all expected inputs.

### Stage 3: Evidence Analysis
**Goal:** Semantic analysis and fact-checking.

- **Agent:** `evidence-agent`
- **Input:** `pack_global.json`
- **Expected Output:**
    - `outputs/evidence_out.json` (Legacy report; may be large/truncated)
- **Verification:** Ensure JSON is valid.

### Stage 3.5: Evidence Adapter (Manual)
**Goal:** Produce canonical evidence inputs for downstream stages.

- **Agent/Tool:** evidence-agent adapt
- **Input:** `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json`
- **Expected Output:**
    - `outputs/cad_obr/05_evidence/dataset_v1/evidence_map.json` (Canonical claims + anchors)
    - `outputs/cad_obr/05_evidence/dataset_v1/evidence_map_full.jsonl` (Audit trail)
- **Verification:** No finding exists without anchors; `doc_ids`/anchors present.

### Stage 4: Legal Reasoning (FIRAC)
**Goal:** Construct the legal argument matrix.

- **Agent:** `firac-cli`
- **Input:** `outputs/evidence_map.json`
- **Expected Output:**
    - `outputs/firac_matrix.md` (Facts, Issues, Rules, Analysis, Conclusion)
- **Verification:** Check for logic gaps or missing rules.

### Stage 5: Drafting & Compliance
**Goal:** Produce the final petition and validate it.

- **Agents:** `petition-cli` -> `compliance-cli`
- **Input:** `firac_matrix.md`
- **Expected Output:**
    - `outputs/petition_draft.md`
    - `outputs/compliance_check.md` (Pass/Fail)
- **Verification:** `compliance_check.md` must pass all critical checks.

## 3. Risky Commands & Confirmations

- **Overwrite Risk:** Running the full pipeline will **overwrite** existing content in `outputs/cad_obr`.
    - **Command:** `python pipelines/cad_obr.py --force` (or equivalent)
    - **Mitigation:** Ensure backups of important previous runs if needed.
    - **Requirement:** `CONFIRMO: Sobrescrever outputs antigos` (if prompted or if manual overwrite is needed).

## 4. Next Steps

1. **Orchestrate Stage 1**: Run the collector and reconciler.
2. **Validate Stage 1**: Inspect generated DuckDB/JSONL.
3. **Proceed to Stage 2**: Generate Evidence Pack.

---
**Ready to execute Stage 1?**
