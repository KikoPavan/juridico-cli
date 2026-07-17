## Context

During PDF-to-Markdown conversion and cleaning, the pipeline currently replaces all page delimiters with a generic `[[Pág. N]]` string. This approach discards rich judicial metadata present in electronic process headers and footers (such as CNJ process number, event ID, document code, date, user signatures, and sequence). Furthermore, HTML entities like `Certid&atilde;o` remain in the text post-cleaning, and the YAML frontmatter generation lacks logic to infer lawsuit-specific fields or use locators to prevent inserting `null` for date and author when reliable data is present.

## Goals / Non-Goals

**Goals:**
- Implement a centralized `judicial_locator` parser under `packages/shared-llm/judicial_locator.py` that handles structured, legacy, and physical leaf ("fls.") numbering.
- Update `pdf-to-md` to recognize electronic locators on each page, generating `[[judicial_locator: ...]]` tags.
- Update `md-clean-markdown` to preserve structured locators and decode HTML entities.
- Update `md-frontmatter-yaml` to enrich frontmatter YAML with process number, event, and document code, and fall back to locator metadata for date/author before writing `null`.
- Update `gemini_client.py` to seamlessly parse page numbers from the new structured tags while retaining full backward compatibility.

**Non-Goals:**
- Altering the vector database schema.
- Re-architecting downstream extraction prompts (other than ensuring they can parse the new markers if needed).

## Decisions

### Decision 1: Structured Locator Format
We will serialize the locator inside double square brackets prefixing with `judicial_locator:` followed by space-separated or comma-separated key-value pairs where values are double-quoted.
Example: `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1", page="1"]]`
- **Rationale**: Simple to parse using regular expressions, human-readable, and fits naturally within Markdown.
- **Alternatives**: JSON serialization `[[judicial_locator: {"page": 1}]]`. Rejected due to visual complexity and potential issues with nested brackets/quotes in regex parsers.

### Decision 2: Shared Locator Module
Create `packages/shared-llm/judicial_locator.py` containing common regex patterns, parser, and formatting functions.
- **Rationale**: Keeps parsing and extraction logic DRY. Allows both the CLI tools and the `gemini_client.py` to share the same parsing engine.
- **Alternatives**: inline duplicated regexes. Rejected due to maintainability risks.

### Decision 3: HTML Entity Decoding
We will utilize Python's built-in `html.unescape` inside the cleaning step (`clean_legal_docs.py` / `clean_markdown.py`) to decode HTML entities.
- **Rationale**: `html.unescape` is standard, robust, and handles all HTML entity variations (e.g., `&atilde;`, `&Eacute;`) correctly without manual mappings.
- **Alternatives**: Regex-based manual mapping. Rejected because it is error-prone and incomplete.

## Risks / Trade-offs

- **[Risk]** The electronic header/footer is split across lines or poorly formatted due to OCR.
  - *Mitigation*: The parser regex will be flexible, looking for keywords like "Processo", "Evento", "Página", "Fls", "fls" and extracting matching fields individually. If some fields fail to match, a fallback to the sequential page number is always generated.
- **[Risk]** Upstream components or tests expect the exact `[[Pág. N]]` string.
  - *Mitigation*: We will update the regexes in `md-clean-markdown`, `md-frontmatter-yaml`, and `gemini_client.py` to support both structured `judicial_locator` and legacy formats. All tests will be updated to cover both formats.
