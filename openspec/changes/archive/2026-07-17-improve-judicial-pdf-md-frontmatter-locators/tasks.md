## 1. Library and Shared Parser Implementation

- [x] 1.1 Create `packages/shared-llm/judicial_locator.py` implementing `parse_locator_text`, `format_locator`, `extract_judicial_metadata_from_text`, and related regex parsers.
- [x] 1.2 Write unit tests in `tests/test_judicial_locator.py` verifying parsing of electronic headers, simple markers, and physical leaves ("fls.").

## 2. Update pdf-to-md Conversion Skill

- [x] 2.1 Integrate `judicial_locator` parser into `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` to generate `[[judicial_locator: ...]]` page anchors.
- [x] 2.2 Update unit/integration tests of `pdf-to-md` to support the new structured locator tags.

## 3. Update md-clean-markdown Skill

- [x] 3.1 Update `clean_markdown.py` and `validate_output.py` to preserve `[[judicial_locator: ...]]` using updated regexes.
- [x] 3.2 Add HTML entity decoding (via `html.unescape`) into `fix_encoding()` in `clean_legal_docs.py` and `clean_markdown.py`.
- [x] 3.3 Update unit/integration tests of `md-clean-markdown` to cover structured locators and HTML entity decoding.

## 4. Update md-frontmatter-yaml Skill

- [x] 4.1 Update `apply_frontmatter.py` to strip `[[judicial_locator: ...]]` markers prior to H1 title detection.
- [x] 4.2 Update `apply_frontmatter.py` to extract legal metadata from locators in the body (process_number, event, document_code, date, user/author) and inject them into the YAML frontmatter.
- [x] 4.3 Update `validate_output.py` to allow the new legal fields.
- [x] 4.4 Update unit/integration tests of `md-frontmatter-yaml` to cover these new capabilities.

## 5. Update data-processing CLI and shared LLM client

- [x] 5.1 Update `packages/shared-llm/gemini_client.py` to recognize `[[judicial_locator: ...]]` and parse the page number correctly when splitting page slices.
- [x] 5.2 Run OpenSpec validation and all unit/integration tests of the modified modules to verify end-to-end correctness of the pre-JSON pipeline.
