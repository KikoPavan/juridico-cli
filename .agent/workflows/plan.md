---
description: Create project plan using project-planner agent. Planning only: write one plan file in project root; no code writing.
---

# /plan - Project Planning Mode

$ARGUMENTS

---

## 🔴 CRITICAL RULES

1. **NO CODE WRITING** - This command creates a plan file only
2. **Use project-planner agent** - NOT Claude Code's native Plan subagent
3. **Canonical Context** - MUST read `docs/antigravity/juridico-cli/INDEX.md` first
4. **References Section** - Plan MUST include `## Referências` using RELATIVE PATHS (no `file:///`)
5. **Dynamic Naming** - Plan file name derived from task (kebab-case, max 30 chars)
6. **STOP AFTER PLAN** - Do not run `/create` or any implementation steps

---

## Task

Use the `project-planner` agent with this context:

```
CONTEXT:
- User Request: $ARGUMENTS
- Mode: PLANNING ONLY (no code)
- Output: ./{task-slug}.md (project root)
- Canonical Docs: docs/antigravity/juridico-cli/INDEX.md

NAMING RULES:
1. Extract 2-3 key words from request
2. Lowercase, hyphen-separated (kebab-case)
3. Max 30 characters
4. Example: "e-commerce cart" → ecommerce-cart.md

RULES:
1. **READ FIRST:** `docs/antigravity/juridico-cli/INDEX.md` to understand the project (Context Check).
2. **CONSULT:** Follow links in INDEX.md only if relevant to the specific request.
3. **PLAN:** Create ./{slug}.md in project root with task breakdown.
4. **REFERENCES:** Include a section `## Referências` in the plan:
   - List `docs/antigravity/juridico-cli/INDEX.md` as the base.
   - List any other file used using **relative paths** (e.g. `docs/...md`).
   - **DO NOT** use `file:///` URI scheme.
   - **MUST** use section anchors for deep links (e.g. `docs/...md#Seção`).
5. **DO NOT** write or modify any other files.
6. **REPORT** the exact file name created.
7. **END** after reporting (no execution).
```

---

## Expected Output

| Deliverable | Location |
| ------------- | ---------- |
| Project Plan | `./{task-slug}.md` |
| References | `## Referências` section (Relative paths + Anchors) |
| Task Breakdown | Inside plan file |
| Agent Assignments | Inside plan file |
| Verification Checklist | Inside plan file (Phase X) |

---

## After Planning

Tell user:
```
[OK] Plan created: ./{slug}.md

Next steps (manual):

• Review/adjust the plan
• When ready, run `/create` using the plan
```

---

## Naming Examples

| Request | Plan File |
| --------- | ----------- |
| `/plan e-commerce site with cart` | `./ecommerce-cart.md` |
| `/plan mobile app for fitness` | `./fitness-app.md` |
| `/plan add dark mode feature` | `./dark-mode.md` |
| `/plan fix authentication bug` | `./auth-fix.md` |
| `/plan SaaS dashboard` | `./saas-dashboard.md` |

---

## Usage

```
/plan e-commerce site with cart
/plan mobile app for fitness tracking
/plan SaaS dashboard with analytics
```
