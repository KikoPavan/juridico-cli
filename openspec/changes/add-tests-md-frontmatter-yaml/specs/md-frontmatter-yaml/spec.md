## ADDED Requirements

### Requirement: Automated pytest suite coverage
The skill `md-frontmatter-yaml` SHALL have a companion pytest file `test_frontmatter_yaml.py` under its scripts directory that verifies all of the core requirements defined in the canonical specification.

#### Scenario: Pytest run passes successfully
- **WHEN** `uv run pytest platform/skills/md-frontmatter-yaml/` is executed
- **THEN** the test runner completes with exit code 0 and all tests pass
