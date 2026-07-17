## Why

Brazilian lawsuit PDFs often contain digital locators (process numbers, event IDs, document codes, pages, dates, user names, sequence numbers) in their headers or footers. The current pipeline uses a generic `[[Pág. N]]` marker, discarding this rich judicial context. This change introduces a structured `judicial_locator` to represent page markers, enabling downstream tools to leverage this metadata while preserving compatibility with legacy page markers and older physical files that use "fls.". Additionally, it fixes HTML entity encoding bugs (e.g., `Certid&atilde;o` to `Certidão`) and enriches the document's YAML frontmatter with inferred legal metadata.

## What Changes

- Replaces the generic `[[Pág. N]]` page delimiter with a structured `[[judicial_locator: ...]]` marker during PDF-to-MD conversion.
- Recognizes electronic locators in lawsuit pages, extracting attributes such as `process_number`, `event`, `document_code`, `page`, `page_separation` (for legacy/physical page numbering), `date`, `user`, and `sequence`.
- Updates `md-clean-markdown` to preserve `[[judicial_locator: ...]]` markers intact and clean HTML entities like `Certid&atilde;o` to `Certidão`.
- Updates `md-frontmatter-yaml` to parse page locators, consolidate document-level legal metadata, and inject them into the YAML frontmatter without overriding explicitly provided metadata.
- Updates `gemini_client.py` and other packages consuming page markers to recognize and parse `[[judicial_locator: ...]]` while maintaining compatibility with legacy `[[Pág. N]]` and `<!-- page N -->` formats.

## Capabilities

### New Capabilities
- `judicial-locator`: A structured page marker format and parsing library that extracts judicial metadata from lawsuit electronic page headers and footers.

### Modified Capabilities
- `pdf-to-md`: Generates structured `judicial_locator` markers instead of `[[Pág. N]]` during conversion.
- `md-clean-markdown`: Preserves `[[judicial_locator: ...]]` markers and decodes HTML entities.
- `md-frontmatter-yaml`: Extracts judicial metadata from locators to enrich frontmatter YAML.

## Impact

- `platform/skills/pdf-to-md/` scripts and tests.
- `platform/skills/md-clean-markdown/` scripts and tests.
- `platform/skills/md-frontmatter-yaml/` scripts and tests.
- `packages/shared-llm/gemini_client.py` page-slicing logic.
