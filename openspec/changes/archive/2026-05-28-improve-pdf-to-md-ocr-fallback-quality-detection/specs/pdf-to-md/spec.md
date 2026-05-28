## MODIFIED Requirements

### Requirement: Use PaddleOCR for scanned or low-text pages

The system SHALL use PaddleOCR for pages that are scanned, unreadable, have insufficient native text extraction, have native text consisting entirely of boilerplate content, OR whose native text quality score falls below `MIN_TEXT_QUALITY`. PaddleOCR MUST be installed as a declared project dependency; the OCR path is not optional or best-effort.

#### Scenario: Scanned page OCR

- **GIVEN** a PDF page with no reliable native text
- **WHEN** the `pdf-to-md` pipeline evaluates the page
- **THEN** the system MUST render the page as an image
- **AND** process the rendered image with PaddleOCR
- **AND** include the OCR text in the Markdown output for that page

#### Scenario: PaddleOCR declared as dependency

- **GIVEN** the `juridico-cli` project environment
- **WHEN** the `ocr` dependency group is installed (`uv sync --group ocr`)
- **THEN** `import paddleocr` MUST succeed without errors
- **AND** PaddleOCR version MUST be registered in `docs/reference/project_version_matrix.md`

#### Scenario: OCR path validated E2E

- **GIVEN** the `ocr` dependency group is installed
- **WHEN** `test_ocr_path.py` is executed
- **THEN** PaddleOCR MUST extract recognizable text from a synthetic test image
- **AND** the extracted text MUST contain the expected test string
- **AND** the test MUST exit with code 0

#### Scenario: Boilerplate-only page triggers OCR

- **GIVEN** a PDF page whose native extracted text consists only of institutional headers, "Fls. N" numerations, or repeated footer lines
- **WHEN** the `pdf-to-md` pipeline evaluates the page with `_needs_ocr`
- **THEN** after stripping boilerplate, the effective text MUST fall below `MIN_CHARS_FOR_TEXT`
- **AND** the system MUST route the page to PaddleOCR
- **AND** the OCR result MUST be used as the page text in the Markdown output

#### Scenario: Low-quality native text triggers OCR

- **GIVEN** a PDF page whose native extracted text has sufficient character count and printable ratio
- **AND** the text exhibits corrupted spacing — words glued together, abnormal token lengths, or abnormal space density
- **WHEN** the `pdf-to-md` pipeline evaluates the page with `_needs_ocr`
- **THEN** `_text_quality_score(text)` MUST return a value below `MIN_TEXT_QUALITY`
- **AND** the system MUST route the page to PaddleOCR
- **AND** the OCR result MUST be used as the page text in the Markdown output
