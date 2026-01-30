---
trigger: always_on
---

---
trigger: always_on
---

# GEMINI.md - Antigravity Kit

> This file defines how the AI behaves in this workspace.

---

## CRITICAL: AGENT & SKILL PROTOCOL (START HERE)

> **MANDATORY:** 

```
Agent activated → Check frontmatter "skills:" field
    │
    └── For EACH skill:
        ├── Read SKILL.md (INDEX only)
        ├── Find relevant sections from content map
        └── Read ONLY those section files
```

- **Selective Reading:** DO NOT read ALL files in a skill folder. Read `SKILL.md` first, then only read sections matching the user's request.
- **Rule Priority:** P0 (GEMINI.md) > P1 (Agent .md) > P2 (SKILL.md). All rules are binding.

### 2. Enforcement Protocol
1. **When agent is activated:**
   - ✅ READ all rules inside the agent file.
   - ✅ CHECK frontmatter `skills:` list.
   - ✅ LOAD each skill's `SKILL.md`.
   - ✅ APPLY all rules from agent AND skills.
2. **Forbidden:** Never skip reading agent rules or skill instructions. "Read → Understand → Apply" is mandatory.

---

## 📥 REQUEST CLASSIFIER (STEP 2)

**Before ANY action, classify the request:**

| Request Type     | Trigger Keywords                           | Active Tiers                   | Result                     |
|------------------|--------------------------------------------|--------------------------------|----------------------------|
| **QUESTION**     | "what is", "how does", "explain"           | TIER 0 only                    | Text Response              |
| **SURVEY/INTEL** | "analyze", "list files", "overview"        | TIER 0 + Explorer              | Session Intel (No File)    |
| **SIMPLE CODE**  | "fix", "add", "change" (single file)       | TIER 0 + TIER 1 (lite)         | Inline Edit                |
| **COMPLEX CODE** | "build", "create", "implement", "refactor" | TIER 0 + TIER 1 (full) + Agent | **{task-slug}.md Required**|
| **DESIGN/UI**    | "design", "UI", "page", "dashboard"        | TIER 0 + TIER 1 + Agent        | **{task-slug}.md Required**|
| **SLASH CMD**    | /create, /orchestrate, /debug              | Command-specific flow          | Variable                   |

---

## TIER 0: UNIVERSAL RULES (Always Active)

### 🌐 Language Handling

Responda exclusivamente em português do Brasil (pt-BR), independentemente do idioma do prompt.
1. **If prompt is in another language:** translate internally for comprehension, but respond in pt-BR.
2. **If user requests translation:** provide the requested translation, but all instructions/explanations/context remain in pt-BR.
3. **Code comments / variable names** may remain in English.

### 🧹 Clean Code (Global Mandatory)

**ALL code MUST follow `@[skills/clean-code]` rules. No exceptions.**

- Concise, direct, solution-focused
- No verbose explanations
- No over-commenting
- No over-engineering
- **Self-Documentation:** Every agent is responsible for documenting their own changes in relevant `.md` files.
- **Global Testing Mandate:** Every agent is responsible for writing and running tests for their changes. Follow the "Testing Pyramid" (Unit > Integration > E2E) and the "AAA Pattern" (Arrange, Act, Assert).
- **Global Performance Mandate:** "Measure first, optimize second."
  - For Web: Core Web Vitals.
  - For CLI/Pipelines: runtime profiling, I/O efficiency, determinism, and reproducible outputs.
- **Infrastructure & Safety Mandate:** Every agent is responsible for deployability and operational safety of changes. Follow the "5-Phase Deployment Process" (Prepare, Backup, Deploy, Verify, Confirm/Rollback). Always verify environment variables and secrets security.

### 📁 File Dependency Awareness

**Before modifying ANY file:**
1. Check `CODEBASE.md` → File Dependencies
2. Identify dependent files
3. Update ALL affected files together

### 🗺️ System Map Read (MANDATORY)

> 🔴 **MANDATORY:** Read `.agent/ARCHITECTURE.md` at session start to understand Kit Agents, Skills, and Scripts.

**Path Awareness (DO NOT CONFUSE):**
- **Kit tooling (Antigravity Kit):** `.agent/` (rules/skills/workflows/scripts)
- **Product/runtime (juridico-cli):**
  - Agents/CLIs: `agents/`
  - Pipelines: `pipelines/`
  - Outputs: `outputs/`
  - Artifacts (db/packs/evidence): `artifacts/`

> 🔴 NEVER assume `.agent/` contains the runtime agents of `juridico-cli`. `.agent/` is Kit-only.

### 🧠 Read → Understand → Apply

```
❌ WRONG: Read agent file → Start coding
✅ CORRECT: Read → Understand WHY → Apply PRINCIPLES → Code

```

**Before coding, answer:**
1. What is the GOAL of this agent/skill?
2. What PRINCIPLES must I apply?
3. How does this DIFFER from generic output?

---

## TIER 1: CODE RULES (When Writing Code)

### 📱 Project Type Routing

| Project Type | Primary Agent | Skills |
|--------------|---------------|--------|
| **MOBILE** (iOS, Android, RN, Flutter)           |  `mobile-developer` | mobile-design |
| **WEB** (Next.js, React web)                      | `frontend-specialist` | frontend-design |
| **BACKEND** (API, server, DB)                     | `backend-specialist` | api-patterns, database-design |
| **CLI (Python)** (commands, pipelines, artifacts) | `backend-specialist` | python-patterns, testing-patterns, systematic-debugging, deployment-procedures |

> 🔴 **Mobile + frontend-specialist = WRONG.** Mobile = mobile-developer ONLY.

### 🛑 Socratic Portal (juridico-cli)

**Purpose:** reduce misunderstandings without blocking progress when the user explicitly wants “run first, refine later”.

#### ✅ Minimum items (proceed if present)
1) Objective (what output is desired)
2) Input (dataset/folder/artifact to use)
3) Expected Output (artifact/file/folder to be generated)
4) Constraints (e.g., “no adjustments”, “run full sequence”, “validate by outputs”)

If 1–4 are clear: **PROCEED** with a runnable plan.

#### ⚡ Fast-Path (highest priority)
If the user explicitly says: “Prosseguir direto” / “Rodar tudo sem ajustes e refinamos no final” / “Seguir a sequência”, then:
- Ask **0–1** operational risk question (only if needed: env/keys/paths/cost/overwrite risk),
- Then **proceed** with a runnable step plan (do not block with discovery).

#### 📌 Decision table
| Request Type                       | Questions | Action |
|------------------------------------|---: |---|
| New Feature / Build (CLI/Pipeline) | 0–2 | Ask ONLY if any minimum item is missing; otherwise runnable plan. |
| Code Edit / Bug Fix                | 0–1 | Confirm error + expected output; ask 1 thing only if reproduction/input is missing. |
| Vague / Simple                     | 1–2 | Ask objective + expected output (avoid long interviews). |
| Full Orchestration                 | 0–1 | Do NOT stop subagents by default; proceed step-by-step. |
| Direct “Proceed / No adjustments”  | 0–1 | Fast-Path: do not block. |

#### 🔐 Safety override (always applies)
Any action that modifies files/system MUST require explicit confirmation:
`CONFIRMO: <comando>`

### 🏁 Final Checklist Protocol

**Trigger:** When the user says "son kontrolleri yap", "final checks", "çalıştır tüm testleri", or similar phrases.

**CLI note:** For CLI-only repos, treat "Done" as: Security + Lint/Format + Schema (if any) + Tests (unit + smoke). UX/SEO/Lighthouse/E2E are N/A unless there is a UI/URL.

| Task Stage       | Command                                            | Purpose |
|------------------|----------------------------------------------------|---------|
| **Manual Audit** | `python .agent/scripts/checklist.py .`             | Priority-based project audit |
| **Pre-Deploy**   | `python .agent/scripts/checklist.py . --url <URL>` | Full Suite + Performance + E2E |

**Priority Execution Order:**
1. **Security** → 2. **Lint** → 3. **Schema** → 4. **Tests** → 5. **UX** → 6. **SEO** → 7. **Lighthouse/E2E**

**Rules:**
- **Completion:** A task is NOT finished until the applicable checklist passes.
- **Reporting:** If it fails, fix the **Critical** blockers first (Security/Lint).

**Available Scripts (12 total):**
| Script                     | Skill                 | When to Use |
|----------------------------|-----------------------|-------------|
| `security_scan.py`         | vulnerability-scanner | Always on deploy |
| `dependency_analyzer.py`   | vulnerability-scanner | Weekly / Deploy |
| `lint_runner.py`           | lint-and-validate     | Every code change |
| `test_runner.py`           | testing-patterns      | After logic change |
| `schema_validator.py`      | database-design       | After DB change |
| `ux_audit.py`              | frontend-design       | After UI change |
| `accessibility_checker.py` | frontend-design       | After UI change |
| `seo_checker.py`           | seo-fundamentals      | After page change |
| `bundle_analyzer.py`       | performance-profiling | Before deploy |
| `mobile_audit.py`          | mobile-design         | After mobile change |
| `lighthouse_audit.py`      | performance-profiling | Before deploy |
| `playwright_runner.py`     | webapp-testing        | Before deploy |

> 🔴 **Agents & Skills can invoke ANY script** via `python .agent/skills/<skill>/scripts/<script>.py`

---

### 🎭 Gemini Mode Mapping

| Mode     | Agent             | Behavior                                     |
|----------|-------------------|----------------------------------------------|
| **plan** | `project-planner` | 4-phase methodology. NO CODE before Phase 4. |
| **ask**  | -                 | Focus on understanding. Ask questions.       |
| **edit** | `orchestrator`    | Execute. Check `{task-slug}.md` first.       |

---

### Script Locations

| Script        | Path |
|---------------|------|
| Full verify   | `.agent/scripts/verify_all.py` |
| Checklist     | `.agent/scripts/checklist.py` |
| Security scan | `.agent/skills/vulnerability-scanner/scripts/security_scan.py` |
| UX audit      | `.agent/skills/frontend-design/scripts/ux_audit.py` |
| Mobile audit  | `.agent/skills/mobile-design/scripts/mobile_audit.py` |
| Lighthouse    | `.agent/skills/performance-profiling/scripts/lighthouse_audit.py` |
| Playwright    | `.agent/skills/webapp-testing/scripts/playwright_runner.py` |

---
