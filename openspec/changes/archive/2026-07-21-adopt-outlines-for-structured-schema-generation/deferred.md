# Deferred Change — Outlines structured schema generation

## Status

Deferred.

## Reason

This change was technically validated too early in the project sequence.

Outlines is useful for schema-bound structured generation, but it belongs to a later phase of the project, after the PDF-to-Markdown and OCR pipeline is operational.

## Current priority

The current priority is:

1. PDF to Markdown conversion.
2. PaddleOCR integration for scanned or low-text PDFs.
3. Page preservation and anchors.
4. Raw Markdown output compatible with downstream processing.

## Rule

Do not apply this change now.

Do not integrate Outlines into the runtime, skills or project dependencies before the document conversion pipeline is completed and validated.
