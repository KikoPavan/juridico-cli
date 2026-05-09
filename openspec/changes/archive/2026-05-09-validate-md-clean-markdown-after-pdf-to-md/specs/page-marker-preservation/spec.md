## ADDED Requirements

### Requirement: Recognize primary page marker format

The system SHALL recognize `[[Pág. N]]` (where N is a positive integer) as the primary page marker format produced by `pdf-to-md`.

#### Scenario: Standalone primary marker on its own line
- **WHEN** the input contains a line with `[[Pág. 1]]` alone
- **THEN** the line is passed to the output unchanged, without any cleaning rule applied

#### Scenario: Primary marker embedded inline in text
- **WHEN** the input contains a line such as `"texto [[Pág. 2]]"` (marker mid-line)
- **THEN** the entire line is passed to the output unchanged

#### Scenario: Primary marker with space variation
- **WHEN** the input contains `[[Pág.  3]]` (extra space after dot)
- **THEN** the line is passed to the output unchanged

---

### Requirement: Preserve legacy page marker format

The system SHALL continue to recognize and preserve `<!-- page N -->` and its documented variants as legacy formats.

#### Scenario: Legacy HTML comment marker
- **WHEN** the input contains `<!-- page 5 -->`
- **THEN** the line is passed to the output unchanged

#### Scenario: Legacy marker with status annotation
- **WHEN** the input contains `<!-- page 3: empty -->` or `<!-- page 4: extraction_failed -->`
- **THEN** the line is passed to the output unchanged

---

### Requirement: No rule may remove or mutilate any recognized marker

The cleaning pipeline SHALL NOT remove, collapse, convert, or modify any line that contains a recognized page marker (primary or legacy), regardless of which other cleaning rules would otherwise apply.

#### Scenario: Marker line immune to bullet normalization
- **WHEN** a line is a recognized page marker
- **THEN** bullet normalization (Regra 5) is not applied to that line

#### Scenario: Marker line immune to punctuation line removal
- **WHEN** a line is a recognized page marker
- **THEN** punctuation-only line removal (Regra 8) is not applied to that line

#### Scenario: Marker line immune to separator normalization
- **WHEN** a line is a recognized page marker
- **THEN** separator normalization (Regra 6) is not applied to that line

---

### Requirement: Validate marker integrity in output

The output validator SHALL verify that every page marker present in the input file exists in the output file.

#### Scenario: All input markers present in output
- **WHEN** the input has markers `[[Pág. 1]]`, `[[Pág. 2]]`, `[[Pág. 3]]`
- **THEN** the output contains exactly those three markers

#### Scenario: Validation fails if marker is missing from output
- **WHEN** the input has `[[Pág. 2]]` but the output does not contain it
- **THEN** `validate_output.py` reports an error identifying the missing marker

#### Scenario: Validation passes with mixed legacy and primary markers
- **WHEN** the input has both `<!-- page 1 -->` (legacy) and `[[Pág. 2]]` (primary)
- **THEN** both are present in the output and validation passes
