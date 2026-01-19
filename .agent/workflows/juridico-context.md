---
description: description: Load juridico-cli context (CLI-first) and produce an executable plan (run-first, refine-later).
---

# /juridico-context — Load Context & Execute (CLI-first)

## Purpose
Establish a stable context baseline for `juridico-cli` and then proceed with a runnable plan aligned with:
- **CLI + pipelines**, not web/mobile.
- **Run first, refine outputs later**.
- Validate by **runtime outputs**.

## Rules of engagement
1) **Do not confuse paths**
   - `.agent/` is Antigravity Kit tooling (rules/skills/workflows/scripts).
   - Product/runtime lives in: `agents/`, `pipelines/`, `outputs/`, `artifacts/`.

2) **Primary context file**
   - Read: `docs/antigravity/juridico-cli/INDEX.md`
   - Then consult the linked architecture pack as needed.

3) **Execution manager**
   - Use the **orchestrator** to coordinate execution (do not use `/plan` as an executor).

4) **Stage 3.5 (manual adapter before FIRAC)**
   - Before running FIRAC (Stage 4), run the manual adapter: `evidence-agent adapt to produce evidence_map.json.`.
   - FIRAC must consume **only** `evidence_map.json`.

5) **Socratic Portal policy for this workspace**
   - If the user says “Proceed / run everything without adjustments; refine later”:
     - Ask **0–1** operational risk question (only if needed: env/keys/paths/overwrite risk).
     - Then proceed with a runnable plan.
   - Otherwise, ask only what is necessary to clarify:
     - objective, input, expected output, constraints.

6) **Safety override**
   - Any command that modifies files/system must require explicit confirmation:
     - `CONFIRMO: <command>`
   - Never suggest recursive deletion outside the project directory.

## Output format (what you must produce after loading context)
Provide:
1) A short **current-state summary** (what already runs, where outputs are).
2) A **runnable step plan** (by stages) with:
   - Inputs per stage
   - Outputs per stage (paths under `outputs/` and/or `artifacts/`)
   - Minimal verification per stage (what file/folder proves it ran)
3) A list of any “risky commands” that would require `CONFIRMO:`.

## Default assumptions (unless the user overrides)
- Focus on the existing pipeline sequence for CAD_OBR.
- Do not refactor outputs early; prioritize getting **all agents running** first.
- Refinement (schemas/output quality) happens **after** end-to-end execution is stable.
