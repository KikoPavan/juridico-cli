import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

PROJECT_ROOT = Path(__file__).resolve().parents[3]

from data_processing import extractor  # noqa: E402
from data_processing.extractor import DataExtractorApp  # noqa: E402


def _load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


block_strategies_mod = _load_module_from_path(
    "block_strategies", PROJECT_ROOT / "packages" / "shared-llm" / "block_strategies.py"
)
BlockExtractionStrategyUnavailableError = block_strategies_mod.BlockExtractionStrategyUnavailableError

MEANINGFUL_BODY = (
    "Este documento apresenta fundamentos jurídicos relevantes e descreve os "
    "fatos do processo de forma suficientemente detalhada para a extração."
)


class FakeDispatcher:
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path

    def dispatch(self, bundle_id: str):
        return {
            "skill_config": {"schema_ref": str(self.schema_path), "profile": "test"},
            "system_prompt": "Extraia os dados.",
            "llm_profile": {},
            "bundle_id": bundle_id,
        }


class FakeLLMClientRaisingUnavailableStrategy:
    """Simula o comportamento real de GeminiLLMClient._dispatch_block_extraction
    quando o bundle_id não tem estratégia de blocos registrada: levanta
    BlockExtractionStrategyUnavailableError antes de qualquer persistência."""

    model_name = "fake-model"

    def generate_structured(self, messages, *, schema, **kwargs):
        raise BlockExtractionStrategyUnavailableError(kwargs.get("bundle_id"))


def _build_app(tmp_path: Path, dispatcher: FakeDispatcher) -> DataExtractorApp:
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
    app.dispatcher = dispatcher
    return app


def test_unavailable_block_strategy_propagates_and_persists_nothing(tmp_path, monkeypatch):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps({
            "type": "object",
            "required": ["document_type"],
            "properties": {"document_type": {"const": "procuracao"}},
        }),
        encoding="utf-8",
    )

    app = _build_app(tmp_path, FakeDispatcher(schema_path))
    input_path = tmp_path / "piece.md"
    input_path.write_text(MEANINGFUL_BODY, encoding="utf-8")

    client = FakeLLMClientRaisingUnavailableStrategy()
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    with pytest.raises(BlockExtractionStrategyUnavailableError):
        app.run_extraction("extr-procuracao", input_path.name, input_path=input_path)

    assert list(Path(app.dirs["extracted"]).iterdir()) == []
