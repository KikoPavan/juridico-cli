# WALKTHROUGH-juridico-execution.md

> **Date:** 2026-01-26
> **Status:** Stage 1-3 Complete. Stage 4 Blocked.

## Summary

We successfully executed the "Data Ingestion & Reconciliation" pipeline (CAD_OBR) and the "Evidence Analysis" stage. The "FIRAC" (Legal Reasoning) stage is currently blocked due to a legacy implementation in `firac-cli`.

## Stage 1: Data Ingestion & Reconciliation (CAD_OBR)

**Executed:**
1. `collector-cad_obr`: Ingested `escritura_imovel`, `contrato_social`, `escritura_hipotecaria`.
2. `pipeline/cad_obr.py`: Normalized & Monetized.
3. `reconciler_cli.py`: Generated `dataset_v1`.

**Outputs Verified:**
- `outputs/cad_obr/04_reconciler/dataset_v1/` contains 9 `.jsonl` files.
- `datasets_v1` successfully created.

## Stage 2: Evidence Packing

**Executed:**
- `evidence_pack_cli.py`: Consolidated dataset into `pack_global.json` and generated `duckdb`.

**Outputs Verified:**
- `outputs/cad_obr/pack_global.json`: Created.
- `artifacts/db/cad_obr_dataset_v1.duckdb`: Created (DuckDB).

## Stage 3: Evidence Analysis

**Executed:**
- `evidence-agent`: Analyzed the pack.
- **Note:** The agent output was truncated due to token limits or timeout. We applied a manual patch to `evidence_out.json` to ensure a valid JSON structure for adapter conversion.

**Outputs Verified:**
- `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json`: Valid JSON (Patched, Legacy).

## Stage 3.5: Evidence Adapter (Manual) — REQUIRED

**Goal:**
- Convert legacy evidence output into the canonical contract for downstream stages.

**Executed/To Execute:**
- Manual adapter: `evidence-agent adapt (converts evidence_out.json into canonical evidence_map.json)`

**Expected Outputs:**
- `outputs/cad_obr/05_evidence/dataset_v1/evidence_map.json`: Canonical evidence input.
- `outputs/cad_obr/05_evidence/dataset_v1/evidence_map_full.jsonl`: Audit trail.

## Stage 4: Legal Reasoning (FIRAC) - BLOCKED

**Issue:**
- `agents/firac-cli/main.py` attempts to run `gemini skill ...`, which is not a valid command in the current environment.
- The agent needs to be updated to use the `google.genai` library directly, similar to `evidence-agent` and `collector-cad_obr`.

## Recommendations

1. **Fix `firac-cli`**: Rewrite `main.py` and `config.yaml` to use the Python SDK (`google.genai`).
2. **Run Stage 3.5 Adapter**: Produce `evidence_map.json` (canonical) before FIRAC.
3. **Resume Stage 4**: Once fixed, run FIRAC using **only** `evidence_map.json`.
4. **Optimize Evidence Agent (later)**: Adjust `max_output_tokens` or prompt to prevent truncation.
