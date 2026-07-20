import json
import sys
from pathlib import Path

import pytest
import yaml


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing import extractor
from data_processing.extractor import DataExtractorApp
from data_processing.orchestrator.stage_router import run_collect_stage


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEANINGFUL_BODY = (
    "Esta contestação apresenta fundamentos jurídicos relevantes, descreve os fatos "
    "do processo e requer a apreciação integral dos pedidos formulados pela parte."
)


class FakeDispatcher:
    def __init__(self, schema_path: Path, *, registered: bool = True):
        self.schema_path = schema_path
        self.registered = registered
        self.calls: list[str] = []

    def dispatch(self, bundle_id: str):
        self.calls.append(bundle_id)
        if not self.registered:
            raise ValueError(f"Skill não registrada: {bundle_id}")
        return {
            "skill_config": {"schema_ref": str(self.schema_path), "profile": "test"},
            "system_prompt": "Extraia os dados.",
            "llm_profile": {},
            "bundle_id": bundle_id,
        }


class FakeLLMClient:
    model_name = "fake-model"

    def __init__(self, response):
        self.response = response
        self.calls: list[dict] = []

    def generate_structured(self, messages, *, schema):
        self.calls.append({"messages": messages, "schema": schema})
        return self.response


class FakeExtractorApp:
    instances = []
    error: Exception | None = None

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.calls: list[dict] = []
        self.__class__.instances.append(self)

    def run_extraction(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return "result.json"


@pytest.fixture(autouse=True)
def reset_fake_extractor():
    FakeExtractorApp.instances = []
    FakeExtractorApp.error = None


def _write_normalized_markdown(path: Path, **frontmatter) -> None:
    path.write_text(
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---\n{MEANINGFUL_BODY}\n",
        encoding="utf-8",
    )


def _run_collect(tmp_path: Path, monkeypatch, **frontmatter) -> FakeExtractorApp:
    staging = tmp_path / "staging"
    staging.mkdir()
    _write_normalized_markdown(staging / "piece.md", **frontmatter)
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(extractor, "DataExtractorApp", FakeExtractorApp)

    run_collect_stage("proc", config_path, staging)

    assert len(FakeExtractorApp.instances) == 1
    return FakeExtractorApp.instances[0]


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


def _write_schema(tmp_path: Path) -> Path:
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(
        json.dumps({
            "type": "object",
            "required": ["accepted"],
            "additionalProperties": False,
            "properties": {"accepted": {"type": "boolean"}},
        }),
        encoding="utf-8",
    )
    return schema_path


def test_ready_approved_registered_skill_is_dispatched_with_staging_path(tmp_path, monkeypatch):
    app = _run_collect(
        tmp_path,
        monkeypatch,
        status="ready",
        review_status="approved",
        skill_key="extr-contestacao-processo",
    )

    assert app.calls == [{
        "bundle_id": "extr-contestacao-processo",
        "input_filename": "piece.md",
        "input_path": tmp_path / "staging" / "piece.md",
    }]


@pytest.mark.parametrize(
    "frontmatter",
    [
        {"status": "needs_review", "review_status": "unroutable", "skill_key": "extr-test"},
        {"status": "ready", "review_status": "unroutable", "skill_key": "extr-test"},
        {"status": "ready", "review_status": "approved", "skill_key": "REVISAR_MANUAL"},
        {"status": "ready", "review_status": "approved", "document_type": "contestacao_processo"},
        {"status": "ready", "review_status": "approved", "skill_key": "contestacao-processo"},
    ],
)
def test_ineligible_frontmatter_never_dispatches(tmp_path, monkeypatch, frontmatter):
    app = _run_collect(tmp_path, monkeypatch, **frontmatter)

    assert app.calls == []


def test_unregistered_skill_is_a_controlled_per_file_rejection(tmp_path, monkeypatch, capsys):
    FakeExtractorApp.error = ValueError("Skill não registrada: extr-inexistente")
    app = _run_collect(
        tmp_path,
        monkeypatch,
        status="ready",
        review_status="approved",
        skill_key="extr-inexistente",
    )

    assert len(app.calls) == 1
    assert "Skill não registrada: extr-inexistente" in capsys.readouterr().out


def test_explicit_staging_path_wins_over_homonymous_legacy_file(tmp_path, monkeypatch):
    schema_path = _write_schema(tmp_path)
    dispatcher = FakeDispatcher(schema_path)
    app = _build_app(tmp_path, dispatcher)
    legacy_path = Path(app.dirs["input_md_frontmatter"]) / "piece.md"
    explicit_path = tmp_path / "custom-staging" / "piece.md"
    explicit_path.parent.mkdir()
    legacy_path.write_text(f"LEGADO {MEANINGFUL_BODY}", encoding="utf-8")
    explicit_path.write_text(f"STAGING EXPLICITO {MEANINGFUL_BODY}", encoding="utf-8")
    client = FakeLLMClient({"accepted": True})
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    app.run_extraction("extr-test", "piece.md", input_path=explicit_path)

    assert "STAGING EXPLICITO" in client.calls[0]["messages"][-1]["content"]
    assert "LEGADO" not in client.calls[0]["messages"][-1]["content"]


def test_valid_response_is_persisted_after_schema_validation(tmp_path, monkeypatch):
    schema_path = _write_schema(tmp_path)
    dispatcher = FakeDispatcher(schema_path)
    app = _build_app(tmp_path, dispatcher)
    input_path = tmp_path / "piece.md"
    input_path.write_text(MEANINGFUL_BODY, encoding="utf-8")
    client = FakeLLMClient({"accepted": True})
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    output_path = Path(
        app.run_extraction("extr-test", input_path.name, input_path=input_path)
    )

    assert dispatcher.calls == ["extr-test"]
    assert json.loads(output_path.read_text(encoding="utf-8")) == {"accepted": True}


def test_invalid_response_is_not_persisted_or_allowed_to_replace_previous_result(
    tmp_path, monkeypatch
):
    schema_path = _write_schema(tmp_path)
    app = _build_app(tmp_path, FakeDispatcher(schema_path))
    input_path = tmp_path / "piece.md"
    input_path.write_text(MEANINGFUL_BODY, encoding="utf-8")
    output_path = Path(app.dirs["extracted"]) / "result_extr-test_piece.json"
    output_path.write_text('{"accepted": true}\n', encoding="utf-8")
    client = FakeLLMClient({"unexpected": "invalid"})
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    with pytest.raises(ValueError, match="Resposta inválida"):
        app.run_extraction("extr-test", input_path.name, input_path=input_path)

    assert output_path.read_text(encoding="utf-8") == '{"accepted": true}\n'
    log_text = "".join(path.read_text(encoding="utf-8") for path in Path(app.dirs["logs"]).glob("*.log"))
    assert "Resposta inválida" in log_text
    assert "Extração concluída com sucesso" not in log_text


def test_unregistered_dispatch_never_creates_llm_client(tmp_path, monkeypatch):
    schema_path = _write_schema(tmp_path)
    app = _build_app(tmp_path, FakeDispatcher(schema_path, registered=False))
    input_path = tmp_path / "piece.md"
    input_path.write_text(MEANINGFUL_BODY, encoding="utf-8")
    monkeypatch.setattr(
        extractor.LLMClientFactory,
        "create_client",
        lambda **kwargs: pytest.fail("LLM não deve ser criado"),
    )

    with pytest.raises(ValueError, match="Skill não registrada"):
        app.run_extraction("extr-inexistente", input_path.name, input_path=input_path)


def test_missing_explicit_path_never_creates_llm_client(tmp_path, monkeypatch):
    schema_path = _write_schema(tmp_path)
    app = _build_app(tmp_path, FakeDispatcher(schema_path))
    monkeypatch.setattr(
        extractor.LLMClientFactory,
        "create_client",
        lambda **kwargs: pytest.fail("LLM não deve ser criado"),
    )

    with pytest.raises(FileNotFoundError, match="Caminho de entrada explícito"):
        app.run_extraction("extr-test", "missing.md", input_path=tmp_path / "missing.md")


def test_legacy_two_argument_call_still_finds_frontmatter_directory(tmp_path, monkeypatch):
    schema_path = _write_schema(tmp_path)
    app = _build_app(tmp_path, FakeDispatcher(schema_path))
    legacy_path = Path(app.dirs["input_md_frontmatter"]) / "legacy.md"
    legacy_path.write_text(MEANINGFUL_BODY, encoding="utf-8")
    client = FakeLLMClient({"accepted": True})
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    output_path = app.run_extraction("extr-test", "legacy.md")

    assert output_path is not None
    assert Path(output_path).exists()
    assert len(client.calls) == 1
