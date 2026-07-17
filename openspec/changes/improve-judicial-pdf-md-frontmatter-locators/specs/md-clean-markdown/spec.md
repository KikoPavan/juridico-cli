## ADDED Requirements

### Requirement: Decode HTML entities
The system SHALL decode common HTML entities (such as `&atilde;` to `ã`, `&eacute;` to `é`, etc.) back to normal UTF-8 characters during text cleaning.

#### Scenario: Common legal HTML entity decoded
- **WHEN** the input text contains the string "Certid&atilde;o"
- **THEN** after cleaning, the output MUST contain the string "Certidão"

### Requirement: Preserve judicial_locator markers
The clean pipeline SHALL preserve all `[[judicial_locator: ...]]` page markers intact in the output.

#### Scenario: Judicial locator preserved
- **WHEN** the input contains `[[judicial_locator: page="2", process_number="1234"]]`
- **THEN** after cleaning, the output MUST contain the same `[[judicial_locator: page="2", process_number="1234"]]` marker unchanged

## MODIFIED Requirements

### Requirement: SKILL.md declares primary marker format

`SKILL.md` SHALL document `[[judicial_locator: ...]]` as the primary page marker format, and `[[Pág. N]]` / `<!-- page N -->` as legacy. The "Preserva marcadores de página" statement in the skill description MUST list all formats explicitly.

#### Scenario: SKILL.md updated
- **WHEN** SKILL.md is read
- **THEN** it mentions `[[judicial_locator: ...]]` as primary and legacy formats in the page marker preservation description
