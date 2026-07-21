#!/usr/bin/env python3
"""
Testes de seleção de estratégia de Extração por Blocos
(packages/shared-llm/block_strategies.py): resolução por bundle_id,
isolamento de campos entre extr-peticao-processo e extr-contestacao-processo,
falha controlada para skills sem estratégia, e sanitização de page_marker.

Usa exclusivamente um fake client (mock de generate_content); nenhuma
chamada real ao Gemini é feita nesta suíte.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "packages" / "shared-llm"))


def _load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


client_mod = _load_module_from_path("client_mod", ROOT_DIR / "packages" / "shared-llm" / "client.py")
sys.modules["client"] = client_mod

block_strategies_mod = _load_module_from_path(
    "block_strategies", ROOT_DIR / "packages" / "shared-llm" / "block_strategies.py"
)

gemini_client_mod = _load_module_from_path(
    "gemini_client_mod", ROOT_DIR / "packages" / "shared-llm" / "gemini_client.py"
)

GeminiLLMClient = gemini_client_mod.GeminiLLMClient
PeticaoBlockStrategy = block_strategies_mod.PeticaoBlockStrategy
ContestacaoBlockStrategy = block_strategies_mod.ContestacaoBlockStrategy
DecisaoBlockStrategy = block_strategies_mod.DecisaoBlockStrategy
BlockExtractionStrategyUnavailableError = block_strategies_mod.BlockExtractionStrategyUnavailableError
resolve_block_strategy = block_strategies_mod.resolve_block_strategy
sanitize_anchor_page_marker = block_strategies_mod.sanitize_anchor_page_marker

SHARED_SCHEMAS_DIR = ROOT_DIR / "packages" / "shared-schemas"
sys.path.insert(0, str(SHARED_SCHEMAS_DIR))
from local_resolver import load_validator  # noqa: E402

CONTESTACAO_SCHEMA_PATH = (
    ROOT_DIR / "platform" / "skills" / "extr-contestacao-processo" / "assets" / "contestacao_processo.schema.json"
)
PETICAO_SCHEMA_PATH = ROOT_DIR / "platform" / "skills" / "extr-peticao-processo" / "assets" / "peticao_processo.schema.json"
DECISAO_SCHEMA_PATH = (
    ROOT_DIR / "platform" / "skills" / "extr-decisao-processo" / "assets" / "decisao_processo.schema.json"
)

PETICAO_ONLY_FIELDS = {
    "peticao_identification", "valor_da_causa", "fatos", "fatos_cronologicos",
    "atos_juridicos", "documentos_citados", "fundamentos_legais", "teses_juridicas",
    "processos_relacionados", "pedidos", "pedidos_individualizados",
    "tutela_urgencia", "provas_requeridas", "riscos_ou_pontos_de_atencao",
}
CONTESTACAO_ONLY_FIELDS = {
    "contestacao_identification", "preliminares", "merito",
    "provas_e_requerimentos", "pedidos_finais",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _minimal_mock_generate(document_type):
    """Fake generate_content que só devolve document_type — o preenchimento
    de defaults de cada estratégia é responsável por completar o resto com
    os TIPOS corretos dessa skill."""
    def _side_effect(*args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.text = json.dumps({"document_type": document_type})
        return mock_resp
    return MagicMock(side_effect=_side_effect)


# ---------------------------------------------------------------------------
# Resolução de estratégia por bundle_id
# ---------------------------------------------------------------------------

def test_bundle_id_extr_peticao_resolves_peticao_strategy():
    assert resolve_block_strategy("extr-peticao-processo") is PeticaoBlockStrategy


def test_bundle_id_extr_contestacao_resolves_contestacao_strategy():
    assert resolve_block_strategy("extr-contestacao-processo") is ContestacaoBlockStrategy


def test_bundle_id_extr_decisao_resolves_decisao_strategy():
    assert resolve_block_strategy("extr-decisao-processo") is DecisaoBlockStrategy


def test_unregistered_bundle_id_raises_without_using_peticao_strategy():
    with pytest.raises(BlockExtractionStrategyUnavailableError):
        resolve_block_strategy("extr-procuracao")


def test_bundle_id_without_strategy_never_calls_gemini(tmp_path):
    client = GeminiLLMClient(api_key="mock")
    mock_generate = MagicMock()
    messages = [{"role": "user", "content": "texto qualquer"}]
    schema = {"type": "object", "required": ["document_type"], "properties": {"document_type": {"const": "procuracao"}}}

    with patch.object(client.client.models, "generate_content", mock_generate):
        with pytest.raises(BlockExtractionStrategyUnavailableError):
            client._dispatch_block_extraction("extr-procuracao", messages, schema, str(tmp_path), 2000, str(ROOT_DIR))

    assert mock_generate.call_count == 0


# ---------------------------------------------------------------------------
# bundle_id determina a estratégia (isolamento de campos entre skills)
# ---------------------------------------------------------------------------

def test_bundle_id_determines_which_strategy_and_fields_are_used(tmp_path):
    peticao_schema = load_json(PETICAO_SCHEMA_PATH)
    contestacao_schema = load_json(CONTESTACAO_SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")
    messages = [{"role": "user", "content": "Texto genérico de entrada."}]

    with patch.object(client.client.models, "generate_content", _minimal_mock_generate("peticao_processo")):
        peticao_result = client._dispatch_block_extraction(
            "extr-peticao-processo", messages, peticao_schema, str(tmp_path), 2000, str(ROOT_DIR)
        )

    with patch.object(client.client.models, "generate_content", _minimal_mock_generate("contestacao_processo")):
        contestacao_result = client._dispatch_block_extraction(
            "extr-contestacao-processo", messages, contestacao_schema, str(tmp_path), 2000, str(ROOT_DIR)
        )

    # A extração de petição nunca recebe campos exclusivos de contestação, e
    # vice-versa — o bundle_id determina exclusivamente o conjunto de campos.
    assert set(peticao_result.keys()) & CONTESTACAO_ONLY_FIELDS == set()
    assert set(contestacao_result.keys()) & PETICAO_ONLY_FIELDS == set()

    assert "pedidos" in peticao_result
    assert "pedidos_finais" in contestacao_result


# ---------------------------------------------------------------------------
# ContestacaoBlockStrategy: só produz propriedades do schema de contestação
# ---------------------------------------------------------------------------

def _contestacao_payload_for(properties_requested):
    payload = {"document_type": "contestacao_processo"}
    if "process_number" in properties_requested:
        payload["process_number"] = {
            "value": "0001234-56.2026.8.26.0100",
            "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Processo nº 0001234"}],
        }
    if "parties" in properties_requested:
        payload["parties"] = []
    if "representations" in properties_requested:
        payload["representations"] = []
    if "contestacao_identification" in properties_requested:
        payload["contestacao_identification"] = {
            "value": "CONTESTAÇÃO",
            "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "CONTESTAÇÃO"}],
        }
    if "preliminares" in properties_requested:
        payload["preliminares"] = [{
            "text": "Inépcia da inicial por ausência de causa de pedir.",
            "anchors": [{"kind": "pagina", "page_marker": "2", "quote": "Inépcia da inicial"}],
        }]
    if "merito" in properties_requested:
        payload["merito"] = [{
            "text": "Impugna especificamente os fatos narrados na inicial.",
            "anchors": [{"kind": "pagina", "page_marker": "3", "quote": "Impugna especificamente"}],
        }]
    if "provas_e_requerimentos" in properties_requested:
        payload["provas_e_requerimentos"] = []
    if "pedidos_finais" in properties_requested:
        payload["pedidos_finais"] = [{
            "text": "Seja julgada totalmente improcedente a ação.",
            "anchors": [{"kind": "pagina", "page_marker": "4", "quote": "totalmente improcedente"}],
        }]
    return payload


def _mock_generate_content_for_contestacao(*args, **kwargs):
    config = kwargs.get("config")
    block_schema = getattr(config, "response_json_schema", None) or {}
    properties_requested = set(block_schema.get("properties", {}).keys())
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(_contestacao_payload_for(properties_requested))
    return mock_resp


def test_bundle_id_extr_contestacao_produces_only_contestacao_fields(tmp_path):
    schema = load_json(CONTESTACAO_SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")
    mock_generate = MagicMock(side_effect=_mock_generate_content_for_contestacao)
    messages = [{
        "role": "user",
        "content": "PRELIMINAR\nInépcia da inicial.\nMÉRITO\nImpugna os fatos.\nDOS PEDIDOS FINAIS\nJulgar improcedente.",
    }]

    with patch.object(client.client.models, "generate_content", mock_generate):
        result = client._dispatch_block_extraction(
            "extr-contestacao-processo", messages, schema, str(tmp_path), 2000, str(ROOT_DIR)
        )

    assert result["document_type"] == "contestacao_processo"
    assert not (set(result.keys()) & PETICAO_ONLY_FIELDS)

    payload = {k: v for k, v in result.items() if k != "_failed_blocks"}
    validator = load_validator(schema, CONTESTACAO_SCHEMA_PATH, SHARED_SCHEMAS_DIR)
    errors = list(validator.iter_errors(payload))
    assert errors == [], f"Erros de validação: {errors}"


def test_contestacao_result_passes_official_validate_output_script(tmp_path):
    schema = load_json(CONTESTACAO_SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")
    mock_generate = MagicMock(side_effect=_mock_generate_content_for_contestacao)
    messages = [{
        "role": "user",
        "content": "PRELIMINAR\nInépcia da inicial.\nMÉRITO\nImpugna os fatos.\nDOS PEDIDOS FINAIS\nJulgar improcedente.",
    }]

    with patch.object(client.client.models, "generate_content", mock_generate):
        result = client._dispatch_block_extraction(
            "extr-contestacao-processo", messages, schema, str(tmp_path), 2000, str(ROOT_DIR)
        )

    payload = {k: v for k, v in result.items() if k != "_failed_blocks"}
    result_path = tmp_path / "resultado_contestacao.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    validate_script = (
        ROOT_DIR / "platform" / "skills" / "extr-contestacao-processo" / "scripts" / "validate_output.py"
    )
    proc = subprocess.run(
        [sys.executable, str(validate_script), "--input", str(result_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


def test_contestacao_deterministic_fallback_returns_empty_when_no_heading(tmp_path):
    """Sem cabeçalho estrutural de preliminares/mérito/pedidos, o fallback
    determinístico de contestação retorna listas vazias — nunca conteúdo de
    petição nem dado inventado."""
    schema = load_json(CONTESTACAO_SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")

    def _always_fail(*args, **kwargs):
        raise Exception("Falha simulada de chamada estruturada e de fallback livre")

    messages = [{"role": "user", "content": "Texto sem nenhuma seção estrutural reconhecível."}]

    with patch.object(client.client.models, "generate_content", MagicMock(side_effect=_always_fail)):
        result = client._dispatch_block_extraction(
            "extr-contestacao-processo", messages, schema, str(tmp_path), 2000, str(ROOT_DIR)
        )

    assert result.get("preliminares") == []
    assert result.get("merito") == []
    assert not (set(result.keys()) & PETICAO_ONLY_FIELDS)


# ---------------------------------------------------------------------------
# Sanitização de page_marker
# ---------------------------------------------------------------------------

def test_sanitize_anchor_page_marker_replaces_bracket_and_empty_values():
    obj = {
        "anchors": [
            {"kind": "pagina", "page_marker": "[]", "quote": "a"},
            {"kind": "pagina", "page_marker": "[ ]", "quote": "b"},
            {"kind": "pagina", "page_marker": "", "quote": "c"},
            {"kind": "pagina", "page_marker": "7", "quote": "d"},
        ]
    }
    sanitize_anchor_page_marker(obj, fallback_page="3")
    markers = [a["page_marker"] for a in obj["anchors"]]
    assert markers == ["3", "3", "3", "7"]


def test_page_marker_bracket_value_from_llm_is_sanitized_in_consolidation(tmp_path):
    schema = load_json(CONTESTACAO_SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")

    def _side_effect(*args, **kwargs):
        config = kwargs.get("config")
        block_schema = getattr(config, "response_json_schema", None) or {}
        properties_requested = set(block_schema.get("properties", {}).keys())
        payload = {"document_type": "contestacao_processo"}
        if "process_number" in properties_requested:
            payload["process_number"] = {
                "value": "0001234-56.2026.8.26.0100",
                "anchors": [{"kind": "pagina", "page_marker": "[]", "quote": "Processo"}],
            }
        mock_resp = MagicMock()
        mock_resp.text = json.dumps(payload)
        return mock_resp

    messages = [{"role": "user", "content": "[[Pág. 1]]\nTexto do processo."}]

    with patch.object(client.client.models, "generate_content", MagicMock(side_effect=_side_effect)):
        result = client._dispatch_block_extraction(
            "extr-contestacao-processo", messages, schema, str(tmp_path), 2000, str(ROOT_DIR)
        )

    assert '"page_marker": "[]"' not in json.dumps(result)
    assert result["process_number"]["anchors"][0]["page_marker"] != "[]"
    assert result["process_number"]["anchors"][0]["page_marker"] == "1"


# ---------------------------------------------------------------------------
# DecisaoBlockStrategy: schema estrito, locators reais e fallback local
# ---------------------------------------------------------------------------

DECISAO_ALLOWED_FIELDS = {
    "document_type",
    "process_number",
    "decision_type",
    "decision_date",
    "decisor",
    "relatorio",
    "fundamentacao",
    "dispositivo",
    "outcome",
    "determinacoes",
    "anchors",
}
DECISAO_BLOCK_FIELDS = [
    {"document_type", "process_number", "decision_type", "decision_date", "decisor", "anchors"},
    {"document_type", "relatorio"},
    {"document_type", "fundamentacao"},
    {"document_type", "dispositivo", "outcome"},
    {"document_type", "determinacoes"},
]
DECISAO_LOCATOR_1 = (
    '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", '
    'event="32", document_code="DESPADEC1", page="1"]]'
)
DECISAO_LOCATOR_2 = (
    '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", '
    'event="32", document_code="DESPADEC1", page="2"]]'
)
DECISAO_MARKDOWN = f"""{DECISAO_LOCATOR_1}
PROCESSO 4000153-37.2026.8.26.0136/SP
DESPACHO
# RELATÓRIO
AUTOR: JURACI PIRES PAVAN. RÉU: BANCO DO BRASIL SA. Documento do evento 18.
# FUNDAMENTAÇÃO
A tutela exige probabilidade do direito e perigo de dano.
{DECISAO_LOCATOR_2}
# DISPOSITIVO
DEFIRO a tutela de urgência requerida.
INTIME-SE a parte ré no prazo de 15 dias.
"""


def _decision_payload(properties_requested, marker=DECISAO_LOCATOR_1):
    payload = {"document_type": "decisao_processo"}
    if "process_number" in properties_requested:
        payload["process_number"] = {
            "value": "4000153-37.2026.8.26.0136/SP",
            "anchors": [{"kind": "pagina", "page_marker": marker, "quote": "4000153-37.2026.8.26.0136/SP"}],
        }
    if "decision_type" in properties_requested:
        payload["decision_type"] = {
            "value": "despacho",
            "value_raw": "DESPACHO",
            "anchors": [{"kind": "pagina", "page_marker": marker, "quote": "DESPACHO"}],
        }
    if "decision_date" in properties_requested:
        payload["decision_date"] = {
            "value": "2026-04-27",
            "anchors": [{"kind": "pagina", "page_marker": marker, "quote": "27/04/2026"}],
        }
    if "decisor" in properties_requested:
        payload["decisor"] = {
            "name": "MARCOS ROGÉRIO SANCHES CRUZ GERALDO",
            "anchors": [{"kind": "pagina", "page_marker": marker, "quote": "MARCOS ROGÉRIO"}],
        }
    if "anchors" in properties_requested:
        payload["anchors"] = [{"kind": "pagina", "page_marker": marker, "quote": "DESPACHO"}]
    if "relatorio" in properties_requested:
        payload["relatorio"] = [{
            "text": "AUTOR: JURACI PIRES PAVAN. RÉU: BANCO DO BRASIL SA. Documento do evento 18.",
            "anchors": [{"kind": "pagina", "page_marker": marker, "quote": "AUTOR: JURACI PIRES PAVAN"}],
        }]
    if "fundamentacao" in properties_requested:
        payload["fundamentacao"] = [{
            "text": "A tutela exige probabilidade do direito e perigo de dano.",
            "anchors": [{"kind": "pagina", "page_marker": marker, "quote": "probabilidade do direito"}],
        }]
    if "dispositivo" in properties_requested:
        payload["dispositivo"] = [{
            "text": "DEFIRO a tutela de urgência requerida.",
            "anchors": [{"kind": "pagina", "page_marker": DECISAO_LOCATOR_2, "quote": "DEFIRO a tutela"}],
        }]
    if "outcome" in properties_requested:
        payload["outcome"] = {
            "value": "deferiu",
            "value_raw": "DEFIRO",
            "anchors": [{"kind": "pagina", "page_marker": DECISAO_LOCATOR_2, "quote": "DEFIRO"}],
        }
    if "determinacoes" in properties_requested:
        payload["determinacoes"] = [{
            "text": "INTIME-SE a parte ré no prazo de 15 dias.",
            "anchors": [{"kind": "pagina", "page_marker": DECISAO_LOCATOR_2, "quote": "INTIME-SE"}],
        }]
    return payload


def _mock_generate_content_for_decisao(*args, **kwargs):
    config = kwargs["config"]
    block_schema = getattr(config, "response_json_schema", None) or {}
    properties_requested = set(block_schema.get("properties", {}))
    response = MagicMock()
    response.text = json.dumps(_decision_payload(properties_requested), ensure_ascii=False)
    return response


def _run_decisao(tmp_path, generate_content=_mock_generate_content_for_decisao, schema=None, markdown=DECISAO_MARKDOWN):
    schema = schema or load_json(DECISAO_SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")
    mock_generate = MagicMock(side_effect=generate_content)
    messages = [{"role": "user", "content": markdown}]
    with patch.object(client.client.models, "generate_content", mock_generate):
        result = client._dispatch_block_extraction(
            "extr-decisao-processo", messages, schema, str(tmp_path), 2000, str(ROOT_DIR)
        )
    return result, mock_generate


def test_decisao_uses_five_schema_derived_blocks_and_only_allowed_fields(tmp_path):
    result, mock_generate = _run_decisao(tmp_path)

    assert mock_generate.call_count == 5
    requested = []
    for call in mock_generate.call_args_list:
        normalized_schema = call.kwargs["config"].response_json_schema
        requested.append(set(normalized_schema["properties"]))
    assert requested == DECISAO_BLOCK_FIELDS
    assert set(result) <= DECISAO_ALLOWED_FIELDS
    assert not (set(result) & PETICAO_ONLY_FIELDS)
    assert not (set(result) & CONTESTACAO_ONLY_FIELDS)
    assert "AUTOR:" in result["relatorio"][0]["text"]
    assert "Documento do evento 18" in result["relatorio"][0]["text"]
    assert "prazo de 15 dias" in result["determinacoes"][0]["text"]


def test_decisao_preserves_real_judicial_locator_and_validates_schema(tmp_path):
    schema = load_json(DECISAO_SCHEMA_PATH)
    result, _ = _run_decisao(tmp_path, schema=schema)

    markers = [anchor["page_marker"] for anchor in DecisaoBlockStrategy._iter_anchors(result)]
    assert DECISAO_LOCATOR_1 in markers
    assert DECISAO_LOCATOR_2 in markers
    assert "[]" not in markers
    validator = load_validator(schema, DECISAO_SCHEMA_PATH, SHARED_SCHEMAS_DIR)
    assert list(validator.iter_errors(result)) == []


def test_decisao_invalid_marker_rejects_block_and_uses_local_fallback(tmp_path, caplog):
    def _invalid_marker(*args, **kwargs):
        requested = set(kwargs["config"].response_json_schema.get("properties", {}))
        response = MagicMock()
        response.text = json.dumps(_decision_payload(requested, marker="[]"), ensure_ascii=False)
        return response

    result, _ = _run_decisao(tmp_path, generate_content=_invalid_marker)

    markers = [anchor["page_marker"] for anchor in DecisaoBlockStrategy._iter_anchors(result)]
    assert markers
    assert set(markers) <= {DECISAO_LOCATOR_1, DECISAO_LOCATOR_2}
    assert "fallback local determinístico" in caplog.text
    assert "Bloco IDENTIFICACAO" in caplog.text


def test_decisao_fallback_without_marker_does_not_fabricate_anchor(tmp_path):
    def _always_fail(*args, **kwargs):
        raise RuntimeError("falha Gemini simulada")

    markdown = "DESPACHO\n# FUNDAMENTAÇÃO\nTexto literal sem qualquer marcador de página."
    result, mock_generate = _run_decisao(tmp_path, generate_content=_always_fail, markdown=markdown)

    assert mock_generate.call_count == 5
    assert list(DecisaoBlockStrategy._iter_anchors(result)) == []
    assert result.get("fundamentacao") == []
    assert "process_number" not in result


def test_decisao_invalid_consolidation_raises_before_return(tmp_path):
    schema = load_json(DECISAO_SCHEMA_PATH)
    schema["minProperties"] = 100

    def _always_fail(*args, **kwargs):
        raise RuntimeError("falha Gemini simulada")

    with pytest.raises(ValueError, match="schema completo"):
        _run_decisao(
            tmp_path,
            generate_content=_always_fail,
            schema=schema,
            markdown=f"{DECISAO_LOCATOR_1}\nDESPACHO sem comando decisório explícito.",
        )


def test_decisao_result_passes_official_validate_output_script(tmp_path):
    result, _ = _run_decisao(tmp_path)
    result_path = tmp_path / "resultado_decisao.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    validate_script = (
        ROOT_DIR / "platform" / "skills" / "extr-decisao-processo" / "scripts" / "validate_output.py"
    )

    proc = subprocess.run(
        [sys.executable, str(validate_script), "--input", str(result_path)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout
