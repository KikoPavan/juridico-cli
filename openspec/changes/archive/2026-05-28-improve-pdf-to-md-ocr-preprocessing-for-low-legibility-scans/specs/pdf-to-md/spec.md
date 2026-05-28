## MODIFIED Requirements

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
