## ADDED Requirements

### Requirement: Log OCR mode per page

The system SHALL log the OCR mode for each page processed via the OCR path. Valid modes are: `ocr_preprocessed`, `ocr_raw`, and `low_ocr_quality`. The mode SHALL appear in the stderr log line for that page. Pages processed via PyMuPDF direct text extraction MUST NOT receive an OCR mode label.

#### Scenario: Preprocessed OCR logs ocr_preprocessed

- **WHEN** a page is processed with PaddleOCR on a preprocessed image
- **AND** the OCR result meets minimum quality (`_text_quality_score >= MIN_OCR_POST_QUALITY`)
- **THEN** the log line for that page MUST include the token `ocr_preprocessed`

#### Scenario: Raw OCR fallback logs ocr_raw

- **WHEN** image preprocessing fails and OCR is executed on the original image
- **AND** the OCR result meets minimum quality
- **THEN** the log line for that page MUST include the token `ocr_raw`

#### Scenario: Low-quality OCR logs low_ocr_quality

- **WHEN** a page is processed with PaddleOCR (with or without preprocessing)
- **AND** `_text_quality_score(ocr_text) < MIN_OCR_POST_QUALITY`
- **THEN** the log line for that page MUST include the token `low_ocr_quality`
- **AND** the page status MUST be `low_ocr_quality`

### Requirement: Mark low-quality OCR pages in output

The system SHALL replace the text of a page whose OCR result falls below `MIN_OCR_POST_QUALITY` with the literal placeholder `[low_ocr_quality]`. The page anchor `[[Pág. N]]` MUST be preserved. The corrupted OCR text MUST NOT appear in the Markdown output.

#### Scenario: low_ocr_quality page receives placeholder text

- **GIVEN** a page whose PaddleOCR result has `_text_quality_score < MIN_OCR_POST_QUALITY`
- **WHEN** the Markdown output is generated
- **THEN** the page MUST contain the anchor `[[Pág. N]]`
- **AND** the page MUST contain the literal text `[low_ocr_quality]`
- **AND** the page MUST NOT contain the corrupted OCR text

#### Scenario: Page anchor preserved for low_ocr_quality pages

- **GIVEN** a PDF where page 2 is marked as `low_ocr_quality`
- **WHEN** the Markdown output is generated
- **THEN** the output MUST contain `[[Pág. 2]]`
- **AND** the anchor MUST appear before the placeholder `[low_ocr_quality]`

### Requirement: Compare mode for diagnostic logging

The system SHALL support a `--compare-ocr` flag (or `PDF_TO_MD_COMPARE_OCR=1` environment variable) that, when enabled, additionally runs PaddleOCR on the raw (unprocessed) image and logs both results to stderr for comparison. This MUST NOT alter the final Markdown output.

#### Scenario: compare-ocr logs both raw and preprocessed results

- **WHEN** the script is invoked with `--compare-ocr` for a page requiring OCR
- **THEN** stderr MUST include a log line for the raw OCR result with token `ocr_raw`
- **AND** stderr MUST include a log line for the preprocessed OCR result with token `ocr_preprocessed`
- **AND** the final Markdown output MUST be identical to a run without `--compare-ocr`

#### Scenario: compare-ocr disabled by default

- **WHEN** the script is invoked without `--compare-ocr` and without `PDF_TO_MD_COMPARE_OCR=1`
- **THEN** raw OCR (on unprocessed image) MUST NOT be executed
- **AND** the log MUST NOT contain the token `ocr_raw` for normally processed pages

### Requirement: Automated test for low_ocr_quality path

The system SHALL include an automated test that verifies the `low_ocr_quality` path without requiring PaddleOCR to be installed. The test SHALL use a synthetic fixture representing corrupted OCR output text.

#### Scenario: low_ocr_quality test does not require PaddleOCR

- **GIVEN** a synthetic string simulating corrupted OCR output (quality score below `MIN_OCR_POST_QUALITY`)
- **WHEN** the quality evaluation function is called on that string
- **THEN** the test MUST conclude that the result qualifies as `low_ocr_quality`
- **AND** the test MUST exit with code 0 (pass) without importing PaddleOCR
