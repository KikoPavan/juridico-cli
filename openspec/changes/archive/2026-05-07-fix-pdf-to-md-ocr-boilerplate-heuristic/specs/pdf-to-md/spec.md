## MODIFIED Requirements

### Requirement: Use PaddleOCR for scanned or low-text pages

The system SHALL use PaddleOCR for pages that are scanned, unreadable, have insufficient native text extraction, OR whose native text consists entirely of boilerplate content. PaddleOCR MUST be installed as a declared project dependency; the OCR path is not optional or best-effort.

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

## ADDED Requirements

### Requirement: Strip boilerplate before OCR decision

The system SHALL identify and strip boilerplate lines from native extracted text before evaluating whether a page requires OCR. Boilerplate patterns SHALL be defined as a module-level constant (`BOILERPLATE_PATTERNS`) and applied via `_strip_boilerplate(text)`.

#### Scenario: Boilerplate stripped from effective text

- **GIVEN** a page whose native text contains a court institutional header followed by no other content
- **WHEN** `_strip_boilerplate(text)` is called
- **THEN** the function MUST return a string with all matching boilerplate lines removed
- **AND** the returned string MUST NOT contain the matched boilerplate lines

#### Scenario: Non-boilerplate text preserved

- **GIVEN** a page whose native text contains petition body paragraphs that do not match any boilerplate pattern
- **WHEN** `_strip_boilerplate(text)` is called
- **THEN** the function MUST return the text unchanged
- **AND** `_needs_ocr` MUST NOT route the page to OCR based on boilerplate stripping alone

#### Scenario: Mixed page (boilerplate + content)

- **GIVEN** a page with one institutional header line and multiple body paragraphs
- **WHEN** `_strip_boilerplate(text)` is called
- **THEN** only the header line MUST be removed
- **AND** the remaining body paragraphs MUST be preserved in the returned string
- **AND** if the residual text exceeds `MIN_CHARS_FOR_TEXT`, `_needs_ocr` MUST return False

### Requirement: Boilerplate detection unit-tested

The system SHALL include unit tests covering the boilerplate heuristic in isolation, independent of the full OCR pipeline.

#### Scenario: `_is_boilerplate` returns True for known patterns

- **GIVEN** a string matching a known boilerplate pattern (e.g., `"Fls. 42"`, `"TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO"`)
- **WHEN** the boilerplate detection function is called
- **THEN** it MUST return True (or the equivalent stripped result)

#### Scenario: `_is_boilerplate` returns False for body text

- **GIVEN** a string containing a sentence from a legal petition body
- **WHEN** the boilerplate detection function is called
- **THEN** it MUST return False (or the equivalent unchanged result)
