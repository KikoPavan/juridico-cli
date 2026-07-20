import json
import socket
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHARED_SCHEMAS_DIR = PROJECT_ROOT / "packages" / "shared-schemas"
PETICAO_SCHEMA_PATH = (
    PROJECT_ROOT / "platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json"
)

sys.path.insert(0, str(SHARED_SCHEMAS_DIR))
from local_resolver import SchemaReferenceError, load_validator  # noqa: E402

from data_processing import extractor  # noqa: E402
from data_processing.extractor import DataExtractorApp  # noqa: E402


MEANINGFUL_BODY = (
    "Esta petição apresenta fundamentos jurídicos relevantes, descreve os fatos "
    "do processo e requer a apreciação integral dos pedidos formulados pela parte."
)

VALID_PETICAO_PAYLOAD = {
    "document_type": "peticao_processo",
    "valor_da_causa": {
        "value": "R$ 1.000,00",
        "anchors": [
            {"kind": "pagina", "page_marker": "1", "quote": "Valor da causa: R$ 1.000,00"}
        ],
    },
}

INVALID_PETICAO_PAYLOAD = {"document_type": "tipo_invalido"}


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


class FakeLLMClient:
    model_name = "fake-model"

    def __init__(self, response):
        self.response = response
        self.calls: list[dict] = []

    def generate_structured(self, messages, *, schema):
        self.calls.append({"messages": messages, "schema": schema})
        return self.response


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


def test_relative_ref_to_common_schema_is_resolved_locally():
    schema = json.loads(PETICAO_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "defs/common.schema.json#/$defs/NonEmptyString" in json.dumps(schema)

    validator = load_validator(schema, PETICAO_SCHEMA_PATH, SHARED_SCHEMAS_DIR)
    errors = list(validator.iter_errors(VALID_PETICAO_PAYLOAD))

    assert errors == []


def test_absolute_juridico_cli_local_uri_maps_to_same_local_file(tmp_path):
    common_id = "https://juridico-cli.local/schemas/defs/common.schema.json"
    absolute_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://juridico-cli.local/schemas/absolute_ref.schema.json",
        "type": "object",
        "properties": {"nome": {"$ref": f"{common_id}#/$defs/NonEmptyString"}},
    }
    relative_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://juridico-cli.local/schemas/relative_ref.schema.json",
        "type": "object",
        "properties": {"nome": {"$ref": "defs/common.schema.json#/$defs/NonEmptyString"}},
    }

    absolute_path = tmp_path / "absolute_ref.schema.json"
    absolute_path.write_text(json.dumps(absolute_schema), encoding="utf-8")
    relative_path = tmp_path / "relative_ref.schema.json"
    relative_path.write_text(json.dumps(relative_schema), encoding="utf-8")

    absolute_validator = load_validator(absolute_schema, absolute_path, SHARED_SCHEMAS_DIR)
    relative_validator = load_validator(relative_schema, relative_path, SHARED_SCHEMAS_DIR)

    valid_errors_absolute = list(absolute_validator.iter_errors({"nome": "Fulano"}))
    valid_errors_relative = list(relative_validator.iter_errors({"nome": "Fulano"}))
    invalid_errors_absolute = list(absolute_validator.iter_errors({"nome": ""}))
    invalid_errors_relative = list(relative_validator.iter_errors({"nome": ""}))

    assert valid_errors_absolute == valid_errors_relative == []
    assert len(invalid_errors_absolute) == len(invalid_errors_relative) == 1


def test_validation_never_touches_the_network(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("Validação local não deve abrir nenhuma conexão de rede")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)

    schema = json.loads(PETICAO_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = load_validator(schema, PETICAO_SCHEMA_PATH, SHARED_SCHEMAS_DIR)
    errors = list(validator.iter_errors(VALID_PETICAO_PAYLOAD))

    assert errors == []


def test_missing_reference_raises_controlled_schema_reference_error(tmp_path):
    broken_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://juridico-cli.local/schemas/broken.schema.json",
        "type": "object",
        "properties": {"x": {"$ref": "defs/does_not_exist.schema.json#/$defs/X"}},
    }
    schema_path = tmp_path / "broken.schema.json"
    schema_path.write_text(json.dumps(broken_schema), encoding="utf-8")

    with pytest.raises(SchemaReferenceError, match="defs/does_not_exist.schema.json"):
        load_validator(broken_schema, schema_path, SHARED_SCHEMAS_DIR)


def test_valid_response_against_real_schema_with_shared_ref_is_persisted(tmp_path, monkeypatch):
    app = _build_app(tmp_path, FakeDispatcher(PETICAO_SCHEMA_PATH))
    input_path = tmp_path / "piece.md"
    input_path.write_text(MEANINGFUL_BODY, encoding="utf-8")
    client = FakeLLMClient(VALID_PETICAO_PAYLOAD)
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    output_path = Path(
        app.run_extraction("extr-peticao-processo", input_path.name, input_path=input_path)
    )

    assert json.loads(output_path.read_text(encoding="utf-8")) == VALID_PETICAO_PAYLOAD


def test_invalid_response_against_real_schema_with_shared_ref_is_not_persisted(tmp_path, monkeypatch):
    app = _build_app(tmp_path, FakeDispatcher(PETICAO_SCHEMA_PATH))
    input_path = tmp_path / "piece.md"
    input_path.write_text(MEANINGFUL_BODY, encoding="utf-8")
    output_path = Path(app.dirs["extracted"]) / "result_extr-peticao-processo_piece.json"
    output_path.write_text('{"previous": true}\n', encoding="utf-8")
    client = FakeLLMClient(INVALID_PETICAO_PAYLOAD)
    monkeypatch.setattr(extractor.LLMClientFactory, "create_client", lambda **kwargs: client)

    with pytest.raises(ValueError, match="Resposta inválida"):
        app.run_extraction("extr-peticao-processo", input_path.name, input_path=input_path)

    assert output_path.read_text(encoding="utf-8") == '{"previous": true}\n'
