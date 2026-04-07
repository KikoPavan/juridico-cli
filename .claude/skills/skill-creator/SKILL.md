---
name: skill-creator
description: Guide for creating and maintaining effective skills for Antigravity-based agents. Use when creating or updating a skill that adds specialized knowledge, workflows, or tool integrations—especially skills intended for the juridico-cli project (skills registry, allowlists, and prompt build/pack patterns).
---

# Skill Creator

This skill provides guidance for creating effective skills.

## License & Attribution

This skill includes a `LICENSE.txt`. Preserve it when copying or adapting this skill.

## About Skills

Skills are modular, self-contained packages that extend an agent’s capabilities by providing specialized knowledge, workflows, and tool usage patterns. Think of them as “onboarding guides” for specific domains or tasks—they transform an agent from a general-purpose assistant into a specialized agent equipped with procedural knowledge and project-specific conventions.

### What Skills Provide

1. Specialized workflows — Multi-step procedures for specific domains
2. Tool integrations — Instructions for working with specific file formats or APIs
3. Domain expertise — Project-specific knowledge, schemas, business logic
4. Bundled resources — Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else the agent needs: system prompt, conversation history, other skills’ metadata, and the actual user request.

**Default assumption: the agent is already very smart.** Only add context the agent does not already have. Challenge each piece of information: “Is this necessary?” and “Does this justify its token cost?”

Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task’s fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

Think of the agent as exploring a path: a narrow bridge with cliffs needs guardrails (low freedom), while an open field allows many routes (high freedom).

### Anatomy of a Skill

Every skill consists of a required `SKILL.md` file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.) or reference automation
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```


#### SKILL.md (required)

Every `SKILL.md` consists of:

- **Frontmatter** (YAML): Contains only `name` and `description`. Many runtimes use these fields as the primary trigger/discovery mechanism, so be clear and explicit about when to use the skill.
- **Body** (Markdown): Instructions and guidance for using the skill. Typically loaded only after the skill triggers.

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, can be used without embedding large code blocks in the skill body
- **Note**: Some environments may not execute scripts automatically. In that case, scripts still provide authoritative reference implementations.

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform the agent’s process and decisions.

- **When to include**: For documentation the agent should consult while working
- **Examples**: `references/finance.md` for schemas, `references/policies.md` for policies, `references/api_docs.md` for API specs
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps `SKILL.md` lean; loaded only when needed
- **Best practice**: If files are large (>10k words), include grep/search patterns in `SKILL.md`
- **Avoid duplication**: Put detailed knowledge in references unless it is core procedural guidance.

##### Assets (`assets/`)

Files not intended to be loaded into context, but used within outputs the agent produces.

- **When to include**: When the skill needs files used in final output
- **Examples**: `assets/logo.png`, `assets/slides.pptx`, `assets/frontend-template/`
- **Benefits**: Separates output resources from documentation and reduces context bloat.

#### What to Not Include in a Skill

A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files, including:

- `README.md`
- `INSTALLATION_GUIDE.md`
- `QUICK_REFERENCE.md`
- `CHANGELOG.md`
- etc.

A skill should contain only what an AI agent needs to do the job at hand. Avoid clutter.

### Progressive Disclosure Design Principle

Skills should be designed to minimize context load:

1. **Metadata (`name` + `description`)** — discovery/trigger mechanism (kept minimal)
2. **`SKILL.md` body** — loaded when the skill triggers (keep under 500 lines when possible)
3. **Bundled resources** — loaded on demand (references) or used as deterministic implementations (scripts)

#### Progressive Disclosure Patterns

Keep the `SKILL.md` body to essentials. Split long content into references when approaching ~500 lines.

**Key principle:** When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in `SKILL.md`. Move variant-specific details into separate reference files.

**Pattern 1: High-level guide with references**
```markdown
# PDF Processing

## Quick start
Extract text with pdfplumber:
[short example]

## Advanced features
- **Form filling**: See references/FORMS.md
- **API reference**: See references/REFERENCE.md
- **Examples**: See references/EXAMPLES.md

**Pattern 2: Domain-specific organization**

```md
bigquery-skill/
├── SKILL.md (overview and navigation)
└── references/
    ├── finance.md
    ├── sales.md
    ├── product.md
    └── marketing.md
```

**Pattern 3: Conditional details**

```markdown
# DOCX Processing

## Creating documents
Use a library approach. See references/DOCX.md.

## Editing documents
**For tracked changes:** See references/REDLINING.md
**For OOXML details:** See references/OOXML.md
```

**Important guidelines:**

- **Avoid deeply nested references;** keep references one level deep from SKILL.md.

- **For reference files longer than 100 lines,** add a table of contents at the top.

**Juridico-cli Conventions (required when creating skills for this project)**
When creating skills intended for the juridico-cli ecosystem, follow these conventions:
• Treat skills as reusable, centrally managed knowledge/workflow packages (not per-agent duplicates).
• Prefer heavy deterministic work in /pipelines (Python/DuckDB/scripts). Use skills to instruct how to run/consume artifacts.
• Maintain rastreabilidade: outputs must cite source_id and anchors (e.g., [[Folha X]] / [Pág. Y]) where applicable.
• Respect governance: skills available to a given agent are controlled by allowlists and compiled prompts/build artifacts.
• Align skills with project data contracts: schemas, JSONL datasets, DuckDB views, and the evidence pack (e.g., pack_global.json).

## Skill Creation Process

Skill creation involves these steps:

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Initialize the skill (use a template or init_skill.py)
4. Edit the skill (implement resources and write SKILL.md)
5. Package/distribute (optional; depends on your runtime)
6. Iterate based on real usage

Follow these steps in order, skipping only when clearly not applicable.

### Step 1: Understand the Skill with Concrete Examples

Skip only when usage patterns are already clearly understood.

To create an effective skill, clearly understand concrete examples of how it will be used. This understanding can come from direct user examples or generated examples validated with user feedback.

Ask questions like:

- "What functionality should the skill support?"
- "What user prompts should trigger this skill?"
- "What are common variants and edge cases?"

Avoid asking too many questions in a single message; start with the most important.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Plan Reusable Skill Contents

For each example:

Consider how to execute from scratch

Identify what reusable resources help repeated execution (scripts, references, assets)

Examples:

- A `pdf-editor` skill might warrant `scripts/rotate_pdf.py`.
- A frontend-webapp-builder skill might warrant an assets/ boilerplate template.
- A big-query skill might warrant references/schema.md.

### Step 3: Initialize the Skill

If creating a new skill, use a template to ensure structure consistency.

If your environment supports it, you may run:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

This typically:

- Creates the skill directory
- Generates a `SKILL.md` template with correct frontmatter
- Creates `scripts/`, `references/`, and `assets/` folders (examples may be removed)

If you cannot run scripts, manually create the directory structure shown above.

### Step 4: Edit the Skill

Remember the skill is created for another agent instance to use. Include procedural knowledge, domain details, or reusable assets that reduce repeated effort and minimize errors.

#### Learn Proven Design Patterns
Consult these guides based on your needs:
- Multi-step processes: `references/workflows.md`
- Specific output formats or quality standards: `references/output-patterns.md`

#### Start with Reusable Contents
Implement reusable resources first: `scripts/`, `references/`, and `assets/`. Delete unnecessary examples created by initialization.

If you add scripts, test them in the target environment when possible.

#### Update SKILL.md
Writing guideline: Use imperative/infinitive form.

##### Frontmatter
Write YAML frontmatter with only `name` and `description`:
- `name`: The skill name
- `description`: The primary triggering mechanism; include what the skill does and when to use it
Do not include any other fields in YAML frontmatter.

##### Body
Write instructions for using the skill and its bundled resources. Keep the body lean and link to reference files for details.

### Step 5: Package / Distribute (Optional)

Packaging into a single distributable file may be useful for sharing. However, some runtimes (including many Antigravity setups) can use the skill folder directly without packaging.

If you need a distributable artifact and your environment supports it:

```bash
scripts/package_skill.py <path/to/skill-folder>
```
Optional output directory:

```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

The packaging script may:
- Validate frontmatter, naming conventions, and structure
- Create a packaged file (e.g., a zip with a `.skill` extension) for distribution

If validation fails, fix errors and retry.

### Step 6: Iterate

After real usage, users may request improvements.

**Iteration workflow:**

1. Use the skill on real tasks
2. Identify struggles or inefficiencies
3. Update `SKILL.md` or bundled resources
4. Test again
