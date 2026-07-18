# md-frontmatter-yaml Specification

## Purpose

Define os requisitos verificáveis da skill `md-frontmatter-yaml`: inserção de frontmatter YAML genérico em Markdown limpo, preservação integral do corpo incluindo marcadores de página primários (`[[Pág. N]]`) e legados (`<!-- page N -->`), e detecção correta de título H1 na presença de marcadores.
## Requirements
### Requirement: Body preserved integrally including primary page markers

The skill SHALL write the output as `frontmatter_block + body` without any modification to `body`. The body MAY contain `[[judicial_locator: ...]]` (primary) or legacy `[[Pág. N]]` / `<!-- page N -->` page markers on any line; all MUST appear in the output unchanged.

#### Scenario: Body with judicial locator preserved
- **WHEN** the input Markdown contains `[[judicial_locator: page="2"]]` on its own line
- **THEN** the output body contains the same line `[[judicial_locator: page="2"]]` unchanged after the frontmatter block

### Requirement: Title detection ignores primary page markers

`_detect_title()` SHALL strip HTML comments, legacy markers, and structured `[[judicial_locator: ...]]` markers from each line before applying the H1 regex, so that a marker preceding a heading on the same line does not prevent title detection.

#### Scenario: H1 after judicial locator on same line detected correctly
- **WHEN** a line in the input is `[[judicial_locator: page="1"]] # Contestação Especial`
- **THEN** `_detect_title()` returns `"Contestação Especial"` as the detected title

### Requirement: Reference examples use primary marker format

`references/exemplo_entrada.md` and `references/exemplo_saida.md` SHALL contain `[[Pág. N]]` as the primary example of a page marker. The legacy `<!-- page N -->` format MAY appear as a secondary reference.

#### Scenario: exemplo_entrada.md contains primary marker

- **WHEN** `references/exemplo_entrada.md` is read
- **THEN** it contains at least one occurrence of `[[Pág. N]]` (N a positive integer)

#### Scenario: exemplo_saida.md preserves primary marker from input

- **WHEN** `references/exemplo_saida.md` is read
- **THEN** the same `[[Pág. N]]` markers from the entrada example appear unchanged in the saída example body

---

### Requirement: SKILL.md documents accepted marker formats

`SKILL.md` SHALL explicitly state that the skill accepts input files containing both `[[Pág. N]]` (primary, produced by `md-clean-markdown`) and `<!-- page N -->` (legacy), and that both are preserved integrally.

#### Scenario: SKILL.md lists primary format

- **WHEN** `SKILL.md` is read
- **THEN** it mentions `[[Pág. N]]` as the primary page marker format in the "O que esta skill faz" or "Contrato de entrada" section

#### Scenario: SKILL.md lists legacy format

- **WHEN** `SKILL.md` is read
- **THEN** it mentions `<!-- page N -->` as the legacy page marker format alongside the primary

---

### Requirement: End-to-end validation passes strict mode with primary marker fixture

Running `run_example.sh` SHALL execute `validate_output.py --original --strict` on a fixture file that contains `[[Pág. N]]` markers, and the command SHALL exit 0.

#### Scenario: Example script exits 0 with strict validation

- **WHEN** `bash scripts/run_example.sh` is executed
- **THEN** exit code is 0 and no validation errors are reported

#### Scenario: Fixture contains primary marker

- **WHEN** the example input used by `run_example.sh` is read
- **THEN** it contains at least one `[[Pág. N]]` marker

### Requirement: Automated pytest suite coverage
The skill `md-frontmatter-yaml` SHALL have a companion pytest file `test_frontmatter_yaml.py` under its scripts directory that verifies all of the core requirements defined in the canonical specification.

#### Scenario: Pytest run passes successfully
- **WHEN** `uv run pytest platform/skills/md-frontmatter-yaml/` is executed
- **THEN** the test runner completes with exit code 0 and all tests pass

### Requirement: Enrich frontmatter with legal metadata from locators
The frontmatter generation SHALL extract legal metadata from `[[judicial_locator: ...]]` markers found in the body and populate respective frontmatter keys: `process_number`, `event`, and `document_code`. Explicit CLI values MUST override these extracted fields.

#### Scenario: Legal metadata injected into frontmatter
- **WHEN** the input body contains a `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1"]]` marker
- **THEN** the generated YAML frontmatter MUST contain `process_number: "4000153-37.2026.8.26.0136/SP"`, `event: "43"`, and `document_code: "CONTES1"`

### Requirement: Document date and author fallback logic
The system SHALL populate `document_date` and `author` from page locators or headers (if present and reliable) before falling back to `null`. It MUST NOT force them to `null` if a valid value is detected or provided.

#### Scenario: Date and author populated from locators
- **WHEN** a locator contains `date="2026-07-17"` and `user="kiko"`, and no date/author is passed via CLI
- **THEN** the YAML frontmatter MUST contain `document_date: "2026-07-17"` and `author: "kiko"`

### Requirement: Title detection prefers explicit legal document-type line for contestação

When `document_type` (from `--doc-type`) equals `contestacao_processo`, the
skill SHALL scan the first 40 lines of the body (after stripping page
markers and `[[judicial_locator: ...]]` tokens) for a standalone line whose
trimmed content is exactly `CONTESTAÇÃO`. If found, that value SHALL be
used as `title`, taking precedence over the generic first-H1 detection.
If no such line exists, the skill SHALL fall back to the existing
first-H1 detection logic unchanged.

#### Scenario: Explicit CONTESTAÇÃO line overrides truncated H1
- **WHEN** `document_type` is `contestacao_processo` and the body contains
  both a long/truncated H1 heading (e.g. `# PROCEDIMENTO COMUM (NULIDADE DE
  ESCRITURA PÚBLICA c.c.  CANCELAMENTO DE`) earlier in the text and a later
  standalone line containing exactly `CONTESTAÇÃO`
- **THEN** the generated frontmatter `title` is `CONTESTAÇÃO`, not the
  truncated H1 text

#### Scenario: No explicit document-type line falls back to H1
- **WHEN** `document_type` is `contestacao_processo` and the body contains
  no standalone `CONTESTAÇÃO` line
- **THEN** `title` is detected using the existing first-H1 logic
  (unchanged behavior)

### Requirement: Author detection from petition party opening pattern

When no explicit author label (`Responsável:`, `Autor:`, etc.) and no
`user` value from a `[[judicial_locator: ...]]` marker are present, the
skill SHALL scan the first 30 lines of the body for the classic Brazilian
petition party-qualification opening pattern: a line starting with an
upper-case party name (letters, digits, `.`, `-`, spaces; optionally
including corporate suffixes such as `S.A.`, `LTDA`, `EIRELI`, `ME`)
followed by a comma, where the same or one of the following lines contains
the filing clause `vem` followed later by `apresentar`. When this pattern
matches, the captured party name SHALL be used as `author`. If the pattern
does not match, `author` SHALL remain `null` (unchanged fallback).

#### Scenario: Party name detected as author from petition opening
- **WHEN** the body begins with `BANCO DO BRASIL S.A., instituição
  financeira ..., ... vem, com o devido respeito ..., apresentar` and no
  explicit author label or locator `user` is present
- **THEN** the generated frontmatter `author` is `BANCO DO BRASIL S.A.`

#### Scenario: No petition opening pattern keeps author null
- **WHEN** the body does not contain an upper-case party name followed by
  a comma and a nearby `vem ... apresentar` clause, and no explicit author
  label or locator `user` is present
- **THEN** `author` remains `null` (unchanged behavior)

### Requirement: Body preservation holds for legal-document heuristics

The new title and author heuristics for legal documents SHALL NOT modify
the Markdown body in any way; only the frontmatter block values are
affected. Removing the frontmatter block from the output MUST yield a body
byte-identical to the original clean input.

#### Scenario: Body identical after removing frontmatter for contestação fixture
- **WHEN** `apply_frontmatter.py` is run on the real contestação fixture
  (`CONTESTAÇÃO_evento_43.md`) and the resulting output's frontmatter block
  is stripped
- **THEN** the remaining body is byte-identical to the original clean input
  file

