## ADDED Requirements

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
