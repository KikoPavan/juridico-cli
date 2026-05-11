# trailing-whitespace-removal Specification

## Purpose
TBD - created by archiving change fix-md-clean-markdown-trailing-whitespace. Update Purpose after archive.
## Requirements
### Requirement: _fix_trailing_whitespace removes spaces and tabs before newline

`_fix_trailing_whitespace` SHALL remove trailing spaces and tabs that precede the terminal `\n` character, not just characters at the very end of the string.

#### Scenario: spaces before newline are removed
- **GIVEN** a line `"foo   \n"` (three trailing spaces before newline)
- **WHEN** `_fix_trailing_whitespace` is called
- **THEN** the result is `"foo\n"` and `stats.trailing_ws_fixed` is incremented

#### Scenario: tab before newline is removed
- **GIVEN** a line `"bar\t\n"` (tab before newline)
- **WHEN** `_fix_trailing_whitespace` is called
- **THEN** the result is `"bar\n"` and `stats.trailing_ws_fixed` is incremented

#### Scenario: exactly two trailing spaces are preserved as forced break
- **GIVEN** a line `"line  \n"` (exactly two spaces before newline)
- **WHEN** `_fix_trailing_whitespace` is called
- **THEN** the result is `"line  \n"` unchanged (Markdown forced line break)

#### Scenario: line without newline trailing spaces are removed
- **GIVEN** a line `"end   "` (three trailing spaces, no newline)
- **WHEN** `_fix_trailing_whitespace` is called
- **THEN** the result is `"end"` and `stats.trailing_ws_fixed` is incremented

---

### Requirement: page markers pass through pipeline untouched

Page markers `[[Pág. N]]` and `<!-- page N -->` SHALL be preserved by the pipeline and SHALL NOT be processed by `_fix_trailing_whitespace`.

#### Scenario: primary marker preserved end-to-end
- **GIVEN** a line `"[[Pág. 3]]\n"` in the input
- **WHEN** `clean_lines` is called with `preserve_markers=True`
- **THEN** the marker line appears unchanged in the output

#### Scenario: legacy marker preserved end-to-end
- **GIVEN** a line `"<!-- page 5 -->\n"` in the input
- **WHEN** `clean_lines` is called with `preserve_markers=True`
- **THEN** the marker line appears unchanged in the output

