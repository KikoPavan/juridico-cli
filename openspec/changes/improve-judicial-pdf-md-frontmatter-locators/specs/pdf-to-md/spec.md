## MODIFIED Requirements

### Requirement: Preserve page anchors

The system SHALL insert one canonical structured judicial locator page anchor for every processed PDF page. If the page contains electronic locator text, the system SHALL extract its fields (process_number, event, document_code, page, page_separation, date, user, sequence) and serialize them into the locator tag. If no electronic locator is found, it SHALL generate a simple structured locator tag with the page number.

#### Scenario: Page anchor generation with electronic locators
- **GIVEN** a PDF page containing electronic locator text "Processo 4000153-37.2026.8.26.0136/SP, Evento 43, CONTES1, Página 2"
- **WHEN** the `pdf-to-md` pipeline generates Markdown
- **THEN** the output page anchor MUST be: `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1", page="2"]]`

#### Scenario: Page anchor generation fallback
- **GIVEN** a PDF page with no electronic locator text
- **WHEN** the `pdf-to-md` pipeline generates Markdown for page 3
- **THEN** the output page anchor MUST be: `[[judicial_locator: page="3"]]`
