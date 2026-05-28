## ADDED Requirements

### Requirement: Preprocess rendered page image before OCR

The system SHALL apply image preprocessing to the rendered page PNG before invoking PaddleOCR. Preprocessing SHALL include at minimum: conversion to grayscale, contrast enhancement via auto-contrast, and binarization via a binary threshold. Preprocessing SHALL use only Pillow (`PIL`) — no additional image processing dependency SHALL be introduced.

#### Scenario: Preprocessing converts page to grayscale

- **WHEN** `_preprocess_image(img_bytes)` is called with a valid PNG image as bytes
- **THEN** the function MUST return bytes of a PNG image in grayscale mode (`"L"` or `"1"`)
- **AND** the returned bytes MUST be valid PNG

#### Scenario: Preprocessing applies auto-contrast

- **WHEN** `_preprocess_image(img_bytes)` is called with a low-contrast PNG image
- **THEN** the function MUST apply `ImageOps.autocontrast` (or equivalent) to stretch the histogram
- **AND** the returned image MUST have a broader intensity range than the input

#### Scenario: Preprocessing applies binarization

- **WHEN** `_preprocess_image(img_bytes)` is called with a grayscale image
- **THEN** the function MUST apply a binary threshold
- **AND** the resulting image MUST contain only black and white pixels

#### Scenario: Preprocessing does not alter non-OCR pages

- **WHEN** `_preprocess_image` is called in the pipeline
- **THEN** it MUST only be called for pages that have already been routed to the OCR path by `_needs_ocr`
- **AND** pages processed via PyMuPDF direct text extraction MUST NOT be preprocessed

#### Scenario: Preprocessing failure falls back gracefully

- **WHEN** `_preprocess_image(img_bytes)` raises an exception (e.g., corrupt image)
- **THEN** the OCR pipeline MUST log the error to stderr
- **AND** MUST fall back to using the original unprocessed image bytes for the OCR call
- **AND** MUST NOT raise an unhandled exception
