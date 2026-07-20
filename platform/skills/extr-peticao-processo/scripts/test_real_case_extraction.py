#!/usr/bin/env python3
"""
Integration test for extr-peticao-processo using an anonymized fixture built
from a real "petição inicial" (fictional names/documents, same structure).

Runs the real skill dispatch + GeminiLLMClient.generate_structured path.
Skipped automatically when GEMINI_API_KEY is not configured.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[4]
FIXTURE_PATH = SKILL_DIR / "scripts" / "fixtures" / "peticao_inicial_fixture.md"
SCHEMA_PATH = SKILL_DIR / "assets" / "peticao_processo.schema.json"

sys.path.insert(0, str(ROOT_DIR / "packages" / "shared-llm"))


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _build_dispatch():
    client_mod = _load_module_from_path("client_mod", ROOT_DIR / "packages" / "shared-llm" / "client.py")
    sys.modules["client"] = client_mod
    gemini_client_mod = _load_module_from_path(
        "gemini_client_mod", ROOT_DIR / "packages" / "shared-llm" / "gemini_client.py"
    )
    dispatcher_mod = _load_module_from_path(
        "skill_dispatcher_mod", ROOT_DIR / "platform" / "skill-runtime" / "skill_dispatcher.py"
    )
    dispatcher = dispatcher_mod.SkillDispatcher(platform_path=str(ROOT_DIR / "platform"))
    dispatch_result = dispatcher.dispatch("extr-peticao-processo")
    return dispatch_result, gemini_client_mod


MINIMUM_REQUIRED_FIELDS = [
    "document_type",
    "peticao_identification",
    "process_number",
    "parties",
    "representations",
    "valor_da_causa",
    "fatos",
    "fundamentos_legais",
    "teses_juridicas",
    "pedidos",
    "tutela_urgencia",
]


@pytest.fixture(scope="module")
def real_case_result():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY não configurada no ambiente. Pulando teste live com caso real.")

    dispatch_result, gemini_client_mod = _build_dispatch()
    system_prompt = dispatch_result["system_prompt"]
    schema_path = dispatch_result["skill_config"]["schema_ref"]

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    with open(FIXTURE_PATH, encoding="utf-8") as f:
        raw_text = f.read()
        if raw_text.startswith("---"):
            raw_text = raw_text.split("---", 2)[2].strip()

    model = dispatch_result["llm_profile"].get("model", "gemini-3-flash-preview")
    client = gemini_client_mod.GeminiLLMClient(api_key=api_key, model_name=model)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text},
    ]
    return client.generate_structured(messages, schema=schema, bundle_id=dispatch_result["bundle_id"])


def test_extraction_has_no_failed_blocks(real_case_result):
    """Requisito: extração da petição inicial não deve falhar em nenhum bloco (E1/E2 inclusive)."""
    failed_blocks = real_case_result.get("_failed_blocks", [])
    assert not failed_blocks, f"Blocos com ressalvas: {failed_blocks}"


def test_extraction_has_minimum_required_fields(real_case_result):
    for field in MINIMUM_REQUIRED_FIELDS:
        assert field in real_case_result, f"Campo obrigatório ausente: {field}"
        assert real_case_result[field], f"Campo obrigatório vazio: {field}"


def test_pedidos_have_anchors(real_case_result):
    pedidos = real_case_result.get("pedidos", [])
    assert pedidos, "Nenhum pedido extraído"
    for item in pedidos:
        anchors = item.get("anchors")
        assert anchors, f"Item de 'pedidos' sem anchors: {item}"
        for anchor in anchors:
            assert "kind" in anchor
            assert "page_marker" in anchor
            assert "quote" in anchor


def test_pedidos_individualizados_have_anchors(real_case_result):
    pedidos_ind = real_case_result.get("pedidos_individualizados", [])
    assert pedidos_ind, "Nenhum pedido individualizado extraído"
    for item in pedidos_ind:
        anchors = item.get("anchors")
        assert anchors, f"Item de 'pedidos_individualizados' sem anchors: {item}"
        for anchor in anchors:
            assert "kind" in anchor
            assert "page_marker" in anchor
            assert "quote" in anchor


def test_final_json_validates_against_schema(real_case_result):
    import jsonschema
    from jsonschema import RefResolver

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)

    common_schema_path = ROOT_DIR / "packages" / "shared-schemas" / "defs" / "common.schema.json"
    with open(common_schema_path, encoding="utf-8") as f:
        common_schema = json.load(f)

    schemas_dir = ROOT_DIR / "packages" / "shared-schemas"
    store = {
        schema.get("$id", "https://juridico-cli.local/schemas/peticao_processo.schema.json"): schema,
        common_schema.get("$id", "https://juridico-cli.local/schemas/defs/common.schema.json"): common_schema,
    }
    resolver = RefResolver(base_uri=schemas_dir.as_uri() + "/", referrer=schema, store=store)
    validator = jsonschema.Draft202012Validator(schema, resolver=resolver)

    payload = {k: v for k, v in real_case_result.items() if k != "_failed_blocks"}
    errors = list(validator.iter_errors(payload))
    assert not errors, f"Validation failed with errors: {errors}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
