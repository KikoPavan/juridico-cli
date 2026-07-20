"""Integrated judicial Markdown flow tests for the OpenSpec change."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.extractor import DataExtractorApp, LLMClientFactory


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "judicial_markdown_cases.json"
CLEAN_SCRIPT = PROJECT_ROOT / "platform/skills/md-clean-markdown/scripts/clean_markdown.py"


class _FakeDispatcher:
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path

    def dispatch(self, _bundle_id: str):
        return {
            "skill_config": {"schema_ref": str(self.schema_path), "profile": "test"},
            "system_prompt": "Extraia os dados.",
            "llm_profile": {},
        }


class _FakeClient:
    model_name = "fake-model"

    def __init__(self, calls: list[str]):
        self.calls = calls

    def generate_structured(self, messages, *, schema, **kwargs):
        self.calls.append(messages[-1]["content"])
        return {"accepted": True}


def _build_app(tmp_path: Path, schema_path: Path) -> DataExtractorApp:
    app = DataExtractorApp.__new__(DataExtractorApp)
    app.platform_path = str(PROJECT_ROOT / "platform")
    app.var_dir = str(tmp_path)
    app.dirs = {
        "input_md_frontmatter": str(tmp_path / "frontmatter"),
        "input_clean": str(tmp_path / "clean"),
        "input_processed_fm_legacy": str(tmp_path / "legacy"),
        "extracted": str(tmp_path / "extracted"),
        "logs": str(tmp_path / "logs"),
    }
    for directory in app.dirs.values():
        Path(directory).mkdir(parents=True, exist_ok=True)
    app.dispatcher = _FakeDispatcher(schema_path)
    return app


def test_pdf_markdown_clean_validation_routes_only_meaningful_document(tmp_path, monkeypatch):
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw_path = tmp_path / "raw.md"
    clean_path = tmp_path / "cleaned.md"
    raw_path.write_text(cases["rich_document"]["markdown"], encoding="utf-8")

    subprocess.run(
        [sys.executable, str(CLEAN_SCRIPT), "--input", str(raw_path), "--output", str(clean_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    cleaned = clean_path.read_text(encoding="utf-8")
    assert "A finalidade desta contestação é demonstrar fundamento jurídico relevante" in cleaned
    assert '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP"' in cleaned

    schema_path = tmp_path / "schema.json"
    schema_path.write_text('{"type": "object"}', encoding="utf-8")
    app = _build_app(tmp_path, schema_path)
    accepted_path = Path(app.dirs["input_md_frontmatter"]) / "accepted.md"
    rejected_path = Path(app.dirs["input_md_frontmatter"]) / "rejected.md"
    accepted_path.write_text(cleaned, encoding="utf-8")
    rejected_path.write_text(cases["locator_only_document"]["markdown"], encoding="utf-8")

    llm_calls: list[str] = []
    monkeypatch.setattr(
        LLMClientFactory,
        "create_client",
        lambda **_kwargs: _FakeClient(llm_calls),
    )

    output_path = app.run_extraction("extr-test", accepted_path.name)
    rejection = app.run_extraction("extr-test", rejected_path.name)

    assert output_path is not None and Path(output_path).exists()
    assert rejection is None
    assert len(llm_calls) == 1
    assert "contestação" in llm_calls[0]
