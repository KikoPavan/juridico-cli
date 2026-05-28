# text-quality-detection Specification

## Purpose
TBD - created by archiving change improve-pdf-to-md-ocr-fallback-quality-detection. Update Purpose after archive.
## Requirements
### Requirement: Detect low-quality native text via heuristic scoring

The system SHALL compute a quality score for native text extracted by PyMuPDF and treat text with a score below `MIN_TEXT_QUALITY` as unreliable, routing the page to PaddleOCR.

#### Scenario: Text quality scoring

- **WHEN** PyMuPDF extracts native text from a PDF page
- **AND** the text passes the character count and printable ratio checks
- **THEN** the system MUST compute a quality score using `_text_quality_score(text)`
- **AND** the score MUST reflect space density and long-token ratio as primary indicators
- **AND** the score MUST be in the range [0.0, 1.0], where 1.0 is perfect quality

#### Scenario: Low-quality text triggers OCR fallback

- **WHEN** `_text_quality_score` returns a value below `MIN_TEXT_QUALITY`
- **THEN** `_needs_ocr` MUST return `(True, "low_quality")`
- **AND** the system MUST route the page to PaddleOCR if available
- **AND** the OCR result MUST replace the native text in the Markdown output

#### Scenario: Quality constant is declared and explicit

- **WHEN** the `convert_pdf_to_md.py` module is loaded
- **THEN** the constant `MIN_TEXT_QUALITY` MUST be declared at the module level
- **AND** its value MUST be between 0.0 and 1.0 exclusive
- **AND** it MUST appear alongside `MIN_CHARS_FOR_TEXT` and `MIN_PRINTABLE_RATIO`

### Requirement: Report routing reason per page

The system SHALL include the routing reason in verbose output and the conversion report for every processed page.

#### Scenario: Verbose log includes routing reason

- **WHEN** `--verbose` is passed to the CLI
- **AND** a page is processed by `_extract_pymupdf`
- **THEN** the stderr log for that page MUST include one of: `low_chars`, `low_printable`, `low_quality`, `pymupdf`, or `ocr`
- **AND** pages routed via `low_quality` MUST display `ocr` as the source label after PaddleOCR runs

#### Scenario: Conversion report includes routing reason

- **WHEN** `--report` is passed to the CLI
- **AND** the conversion report is generated
- **THEN** each page row in the report MUST include the routing reason
- **AND** the reason column MUST distinguish between `low_chars`, `low_printable`, and `low_quality`

