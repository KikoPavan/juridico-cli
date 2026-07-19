# judicial-locator Specification

## Purpose
TBD - created by archiving change improve-judicial-pdf-md-frontmatter-locators. Update Purpose after archive.
## Requirements
### Requirement: Structured Judicial Locator format
The system SHALL support representing page metadata in a structured format: `[[judicial_locator: key1="value1", key2="value2", ...]]`.
The supported attributes are:
- `process_number` (string or null): the CNJ format lawsuit number.
- `event` (string/number or null): the event number in the electronic process (e.g. 43).
- `document_code` (string or null): the code or mnemonic representing the document (e.g. CONTES1).
- `page` (number/string): the sequential page number or physical sheet number.
- `page_separation` (string or null): physical page range or sheet number (e.g. fls. 42).
- `date` (string or null): document date or signature date (ISO-like or parsed format).
- `user` (string or null): the username or system user signature name.
- `sequence` (number/string or null): the page sequence number.

#### Scenario: Full electronic locator formatting
- **WHEN** all attributes are present (process_number="4000153-37.2026.8.26.0136", event="43", document_code="CONTES1", page="2", page_separation="fls. 42", date="2026-07-17", user="kiko", sequence="1")
- **THEN** the system MUST format it exactly as: `[[judicial_locator: process_number="4000153-37.2026.8.26.0136", event="43", document_code="CONTES1", page="2", page_separation="fls. 42", date="2026-07-17", user="kiko", sequence="1"]]`

#### Scenario: Simple page compatibility
- **WHEN** only the page number is available (page="3")
- **THEN** the system MUST format it as: `[[judicial_locator: page="3"]]`

#### Scenario: Parsing structured locator back to dictionary
- **WHEN** the system parses the string `[[judicial_locator: process_number="1234", page="1"]]`
- **THEN** it MUST return a dictionary containing `{"process_number": "1234", "page": "1"}`

#### Scenario: Legacy marker parsing compatibility
- **WHEN** the system parses legacy markers like `[[Pág. 5]]` or `<!-- page 5 -->`
- **THEN** it MUST return a dictionary containing `{"page": "5"}`

#### Scenario: Legacy leaves marker parsing compatibility
- **WHEN** the system parses legacy leaves strings like `fls. 42` or `fl. 15`
- **THEN** it MUST return a dictionary containing `{"page": "42"}` or `{"page": "15"}`

### Requirement: Judicial locators survive the legal pipeline

The `segmentador-juridico → curador-relevancia → yaml-normalizador-juridico` pipeline SHALL preserve every structured `[[judicial_locator: ...]]` marker already present in the piece text through to the final Markdown body.

#### Scenario: Full locator survives normalization
- **WHEN** the input text contains `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="1", document_code="INIC1", page="1"]]`
- **THEN** the final Markdown body contains that marker with the same attributes and values

### Requirement: Generated anchors include available judicial identity

When the legal pipeline generates an anchor, it MUST include `page`, `process_number`, `event`, and `document_code` whenever each respective value is available from the piece, envelope metadata, or existing locator. The pipeline MUST NOT replace an existing non-null anchor attribute with null.

#### Scenario: Generated anchor is enriched from available metadata
- **WHEN** an anchor is generated for page `1` and the available metadata contains process `4000153-37.2026.8.26.0136/SP`, event `1`, and document code `INIC1`
- **THEN** the generated anchor carries `page="1"`, `process_number="4000153-37.2026.8.26.0136/SP"`, `event="1"`, and `document_code="INIC1"`

#### Scenario: Partial metadata still produces a valid anchor
- **WHEN** an anchor is generated with only page `3` available
- **THEN** the generated anchor carries `page="3"` and does not invent process, event, or document values
