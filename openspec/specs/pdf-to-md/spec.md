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

### Requirement: Preserve page anchors

The system SHALL insert one canonical page anchor for every processed PDF page.

#### Scenario: Page anchor generation

- **GIVEN** a PDF with N pages
- **WHEN** the `pdf-to-md` pipeline generates Markdown
- **THEN** the output MUST contain one anchor per page
- **AND** each anchor MUST use the format `[[Pág. N]]`
- **AND** anchors MUST appear in the same order as the original PDF pages

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

