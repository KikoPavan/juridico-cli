"""
Tests for md-frontmatter-yaml skill.
Verifies metadata extraction, body preservation, page marker preservation,
and CLI interface execution.
All code and comments are written in English.
"""

import sys
import pytest
import yaml
from pathlib import Path

# Add the scripts directory of this skill to the system path to allow direct imports
sys.path.insert(0, str(Path(__file__).parent))

import apply_frontmatter
import validate_output


# ---------------------------------------------------------------------------
# Unit Tests: Title Detection
# ---------------------------------------------------------------------------

def test_detect_title_simple_h1():
    body = "# Document Title\nSome content."
    title, method = apply_frontmatter._detect_title(body)
    assert title == "Document Title"
    assert method == "h1"


def test_detect_title_h1_with_primary_page_marker():
    body = "[[Pág. 1]] # Heading Title\nSome content."
    title, method = apply_frontmatter._detect_title(body)
    assert title == "Heading Title"
    assert method == "h1"


def test_detect_title_h1_with_legacy_page_marker():
    body = "<!-- page 2 --> # Legacy Marker Heading\nSome content."
    title, method = apply_frontmatter._detect_title(body)
    assert title == "Legacy Marker Heading"
    assert method == "h1"


def test_detect_title_h1_with_spaces_and_tabs():
    body = "[[Pág. 5]] \t # Spaced Heading \t \nSome content."
    title, method = apply_frontmatter._detect_title(body)
    assert title == "Spaced Heading"
    assert method == "h1"


def test_detect_title_no_h1():
    body = "## Subtitle\nParagraph of text."
    title, method = apply_frontmatter._detect_title(body)
    assert title is None
    assert method == "null"


# ---------------------------------------------------------------------------
# Unit Tests: Date Detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_date,expected_method", [
    ("Date: 15/03/2024\nSome text.", "2024-03-15", "regex_dmy"),
    ("Signed on 15-03-2024", "2024-03-15", "regex_dmy"),
    ("Created: 2024-03-15", "2024-03-15", "regex_iso"),
    ("São Paulo, 15 de março de 2024.", "2024-03-15", "regex_ptbr"),
    ("Referente a março de 2024", "2024-03", "regex_month_year"),
    ("Competência Março 2024", "2024-03", "regex_month_year"),
])
def test_detect_date_formats(text, expected_date, expected_method):
    date_val, method = apply_frontmatter._detect_date(text)
    assert date_val == expected_date
    assert method == expected_method


def test_detect_date_ignores_after_20_lines():
    # Construct a string with 21 empty lines followed by a date
    body = "\n" * 21 + "15/03/2024"
    date_val, method = apply_frontmatter._detect_date(body)
    assert date_val is None
    assert method == "null"


# ---------------------------------------------------------------------------
# Unit Tests: Author Detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_author,expected_method", [
    ("Responsável: John Doe\nContent.", "John Doe", "regex_label"),
    ("Autor: Jane Smith\nContent.", "Jane Smith", "regex_label"),
    ("Elaborado por: Quality Team\nContent.", "Quality Team", "regex_label"),
    ("Preparado por: Operations Dept\nContent.", "Operations Dept", "regex_label"),
    ("Redator: Jack Wilson\nContent.", "Jack Wilson", "regex_label"),
    ("Autora: Alice Johnson\nContent.", "Alice Johnson", "regex_label"),
])
def test_detect_author_labels(text, expected_author, expected_method):
    author, method = apply_frontmatter._detect_author(text)
    assert author == expected_author
    assert method == "regex_label"


def test_detect_author_ignores_after_30_lines():
    body = "\n" * 31 + "Responsável: John Doe"
    author, method = apply_frontmatter._detect_author(body)
    assert author is None
    assert method == "null"


# ---------------------------------------------------------------------------
# Integration Tests: CLI and validate_output.py
# ---------------------------------------------------------------------------

def test_cli_successful_run(tmp_path, monkeypatch):
    input_file = tmp_path / "test_input.md"
    output_file = tmp_path / "test_output.md"
    report_file = tmp_path / "frontmatter_report.md"

    body_content = (
        "[[Pág. 1]]\n"
        "# DOCUMENT TESTING\n"
        "Responsável: Test User\n"
        "Date: 10/12/2025\n"
        "\n"
        "<!-- page 2 -->\n"
        "This is the body content containing primary and legacy markers.\n"
        "Line 1\n"
        "Line 2\n"
    )
    input_file.write_text(body_content, encoding="utf-8")

    # Mock sys.argv for argument parsing
    monkeypatch.setattr("sys.argv", [
        "apply_frontmatter.py",
        "--input", str(input_file),
        "--output", str(output_file),
        "--doc-type", "report",
        "--tags", "test,pytest,frontmatter",
        "--verbose",
        "--report"
    ])

    # Execute main CLI routine
    with pytest.raises(SystemExit) as exc_info:
        apply_frontmatter.main()

    assert exc_info.value.code == 0
    assert output_file.exists()
    assert report_file.exists()

    # Read output content and verify YAML frontmatter
    output_text = output_file.read_text(encoding="utf-8")
    assert output_text.startswith("---\n")
    
    # Parse YAML to verify structure and contents
    parts = output_text.split("---", 2)
    assert len(parts) >= 3
    yaml_data = yaml.safe_load(parts[1])
    
    assert yaml_data["title"] == "DOCUMENT TESTING"
    assert yaml_data["document_type"] == "report"
    assert yaml_data["source_file"] == "test_input.md"
    assert yaml_data["document_date"] == "2025-12-10"
    assert yaml_data["author"] == "Test User"
    assert yaml_data["language"] == "pt-BR"
    assert yaml_data["tags"] == ["test", "pytest", "frontmatter"]
    assert yaml_data["status"] == "raw"
    assert yaml_data["created_by_skill"] == "md-frontmatter-yaml"

    # Assert that the body was preserved byte-by-byte
    output_body = parts[2].lstrip("\n")
    assert output_body == body_content

    # Run the strict validation from validate_output.py
    validation_code = validate_output.run_validation(output_file, input_file, strict=True)
    assert validation_code == 0


def test_cli_aborts_when_frontmatter_pre_exists(tmp_path, monkeypatch):
    input_file = tmp_path / "test_input.md"
    output_file = tmp_path / "test_output.md"

    pre_existing_content = (
        "---\n"
        "title: Existing Title\n"
        "---\n"
        "# Document Title\n"
        "Body content."
    )
    input_file.write_text(pre_existing_content, encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "apply_frontmatter.py",
        "--input", str(input_file),
        "--output", str(output_file)
    ])

    with pytest.raises(SystemExit) as exc_info:
        apply_frontmatter.main()

    assert exc_info.value.code == apply_frontmatter.EXIT_ALREADY_HAS_FM
    assert not output_file.exists()


def test_cli_preserves_page_markers(tmp_path, monkeypatch):
    input_file = tmp_path / "test_input.md"
    output_file = tmp_path / "test_output.md"

    body_content = (
        "[[Pág. 1]]\n"
        "# Title\n"
        "<!-- page 2 -->\n"
        "Some text.\n"
        "[[Pág. 3]]\n"
        "More text.\n"
        "<!-- page 4 -->\n"
    )
    input_file.write_text(body_content, encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "apply_frontmatter.py",
        "--input", str(input_file),
        "--output", str(output_file),
        "--title", "Forced Title"
    ])

    with pytest.raises(SystemExit) as exc_info:
        apply_frontmatter.main()

    assert exc_info.value.code == 0
    
    # Read output and verify the markers are preserved in the correct positions
    output_text = output_file.read_text(encoding="utf-8")
    parts = output_text.split("---", 2)
    assert len(parts) >= 3
    
    output_body = parts[2].lstrip("\n")
    assert output_body == body_content
    assert "[[Pág. 1]]" in output_body
    assert "<!-- page 2 -->" in output_body
    assert "[[Pág. 3]]" in output_body
    assert "<!-- page 4 -->" in output_body


def test_detect_title_h1_with_judicial_locator():
    body = '[[judicial_locator: page="2", process_number="123"]] # Judicial Heading\nSome content.'
    title, method = apply_frontmatter._detect_title(body)
    assert title == "Judicial Heading"
    assert method == "h1"


def test_cli_judicial_locator_metadata_injected(tmp_path, monkeypatch):
    input_file = tmp_path / "test_input.md"
    output_file = tmp_path / "test_output.md"

    body_content = (
        '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="43", document_code="CONTES1", page="1", date="2026-07-17", user="kiko"]]\n'
        "# CONTESTACAO DE TESTE\n"
        "Body content.\n"
    )
    input_file.write_text(body_content, encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "apply_frontmatter.py",
        "--input", str(input_file),
        "--output", str(output_file)
    ])

    with pytest.raises(SystemExit) as exc_info:
        apply_frontmatter.main()

    assert exc_info.value.code == 0
    output_text = output_file.read_text(encoding="utf-8")
    parts = output_text.split("---", 2)
    assert len(parts) >= 3
    yaml_data = yaml.safe_load(parts[1])

    assert yaml_data["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert yaml_data["event"] == "43"
    assert yaml_data["document_code"] == "CONTES1"
    assert yaml_data["document_date"] == "2026-07-17"
    assert yaml_data["author"] == "kiko"


def test_cli_preserves_enriched_event_separator_locator(tmp_path, monkeypatch):
    input_file = tmp_path / "event_separator.md"
    output_file = tmp_path / "event_separator_frontmatter.md"
    locator = (
        '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", '
        'event="32", event_title="DETERMINADA A CITACAO", page="1", '
        'date="27/04/2026 13:34:24", '
        'user="J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO", '
        'user_role="MAGISTRADO", sequence="32", kind="event_separator"]]'
    )
    body = locator + "\n# PÁGINA DE SEPARAÇÃO\nEvento: 32\n"
    input_file.write_text(body, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["apply_frontmatter.py", "--input", str(input_file), "--output", str(output_file)],
    )

    with pytest.raises(SystemExit) as exc_info:
        apply_frontmatter.main()

    assert exc_info.value.code == 0
    output_text = output_file.read_text(encoding="utf-8")
    assert locator in output_text
    yaml_data = yaml.safe_load(output_text.split("---", 2)[1])
    assert yaml_data["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert yaml_data["event"] == "32"
    assert yaml_data["author"] == "J14432 - MARCOS ROGÉRIO SANCHES CRUZ GERALDO"
