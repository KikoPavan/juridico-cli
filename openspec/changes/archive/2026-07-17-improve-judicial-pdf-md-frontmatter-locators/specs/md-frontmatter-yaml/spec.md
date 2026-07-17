## ADDED Requirements

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

## MODIFIED Requirements

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
