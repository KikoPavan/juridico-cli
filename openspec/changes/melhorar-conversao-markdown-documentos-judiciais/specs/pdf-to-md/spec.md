## MODIFIED Requirements

### Requirement: Use PaddleOCR for scanned or low-text pages

The system SHALL use PaddleOCR for pages that are scanned, unreadable, have fewer than 30 useful native-text characters, have native text consisting entirely or predominantly of boilerplate or judicial locators, OR whose native text quality score falls below `MIN_TEXT_QUALITY`. PaddleOCR MUST be installed as a declared project dependency; the OCR path is not optional or best-effort.

Before invoking PaddleOCR, the system SHALL preprocess the rendered page image using `_preprocess_image` (grayscale, auto-contrast, binarization via Pillow). If preprocessing fails, the system SHALL fall back to the raw image. After OCR, the system SHALL evaluate the result with `_text_quality_score`; the post-OCR score MUST penalize output composed only or predominantly of judicial locators. If the score falls below `MIN_OCR_POST_QUALITY`, the page SHALL be marked as `low_ocr_quality` and the output text SHALL be replaced with the literal `[low_ocr_quality]`.

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
- **GIVEN** a PDF page processed through PaddleOCR with preprocessing
- **AND** the OCR result has `_text_quality_score < MIN_OCR_POST_QUALITY`
- **WHEN** the Markdown output is generated
- **THEN** the page MUST contain its canonical page anchor
- **AND** the page MUST contain the literal text `[low_ocr_quality]`
- **AND** the corrupted OCR text MUST NOT appear in the output
- **AND** the page MUST be logged with mode `low_ocr_quality`

#### Scenario: PaddleOCR declared as dependency
- **GIVEN** the `juridico-cli` project environment
- **WHEN** the `ocr` dependency group is installed with `uv sync --group ocr`
- **THEN** `import paddleocr` MUST succeed without errors
- **AND** PaddleOCR version MUST be registered in `docs/reference/project_version_matrix.md`

#### Scenario: OCR path validated E2E
- **GIVEN** the `ocr` dependency group is installed
- **WHEN** `test_ocr_path.py` is executed
- **THEN** PaddleOCR MUST extract recognizable text from a synthetic test image
- **AND** the extracted text MUST contain the expected test string
- **AND** the test MUST exit with code 0

#### Scenario: Boilerplate-only page triggers OCR
- **GIVEN** a PDF page whose native extracted text consists only of institutional headers, judicial locators, `Fls. N` numerations, or repeated footer lines
- **WHEN** the `pdf-to-md` pipeline evaluates the page
- **THEN** after stripping boilerplate and judicial locators, the effective text MUST fall below the useful-text threshold
- **AND** the system MUST route the page to PaddleOCR
- **AND** the OCR result MUST be used or replaced with `[low_ocr_quality]` according to its post-OCR quality

#### Scenario: Locator-dominated page receives explicit OCR fallback
- **GIVEN** `_needs_ocr()` initially returns false for a page
- **AND** the native text is predominantly boilerplate or judicial locators
- **WHEN** the pipeline evaluates the residual useful content
- **THEN** the system MUST attempt PaddleOCR
- **AND** MUST compare the OCR result using the post-OCR quality criteria

#### Scenario: Low-quality native text triggers OCR
- **GIVEN** a PDF page whose native extracted text has sufficient character count and printable ratio
- **AND** the text exhibits corrupted spacing, abnormal token lengths, or abnormal space density
- **WHEN** the `pdf-to-md` pipeline evaluates the page with `_needs_ocr`
- **THEN** `_text_quality_score(text)` MUST return a value below `MIN_TEXT_QUALITY`
- **AND** the system MUST route the page to PaddleOCR
- **AND** the OCR result MUST be used or replaced with `[low_ocr_quality]` according to its post-OCR quality

#### Scenario: OCR output containing only locators is penalized
- **GIVEN** PaddleOCR returns text composed only or predominantly of judicial locators
- **WHEN** the pipeline calculates post-OCR quality
- **THEN** the locator content MUST reduce the quality score
- **AND** an output below `MIN_OCR_POST_QUALITY` MUST be replaced with `[low_ocr_quality]`

#### Scenario: Preprocessing failure falls back to raw OCR
- **GIVEN** `_preprocess_image` raises an exception for a page
- **WHEN** the OCR pipeline handles the error
- **THEN** PaddleOCR MUST still be invoked on the original unprocessed image
- **AND** the log MUST include the token `ocr_raw` for that page
- **AND** the OCR result MUST still be quality-checked post-OCR
