# pdf-to-md

## Purpose

Define the canonical requirements for converting PDF files into raw traceable Markdown through the `pdf-to-md` capability.

The capability supports direct text extraction for digital PDFs and PaddleOCR-based OCR for scanned, unreadable, or low-text pages, while preserving page order and page anchors.
## Requirements
### Requirement: Convert digital PDFs to raw Markdown

The system SHALL convert digital PDFs with native text into raw Markdown while preserving page order.

#### Scenario: Digital PDF conversion

- **GIVEN** a digital PDF with native extractable text
- **WHEN** the `pdf-to-md` pipeline processes the file
- **THEN** the system MUST extract text directly using PyMuPDF
- **AND** generate a raw Markdown output file
- **AND** preserve the original page order

### Requirement: Use PaddleOCR for scanned or low-text pages

The system SHALL use PaddleOCR for pages that are scanned, unreadable, have insufficient native text extraction, have native text consisting entirely of boilerplate content, OR whose native text quality score falls below `MIN_TEXT_QUALITY`. PaddleOCR MUST be installed as a declared project dependency; the OCR path is not optional or best-effort.

Before invoking PaddleOCR, the system SHALL preprocess the rendered page image using `_preprocess_image` (grayscale, auto-contrast, binarization via Pillow). If preprocessing fails, the system SHALL fall back to the raw image. After OCR, the system SHALL evaluate the result with `_text_quality_score`; if the score falls below `MIN_OCR_POST_QUALITY`, the page SHALL be marked as `low_ocr_quality` and the output text SHALL be replaced with the literal `[low_ocr_quality]`.

#### Scenario: Scanned page OCR with preprocessing

- **GIVEN** a PDF page with no reliable native text
- **WHEN** the `pdf-to-md` pipeline evaluates the page
- **THEN** the system MUST render the page as an image
- **AND** MUST apply `_preprocess_image` to the rendered image before OCR
- **AND** MUST process the preprocessed image with PaddleOCR
- **AND** MUST evaluate the OCR result quality with `_text_quality_score`
- **AND** if quality is acceptable, MUST include the OCR text in the Markdown output for that page
- **AND** MUST log the mode `ocr_preprocessed` to stderr for that page

#### Scenario: Low-quality OCR result marks page as low_ocr_quality

- **GIVEN** a PDF page processed through PaddleOCR (with preprocessing)
- **AND** the OCR result has `_text_quality_score < MIN_OCR_POST_QUALITY`
- **WHEN** the Markdown output is generated
- **THEN** the page MUST contain the anchor `[[Pág. N]]`
- **AND** the page MUST contain the literal text `[low_ocr_quality]`
- **AND** the corrupted OCR text MUST NOT appear in the output
- **AND** the page MUST be logged with mode `low_ocr_quality`

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
- **AND** the OCR result (after preprocessing and quality check) MUST be used as the page text in the Markdown output

#### Scenario: Low-quality native text triggers OCR

- **GIVEN** a PDF page whose native extracted text has sufficient character count and printable ratio
- **AND** the text exhibits corrupted spacing — words glued together, abnormal token lengths, or abnormal space density
- **WHEN** the `pdf-to-md` pipeline evaluates the page with `_needs_ocr`
- **THEN** `_text_quality_score(text)` MUST return a value below `MIN_TEXT_QUALITY`
- **AND** the system MUST route the page to PaddleOCR
- **AND** the OCR result (after preprocessing and quality check) MUST be used as the page text or replaced with `[low_ocr_quality]` depending on post-OCR quality

#### Scenario: Preprocessing failure falls back to raw OCR

- **GIVEN** `_preprocess_image` raises an exception for a page
- **WHEN** the OCR pipeline handles the error
- **THEN** PaddleOCR MUST still be invoked on the original unprocessed image
- **AND** the log MUST include the token `ocr_raw` for that page
- **AND** the OCR result MUST still be quality-checked post-OCR

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

### Requirement: Generate raw Markdown only

The system SHALL generate raw Markdown without legal interpretation or structured extraction.

#### Scenario: Raw Markdown output

- **GIVEN** any supported input PDF
- **WHEN** the `pdf-to-md` pipeline completes processing
- **THEN** the output MUST be Markdown text
- **AND** MUST NOT include structured JSON extraction
- **AND** MUST NOT include legal classification
- **AND** MUST NOT invoke Outlines, RAG, Mem0, TurboQuant, RLM, process-processing, or legal-knowledge

### Requirement: OCR dependency group installable

The project SHALL declare PaddleOCR and its CPU backend as an optional `ocr` dependency group in `pyproject.toml`.

#### Scenario: Install OCR group

- **GIVEN** a clean project environment with Python 3.12
- **WHEN** `uv sync --group ocr` is executed
- **THEN** `paddleocr` and `paddlepaddle` MUST install successfully
- **AND** the installed versions MUST be compatible with the versions registered in `docs/reference/project_version_matrix.md`

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

