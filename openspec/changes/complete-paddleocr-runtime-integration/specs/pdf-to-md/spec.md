## MODIFIED Requirements

### Requirement: Use PaddleOCR for scanned or low-text pages

The system SHALL use PaddleOCR for pages that are scanned, unreadable, or have insufficient native text extraction. PaddleOCR MUST be installed as a declared project dependency; the OCR path is not optional or best-effort.

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

## ADDED Requirements

### Requirement: OCR dependency group installable

The project SHALL declare PaddleOCR and its CPU backend as an optional `ocr` dependency group in `pyproject.toml`.

#### Scenario: Install OCR group

- **GIVEN** a clean project environment with Python 3.12
- **WHEN** `uv sync --group ocr` is executed
- **THEN** `paddleocr` and `paddlepaddle` MUST install successfully
- **AND** the installed versions MUST be compatible with the versions registered in `docs/reference/project_version_matrix.md`
