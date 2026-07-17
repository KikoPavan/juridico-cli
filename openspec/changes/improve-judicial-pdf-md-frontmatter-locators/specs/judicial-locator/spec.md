# judicial-locator

## Purpose

Define the requirements for parsing and representing Brazilian judicial electronic page locators. A judicial locator extracts metadata such as process number, event, document code, page number, page separation (physical page/leaves "fls."), date, user, and sequence from lawsuit page content, replacing the generic page markers.

## ADDED Requirements

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
