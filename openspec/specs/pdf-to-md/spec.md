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

The system SHALL use PaddleOCR for pages that are scanned, unreadable, or have insufficient native text extraction.

#### Scenario: Scanned page OCR

- **GIVEN** a PDF page with no reliable native text
- **WHEN** the `pdf-to-md` pipeline evaluates the page
- **THEN** the system MUST render the page as an image
- **AND** process the rendered image with PaddleOCR when available
- **AND** include the OCR text in the Markdown output for that page

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
