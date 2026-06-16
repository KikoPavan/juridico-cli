## ADDED Requirements

### Requirement: Heading normalization is covered by unit tests

`test_clean_markdown.py` SHALL contain tests for `_fix_heading_space` covering: heading without space after `#`, heading with excess spaces, and heading already correct (unchanged).

#### Scenario: heading without space normalized
- **WHEN** `_fix_heading_space` receives `"##Título\n"`
- **THEN** it returns `"## Título\n"` and increments `stats.headings_fixed`

#### Scenario: heading with excess spaces normalized
- **WHEN** `_fix_heading_space` receives `"###   Título\n"`
- **THEN** it returns `"### Título\n"` and increments `stats.headings_fixed`

#### Scenario: correct heading unchanged
- **WHEN** `_fix_heading_space` receives `"## Título\n"`
- **THEN** it returns `"## Título\n"` and does not increment `stats.headings_fixed`

---

### Requirement: Bullet normalization is covered by unit tests

`test_clean_markdown.py` SHALL contain tests for `_fix_bullet` covering: `*` bullet, `+` bullet, `-` bullet (unchanged), and `*` as emphasis (unchanged).

#### Scenario: asterisk bullet normalized to dash
- **WHEN** `_fix_bullet` receives `"* Item\n"`
- **THEN** it returns `"- Item\n"` and increments `stats.bullets_normalized`

#### Scenario: plus bullet normalized to dash
- **WHEN** `_fix_bullet` receives `"+ Item\n"`
- **THEN** it returns `"- Item\n"` and increments `stats.bullets_normalized`

#### Scenario: dash bullet unchanged
- **WHEN** `_fix_bullet` receives `"- Item\n"`
- **THEN** it returns `"- Item\n"` and does not increment `stats.bullets_normalized`

#### Scenario: inline asterisk not treated as bullet
- **WHEN** `_fix_bullet` receives `"*palavra* em destaque\n"`
- **THEN** it returns `"*palavra* em destaque\n"` unchanged

---

### Requirement: Horizontal rule normalization is covered by unit tests

`test_clean_markdown.py` SHALL contain tests for `_fix_horizontal_rule` covering: `***`, `___`, `===`, `- - -` (all normalized to `---`), and a line with mixed text (not normalized).

#### Scenario: triple asterisk normalized to ---
- **WHEN** `_fix_horizontal_rule` receives `"***\n"`
- **THEN** it returns `"---\n"` and increments `stats.separators_normalized`

#### Scenario: triple underscore normalized to ---
- **WHEN** `_fix_horizontal_rule` receives `"___\n"`
- **THEN** it returns `"---\n"` and increments `stats.separators_normalized`

#### Scenario: triple equals normalized to ---
- **WHEN** `_fix_horizontal_rule` receives `"===\n"`
- **THEN** it returns `"---\n"` and increments `stats.separators_normalized`

#### Scenario: spaced dashes normalized to ---
- **WHEN** `_fix_horizontal_rule` receives `"- - - -\n"`
- **THEN** it returns `"---\n"` and increments `stats.separators_normalized`

#### Scenario: line with text not normalized
- **WHEN** `_fix_horizontal_rule` receives `"--- text\n"`
- **THEN** it returns `"--- text\n"` unchanged

---

### Requirement: Decorative line removal is covered by unit tests

`test_clean_markdown.py` SHALL contain tests for `_remove_decorative_line` covering: removal of `....`, `====` and preservation of a normal text line.

#### Scenario: dots-only line removed
- **WHEN** `_remove_decorative_line` receives `"....\n"`
- **THEN** it returns `None` and increments `stats.decorative_removed`

#### Scenario: equals-only line removed
- **WHEN** `_remove_decorative_line` receives `"====\n"`
- **THEN** it returns `None` and increments `stats.decorative_removed`

#### Scenario: normal text line preserved
- **WHEN** `_remove_decorative_line` receives `"Texto normal\n"`
- **THEN** it returns `"Texto normal\n"` unchanged

---

### Requirement: Code block isolation and restoration are covered by unit tests

`test_clean_markdown.py` SHALL contain tests for `_extract_code_blocks` and `_restore_code_blocks` verifying that fenced code block content is isolated before cleaning and restored exactly after.

#### Scenario: fenced code block extracted as placeholder
- **WHEN** `_extract_code_blocks` receives lines containing a fenced block with ` ``` `
- **THEN** the placeholder `__CODE_BLOCK_0__` appears in the returned lines and the original block content is in the returned dict

#### Scenario: placeholder restored to original content
- **WHEN** `_restore_code_blocks` is called with the placeholder lines and the block dict
- **THEN** the output contains the original fenced block content verbatim

#### Scenario: trailing whitespace inside code block preserved
- **WHEN** a fenced block contains a line with trailing spaces
- **THEN** after extract → clean_lines → restore, those trailing spaces remain intact

---

### Requirement: CLI end-to-end execution is covered by integration tests

`test_clean_markdown.py` SHALL contain at least one test that invokes `clean_markdown.py` as a subprocess with a real input file and verifies the output file is created and passes `validate_output.run_validation`.

#### Scenario: CLI produces valid output from real fixture
- **WHEN** `clean_markdown.py --input <fixture> --output <tmp>` is executed via subprocess
- **THEN** exit code is 0, output file exists and is non-empty, and `validate_output.run_validation` returns 0

---

### Requirement: --max-blank customization is covered by tests

`test_clean_markdown.py` SHALL contain a test for `clean_lines` with `max_blank=1` verifying that sequences of 2+ blank lines collapse to 1.

#### Scenario: three blank lines collapsed to one when max_blank=1
- **WHEN** `clean_lines` is called with three consecutive blank lines and `max_blank=1`
- **THEN** the output contains exactly one blank line between the surrounding content

---

### Requirement: --no-markers flag is covered by tests

`test_clean_markdown.py` SHALL contain a test for `clean_lines` with `preserve_markers=False` verifying that `[[Pág. N]]` markers are processed by the normal cleaning rules instead of being bypassed.

#### Scenario: marker processed as normal text when preserve_markers=False
- **WHEN** `clean_lines` receives `["[[Pág. 1]]\n"]` with `preserve_markers=False`
- **THEN** the marker line is present in output (treated as normal text, not bypassed) and no special preservation logic applies
