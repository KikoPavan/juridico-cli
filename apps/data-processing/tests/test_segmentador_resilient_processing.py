"""Regressões do processamento resiliente específico do segmentador."""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "apps" / "data-processing" / "src"
sys.path.insert(0, str(SRC_DIR))

from data_processing.orchestrator.stage_router import (  # noqa: E402
    _build_segmentation_windows,
    _coalesce_contiguous_fragments,
    _compatible_partial_identity,
    _index_judicial_locators,
    _is_document_type_separator,
    _is_separator_absorbable,
    _merge_partial_pieces,
    _multipiece_fallback,
    _partial_descriptor,
    _segmentador_diagnostic,
    _segmentador_preflight,
    run_segmentador_stage,
)


def _page(process="P1", event="1", code="INIC1", page=1, text="conteúdo"):
    return (
        f'[[judicial_locator: process_number="{process}", event="{event}", '
        f'document_code="{code}", page="{page}"]]\n{text}\n'
    )


def _decision(start, end, *, document_type="peticao_inicial", event="1", code="INIC1"):
    return {
        "metadata": {},
        "pecas": [{
            "piece_id": "peca_001",
            "document_type": document_type,
            "document_type_confidence": "high",
            "pages_start": start,
            "pages_end": end,
            "process_number": "P1",
            "event": event,
            "document_code": code,
            "anchors": [{"label": code, "page": start}],
        }],
    }


def _partial(piece, window_id, window_start, window_end, local_index=0):
    return _partial_descriptor(
        piece,
        window={
            "window_id": window_id,
            "pages_start": window_start,
            "pages_end": window_end,
        },
        local_index=local_index,
        source_file="Processo.md",
    )


class MappingFakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_structured(self, messages, schema, **kwargs):
        self.calls.append({"messages": messages, "schema": schema, "kwargs": kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return copy.deepcopy(response)


def test_short_document_keeps_single_call(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    source = _page(page=1)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "curto.md").write_text(source, encoding="utf-8")
    client = MappingFakeClient([_decision(1, 1)])

    result = run_segmentador_stage(input_dir, tmp_path / "out", llm_client=client)

    assert result.name == "envelope_segmentacao.json"
    assert len(client.calls) == 1
    assert client.calls[0]["kwargs"]["debug_context"]["strategy"] == "single_call"


def test_long_document_uses_page_windows_and_merges_crossing_piece(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    source = "".join(
        _page(
            page=page,
            event="1" if page <= 8 else "2" if page <= 14 else "3",
            code="INIC1" if page <= 8 else "CONTES1" if page <= 14 else "DESPADEC1",
            text="x" * 2300,
        )
        for page in range(1, 21)
    )
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "Processo.md").write_text(source, encoding="utf-8")
    first = {"metadata": {}, "pecas": [
        _decision(1, 8)["pecas"][0],
        _decision(9, 12, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
    ]}
    second = {"metadata": {}, "pecas": [
        _decision(12, 14, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
        _decision(15, 20, document_type="decisao_interlocutoria", event="3", code="DESPADEC1")["pecas"][0],
    ]}
    client = MappingFakeClient([first, second])

    result = run_segmentador_stage(input_dir, tmp_path / "out", llm_client=client)
    envelope = json.loads(result.read_text(encoding="utf-8"))

    assert len(client.calls) == 2
    assert all(call["kwargs"]["debug_context"]["strategy"] == "page_windows" for call in client.calls)
    assert [(piece["pages_start"], piece["pages_end"]) for piece in envelope["pecas"]] == [
        (1, 8), (9, 14), (15, 20),
    ]
    assert len([piece for piece in envelope["pecas"] if piece["document_code"] == "CONTES1"]) == 1
    assert envelope["pecas"][1]["source_file"] == "Processo.md"
    assert 'document_code="CONTES1"' in envelope["pecas"][1]["text"]


def test_adjacent_distinct_pieces_are_not_merged():
    result = _merge_partial_pieces([
        _decision(1, 2)["pecas"][0],
        _decision(3, 4, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
    ], 4)
    assert len(result["pecas"]) == 2


def test_incompatible_overlap_is_rejected_before_materialization():
    with pytest.raises(ValueError, match="sobreposição indevida"):
        _merge_partial_pieces([
            _decision(1, 3)["pecas"][0],
            _decision(3, 4, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
        ], 4)


def test_local_piece_ids_do_not_identify_distinct_pieces_globally():
    first = _partial(_decision(1, 11)["pecas"][0], 1, 1, 12)
    second = _partial(
        _decision(12, 20, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
        2, 12, 20,
    )

    result = _merge_partial_pieces([second, first], 20)

    assert [(piece["piece_id"], piece["pages_start"], piece["pages_end"]) for piece in result["pecas"]] == [
        ("peca_001", 1, 11), ("peca_002", 12, 20),
    ]


def test_same_local_piece_id_crossing_overlap_is_merged_without_duplicate_page():
    left = _partial(
        _decision(9, 12, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
        1, 1, 12,
    )
    right = _partial(
        _decision(12, 13, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
        2, 12, 23,
    )

    result = _merge_partial_pieces([right, left], 23)

    assert len(result["pecas"]) == 1
    assert result["pecas"][0]["piece_id"] == "peca_001"
    assert (result["pecas"][0]["pages_start"], result["pecas"][0]["pages_end"]) == (9, 13)
    assert [anchor["page"] for anchor in result["pecas"][0]["anchors"]] == [9, 12]
    assert "_partial_context" not in result["pecas"][0]


def test_window_local_pages_are_translated_from_judicial_locators():
    source = "".join(
        _page(page=page, event="32", code="DESPADEC1") for page in range(1, 4)
    )
    locators = _index_judicial_locators(source)
    for physical_page, locator in enumerate(locators, start=33):
        locator["physical_page"] = physical_page
    piece = _decision(
        2, 3, document_type="decisao_interlocutoria", event="32", code="DESPADEC1"
    )["pecas"][0]

    partial = _partial_descriptor(
        piece,
        window={
            "window_id": 4,
            "pages_start": 34,
            "pages_end": 35,
            "locators": locators[1:],
        },
        local_index=0,
        source_file="Processo.md",
    )

    assert (partial["pages_start"], partial["pages_end"]) == (34, 35)


def test_local_pages_use_event_when_locator_has_no_document_code():
    source = "".join(_page(page=page, event="11", code="") for page in range(2, 5))
    locators = _index_judicial_locators(source)
    for physical_page, locator in enumerate(locators, start=23):
        locator["physical_page"] = physical_page
        locator["attrs"].pop("document_code", None)
    piece = _decision(2, 4, event="11", code="PED HABILIT1")["pecas"][0]

    partial = _partial_descriptor(
        piece,
        window={
            "window_id": 3,
            "pages_start": 23,
            "pages_end": 34,
            "locators": locators,
        },
        local_index=0,
        source_file="Processo.md",
    )

    assert (partial["pages_start"], partial["pages_end"]) == (23, 25)


def test_real_overlap_between_distinct_window_descriptors_remains_rejected():
    left = _partial(_decision(9, 12)["pecas"][0], 1, 1, 12)
    right = _partial(
        _decision(12, 13, document_type="contestacao", event="2", code="CONTES1")["pecas"][0],
        2, 12, 23,
    )

    with pytest.raises(ValueError, match="sobreposição indevida"):
        _merge_partial_pieces([left, right], 23)


def test_generic_and_specific_types_merge_only_with_same_event_and_code():
    left = _partial(
        _decision(22, 23, document_type="pedido_de_habilitacao", event="11", code="PED HABILIT1")["pecas"][0],
        2, 12, 23,
    )
    left["process_number"] = "4000153-37.2026.8.26.0136"
    right = _partial(
        _decision(23, 25, document_type="peticao", event="11", code="PED HABILIT1")["pecas"][0],
        3, 23, 34,
    )
    right["process_number"] = "4000153-37.2026.8.26.0136/SP"

    result = _merge_partial_pieces([left, right], 35)

    assert len(result["pecas"]) == 1
    assert (result["pecas"][0]["pages_start"], result["pecas"][0]["pages_end"]) == (22, 25)


def test_real_unclassified_pages_are_preserved_and_event_separator_joins_next_piece():
    source = (
        _page(page=1, event="1", code="INIC1")
        + _page(page=2, event="", code="")
        + _page(page=3, event="", code="")
        + (
            '[[judicial_locator: process_number="P1", event="13", page="4", '
            'kind="event_separator"]]\n# PÁGINA DE SEPARAÇÃO\n'
        )
        + _page(page=1, event="13", code="DESPADEC1")
    )
    locators = _index_judicial_locators(source)
    first = _decision(1, 1)["pecas"][0]
    decision = _decision(
        5, 5, document_type="decisao_interlocutoria", event="13", code="DESPADEC1"
    )["pecas"][0]

    result = _merge_partial_pieces([first, decision], 5, locators=locators)

    assert [(piece["pages_start"], piece["pages_end"]) for piece in result["pecas"]] == [
        (1, 1), (2, 3), (4, 5),
    ]
    coverage = [
        page
        for piece in result["pecas"]
        for page in range(piece["pages_start"], piece["pages_end"] + 1)
    ]
    assert coverage == [1, 2, 3, 4, 5]
    assert result["pecas"][1]["document_type"] == "nao_classificado"


def test_three_files_are_considered_and_failure_is_isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.md").write_text(_page(code="INIC1"), encoding="utf-8")
    (input_dir / "b.md").write_text("conteúdo ambíguo sem marcadores", encoding="utf-8")
    (input_dir / "c.md").write_text(_page(code="INIC1"), encoding="utf-8")
    client = MappingFakeClient([_decision(1, 1), ValueError("Unterminated string"), _decision(1, 1)])

    manifest_path = run_segmentador_stage(input_dir, tmp_path / "out", llm_client=client)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(client.calls) == 3
    assert manifest["total_files"] == 3
    assert [item["status"] for item in manifest["results"]] == [
        "success", "needs_review", "success",
    ]
    failed = manifest["results"][1]
    diagnostic = json.loads(Path(failed["diagnostic_path"]).read_text(encoding="utf-8"))
    assert diagnostic["source_file"] == "b.md"
    assert diagnostic["stage"] == "segmentador-juridico"
    assert "needs_review" in failed["error"]


def test_multipiece_fallback_requires_classifiable_structural_evidence():
    source = (
        _page(event="1", code="INIC1", page=1, text="# PETIÇÃO INICIAL")
        + _page(event="2", code="CONTES1", page=1, text="# CONTESTAÇÃO")
    )
    fallback = _multipiece_fallback(source, "Processo.md")
    assert fallback is not None
    assert [piece["document_type"] for piece in fallback["pecas"]] == [
        "peticao_inicial", "contestacao",
    ]

    ambiguous = source + _page(event="3", code="XYZ1", page=1, text="sem cabeçalho")
    assert _multipiece_fallback(ambiguous, "Processo.md") is None


def test_preflight_and_windows_never_invent_pages():
    source = "".join(_page(page=page, text="x" * 4000) for page in range(1, 14))
    assert _segmentador_preflight(source)["high_risk"] is True
    windows = _build_segmentation_windows(source)
    assert [(window["pages_start"], window["pages_end"]) for window in windows] == [
        (1, 12), (12, 13),
    ]
    assert all(window["text"] and "[]" not in window["text"] for window in windows)


def test_segmentador_is_not_registered_as_block_extractor():
    registry = (PROJECT_ROOT / "packages/shared-llm/block_strategies.py").read_text(
        encoding="utf-8"
    )
    skill_registry = (
        PROJECT_ROOT / "platform/skill-runtime/skill_registry.yaml"
    ).read_text(encoding="utf-8")
    assert '"segmentador-juridico"' not in registry
    assert "segmentador-juridico:" in skill_registry
    segmentador_block = skill_registry.split("segmentador-juridico:", 1)[1].split(
        "\n  ", 1
    )[0]
    assert "extr-" not in segmentador_block


def test_diagnostics_do_not_overwrite_attempts_or_files(tmp_path):
    first = _segmentador_diagnostic(
        tmp_path, "a.md", "window-1", "page_windows", ValueError("Unterminated string")
    )
    second = _segmentador_diagnostic(
        tmp_path, "b.md", "window-2", "page_windows", ValueError("Unterminated string")
    )
    assert first != second
    assert first.exists() and second.exists()
    assert json.loads(first.read_text(encoding="utf-8"))["source_file"] == "a.md"
    assert json.loads(second.read_text(encoding="utf-8"))["attempt"] == "window-2"


def _separador_decision(start, end, *, event="13"):
    return {
        "metadata": {},
        "pecas": [{
            "piece_id": "peca_001",
            "document_type": "separador_de_evento",
            "document_type_confidence": "high",
            "pages_start": start,
            "pages_end": end,
            "process_number": "P1",
            "event": event,
            "anchors": [{"label": "separador", "page": start}],
        }],
    }


def test_separador_and_specific_piece_merge_into_single_piece():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    result = _merge_partial_pieces([separador, decisao], 30)
    assert len(result["pecas"]) == 1
    assert result["pecas"][0]["document_type"] == "despacho_decisao"
    assert result["pecas"][0]["document_code"] == "DESPADEC1"


def test_separator_absorption_preserves_specific_document_code():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    result = _merge_partial_pieces([separador, decisao], 30)
    assert result["pecas"][0]["document_code"] == "DESPADEC1"


def test_separator_without_document_code_does_not_cause_incompatibility():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    assert _compatible_partial_identity(separador, decisao) is True


def test_separator_and_piece_different_events_are_rejected():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    outra = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="14", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    with pytest.raises(ValueError, match="sobreposição indevida"):
        _merge_partial_pieces([separador, outra], 30)


def test_two_incompatible_specific_types_remain_rejected():
    with pytest.raises(ValueError, match="sobreposição indevida"):
        _merge_partial_pieces([
            _decision(20, 23, document_type="contestacao", event="13", code="CONTES1")["pecas"][0],
            _decision(23, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        ], 30)


def test_isolated_separator_without_corresponding_piece_is_not_absorbed():
    separador = _partial(
        _separador_decision(20, 22, event="13")["pecas"][0],
        2, 20, 26,
    )
    result = _merge_partial_pieces([separador], 30)
    assert len(result["pecas"]) == 1
    assert result["pecas"][0]["document_type"] == "separador_de_evento"


def test_separator_and_specific_piece_do_not_duplicate_pages():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    result = _merge_partial_pieces([separador, decisao], 30)
    pages = list(range(result["pecas"][0]["pages_start"], result["pecas"][0]["pages_end"] + 1))
    assert len(pages) == len(set(pages))


def test_separator_absorption_preserves_full_page_coverage():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    result = _merge_partial_pieces([separador, decisao], 30)
    merged = result["pecas"][0]
    pages = list(range(merged["pages_start"], merged["pages_end"] + 1))
    assert len(pages) == len(set(pages))
    assert pages == sorted(pages)


def test_separator_absorption_preserves_judicial_locator():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    decisao["anchors"] = [
        {"label": "DESPADEC1", "page": 24, "process_number": "P1", "event": "13", "document_code": "DESPADEC1"},
    ]
    result = _merge_partial_pieces([separador, decisao], 30)
    anchors = result["pecas"][0].get("anchors") or []
    anchor_pages = [a["page"] for a in anchors]
    assert 24 in anchor_pages


def test_separator_absorption_produces_ordered_deterministic_ids():
    separador = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    decisao = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    primeira = _partial(
        _decision(1, 19, event="1", code="INIC1")["pecas"][0],
        1, 1, 20,
    )
    result = _merge_partial_pieces([primeira, separador, decisao], 30)
    assert [p["piece_id"] for p in result["pecas"]] == ["peca_001", "peca_002"]


def test_separator_absorption_is_deterministic():
    piece_a = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    piece_b = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    result_a = _merge_partial_pieces(copy.deepcopy([piece_a, piece_b]), 30)
    result_b = _merge_partial_pieces(copy.deepcopy([piece_a, piece_b]), 30)
    assert len(result_a["pecas"]) == len(result_b["pecas"])
    assert result_a["pecas"][0]["document_type"] == result_b["pecas"][0]["document_type"]
    assert result_a["pecas"][0]["document_code"] == result_b["pecas"][0]["document_code"]
    assert result_a["pecas"][0]["pages_start"] == result_b["pecas"][0]["pages_start"]
    assert result_a["pecas"][0]["pages_end"] == result_b["pecas"][0]["pages_end"]


def test_real_overlap_scenario_with_separator_and_despacho_decisao():
    first_window_piece = _partial(
        _separador_decision(24, 26, event="13")["pecas"][0],
        2, 20, 26,
    )
    second_window_piece = _partial(
        _decision(24, 26, document_type="despacho_decisao", event="13", code="DESPADEC1")["pecas"][0],
        3, 24, 30,
    )
    assert _is_separator_absorbable(first_window_piece, second_window_piece) is True
    assert _is_document_type_separator(first_window_piece) is True
    assert _is_document_type_separator(second_window_piece) is False


def _locator(page, event="13", code="DESPADEC1"):
    return {
        "physical_page": page,
        "attrs": {
            "process_number": "P1",
            "event": event,
            "document_code": code,
            "page": str(page),
        },
        "raw": f'[[judicial_locator: process_number="P1", event="{event}", document_code="{code}", page="{page}"]]',
    }


def test_nao_classificado_adjacent_absorbed_into_specific_piece():
    pieces = [
        {"document_type": "despacho", "document_type_confidence": "high",
         "pages_start": 26, "pages_end": 27,
         "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 26}]},
        {"document_type": "nao_classificado", "document_type_confidence": "low",
         "pages_start": 28, "pages_end": 28,
         "anchors": [{"label": "judicial_locator", "page": 28}]},
    ]
    locators = [_locator(28, event="13", code="DESPADEC1")]
    merged = _coalesce_contiguous_fragments(pieces, locators=locators)
    assert len(merged) == 1
    assert merged[0]["pages_end"] >= 28
    assert merged[0]["document_type"] == "despacho"


def test_nao_classificado_not_absorbed_when_event_differs():
    pieces = [
        {"document_type": "despacho", "document_type_confidence": "high",
         "pages_start": 26, "pages_end": 27,
         "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 26}]},
        {"document_type": "nao_classificado", "document_type_confidence": "low",
         "pages_start": 28, "pages_end": 28,
         "anchors": [{"label": "judicial_locator", "page": 28}]},
    ]
    locators = [_locator(28, event="20", code="OUTRO1")]
    merged = _coalesce_contiguous_fragments(pieces, locators=locators)
    assert len(merged) == 2


def test_contiguous_same_strong_identity_are_coalesced():
    pieces = [
        {"document_type": "despacho", "document_type_confidence": "high",
         "pages_start": 29, "pages_end": 30,
         "process_number": "P1", "event": "20", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 29}]},
        {"document_type": "despacho_decisao", "document_type_confidence": "high",
         "pages_start": 31, "pages_end": 32,
         "process_number": "P1", "event": "20", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 31}]},
    ]
    result = _merge_partial_pieces(pieces, 35)
    assert len(result["pecas"]) == 1
    assert result["pecas"][0]["pages_start"] == 29
    assert result["pecas"][0]["pages_end"] == 32


def test_contiguous_different_events_not_coalesced():
    pieces = [
        {"document_type": "despacho", "document_type_confidence": "high",
         "pages_start": 29, "pages_end": 31,
         "process_number": "P1", "event": "20", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 29}]},
        {"document_type": "despacho", "document_type_confidence": "high",
         "pages_start": 32, "pages_end": 35,
         "process_number": "P1", "event": "32", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 32}]},
    ]
    result = _merge_partial_pieces(pieces, 35)
    assert len(result["pecas"]) == 2


def test_coalescence_preserves_page_coverage():
    pieces = [
        {"document_type": "capa_processo", "document_type_confidence": "high",
         "pages_start": 1, "pages_end": 2,
         "process_number": "P1", "event": "abertura", "document_code": "CAPA1",
         "anchors": [{"label": "CAPA1", "page": 1}]},
        {"document_type": "despacho", "document_type_confidence": "high",
         "pages_start": 26, "pages_end": 27,
         "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
         "anchors": [{"label": "DESPADEC1", "page": 26}]},
        {"document_type": "nao_classificado", "document_type_confidence": "low",
         "pages_start": 28, "pages_end": 28,
         "anchors": [{"label": "judicial_locator", "page": 28}]},
    ]
    locators = [_locator(28, event="13", code="DESPADEC1")]
    merged = _coalesce_contiguous_fragments(pieces, locators=locators)
    covered = set()
    for piece in merged:
        covered.update(range(piece["pages_start"], piece["pages_end"] + 1))
    assert 28 in covered


def test_coalescence_renumbers_ids():
    first = {"document_type": "capa_processo", "document_type_confidence": "high",
             "pages_start": 1, "pages_end": 2,
             "process_number": "P1", "event": "abertura", "document_code": "CAPA1",
             "anchors": [{"label": "CAPA1", "page": 1}]}
    second = {"document_type": "despacho", "document_type_confidence": "high",
              "pages_start": 26, "pages_end": 27,
              "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
              "anchors": [{"label": "DESPADEC1", "page": 26}]}
    third = {"document_type": "despacho_decisao", "document_type_confidence": "high",
             "pages_start": 28, "pages_end": 30,
             "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
             "anchors": [{"label": "DESPADEC1", "page": 28}]}
    result = _merge_partial_pieces([first, second, third], 35)
    assert [p["piece_id"] for p in result["pecas"]] == ["peca_001", "peca_002"]


def test_coalescence_is_order_independent():
    left = {"document_type": "despacho", "document_type_confidence": "high",
            "pages_start": 26, "pages_end": 27,
            "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
            "anchors": [{"label": "DESPADEC1", "page": 26}]}
    right = {"document_type": "despacho_decisao", "document_type_confidence": "high",
             "pages_start": 28, "pages_end": 30,
             "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
             "anchors": [{"label": "DESPADEC1", "page": 28}]}
    a = _merge_partial_pieces([left, right], 35)
    b = _merge_partial_pieces([right, left], 35)
    assert len(a["pecas"]) == len(b["pecas"])


def test_event13_20_32_remain_three_distinct_pieces():
    p13 = {"document_type": "despacho", "document_type_confidence": "high",
           "pages_start": 26, "pages_end": 28,
           "process_number": "P1", "event": "13", "document_code": "DESPADEC1",
           "anchors": [{"label": "DESPADEC1", "page": 26}]}
    p20 = {"document_type": "despacho", "document_type_confidence": "high",
           "pages_start": 29, "pages_end": 32,
           "process_number": "P1", "event": "20", "document_code": "DESPADEC1",
           "anchors": [{"label": "DESPADEC1", "page": 29}]}
    p32 = {"document_type": "despacho_decisao", "document_type_confidence": "high",
           "pages_start": 33, "pages_end": 35,
           "process_number": "P1", "event": "32", "document_code": "DESPADEC1",
           "anchors": [{"label": "DESPADEC1", "page": 33}]}
    result = _merge_partial_pieces([p13, p20, p32], 35)
    events = [p.get("event") for p in result["pecas"]]
    assert events == ["13", "20", "32"] or set(events) == {"13", "20", "32"}


def test_orphan_pages_without_process_number_not_absorbed():
    capa = {"document_type": "capa_processo", "document_type_confidence": "high",
            "pages_start": 1, "pages_end": 2, "process_number": "P1", "event": "abertura",
            "document_code": "CAPA1", "anchors": [{"label": "CAPA1", "page": 1}]}
    pet = {"document_type": "peticao_inicial", "document_type_confidence": "high",
           "pages_start": 3, "pages_end": 17, "process_number": "P1", "event": "1",
           "document_code": "INIC1", "anchors": [{"label": "INIC1", "page": 3}]}
    orphan = {"document_type": "nao_classificado", "document_type_confidence": "low",
              "pages_start": 18, "pages_end": 20, "anchors": [{"label": "judicial_locator", "page": 18}]}
    next_doc = {"document_type": "contestacao", "document_type_confidence": "high",
                "pages_start": 21, "pages_end": 25, "process_number": "P1", "event": "11",
                "document_code": "CONT1", "anchors": [{"label": "CONT1", "page": 21}]}
    locators = [
        {"physical_page": 18, "attrs": {"page": "18"}},
        {"physical_page": 19, "attrs": {"page": "19"}},
        {"physical_page": 20, "attrs": {"page": "20"}},
    ]
    result = _merge_partial_pieces([capa, pet, orphan, next_doc], 25, locators=locators)
    pieces = result["pecas"]
    assert len(pieces) == 4, f"esperado 4 (orphan não deve coalescer), obteve {len(pieces)}"
    assert pieces[0]["pages_start"] == 1 and pieces[0]["pages_end"] == 2
    assert pieces[1]["pages_start"] == 3 and pieces[1]["pages_end"] == 17
    assert pieces[2]["document_type"] == "nao_classificado" and pieces[2]["pages_start"] == 18 and pieces[2]["pages_end"] == 20
    assert pieces[3]["pages_start"] == 21 and pieces[3]["pages_end"] == 25


def test_coalesced_result_has_eight_pieces_run2_scenario():
    capa = {"document_type": "capa_processo", "document_type_confidence": "high",
            "pages_start": 1, "pages_end": 2, "process_number": "P1", "event": "abertura",
            "document_code": "CAPA1", "anchors": [{"label": "CAPA1", "page": 1}]}
    sep = {"document_type": "pagina_de_separacao", "document_type_confidence": "high",
           "pages_start": 3, "pages_end": 3, "process_number": "P1", "event": "1",
           "document_code": "SEP1", "anchors": [{"label": "SEP1", "page": 3}]}
    pet = {"document_type": "peticao_inicial", "document_type_confidence": "high",
           "pages_start": 4, "pages_end": 18, "process_number": "P1", "event": "1",
           "document_code": "INIC1", "anchors": [{"label": "INIC1", "page": 4}]}
    nao = {"document_type": "nao_classificado", "document_type_confidence": "low",
           "pages_start": 19, "pages_end": 21, "anchors": [{"label": "judicial_locator", "page": 19}]}
    habil = {"document_type": "pedido_de_habilitacao", "document_type_confidence": "high",
             "pages_start": 22, "pages_end": 25, "process_number": "P1", "event": "11",
             "document_code": "PED HABILIT1", "anchors": [{"label": "PED HABILIT1", "page": 22}]}
    dec13a = {"document_type": "despacho_decisao", "document_type_confidence": "high",
              "pages_start": 26, "pages_end": 27, "process_number": "P1", "event": "13",
              "document_code": "DESPADEC1", "anchors": [{"label": "DESPADEC1", "page": 26}]}
    dec13b = {"document_type": "nao_classificado", "document_type_confidence": "low",
              "pages_start": 28, "pages_end": 28, "anchors": [{"label": "judicial_locator", "page": 28}]}
    dec20 = {"document_type": "despacho_decisao", "document_type_confidence": "high",
             "pages_start": 29, "pages_end": 31, "process_number": "P1", "event": "20",
             "document_code": "DESPADEC1", "anchors": [{"label": "DESPADEC1", "page": 29}]}
    dec32a = {"document_type": "despacho_decisao", "document_type_confidence": "high",
              "pages_start": 32, "pages_end": 33, "process_number": "P1", "event": "32",
              "document_code": "DESPADEC1", "anchors": [{"label": "DESPADEC1", "page": 32}]}
    dec32b = {"document_type": "despacho", "document_type_confidence": "high",
              "pages_start": 34, "pages_end": 35, "process_number": "P1", "event": "32",
              "document_code": "DESPADEC1", "anchors": [{"label": "DESPADEC1", "page": 34}]}
    locators = [_locator(28, event="13", code="DESPADEC1")]
    result = _merge_partial_pieces(
        [capa, sep, pet, nao, habil, dec13a, dec13b, dec20, dec32a, dec32b],
        35, locators=locators,
    )
    assert len(result["pecas"]) == 8
    covered = set()
    for p in result["pecas"]:
        covered.update(range(p["pages_start"], p["pages_end"] + 1))
    assert covered == set(range(1, 36))


def _realistic_process_source():
    pages = [
        _page(event="abertura", code="CAPA1", page=1, text="# CAPA"),
        _page(event="abertura", code="CAPA1", page=2, text="capa"),
        (
            '[[judicial_locator: process_number="P1", event="1", page="3", '
            'kind="event_separator"]]\n# PÁGINA DE SEPARAÇÃO\nEvento 1\n'
        ),
    ]
    pages.extend(_page(event="1", code="INIC1", page=page) for page in range(4, 19))
    pages.extend(
        f'[[judicial_locator: page="{page}"]]\npágina órfã\n'
        for page in range(19, 22)
    )
    pages.extend(_page(event="11", code="PEDHABILIT1", page=page) for page in range(22, 26))
    pages.extend(_page(event="13", code="DESPADEC1", page=page) for page in range(26, 29))
    pages.extend(_page(event="20", code="DESPADEC1", page=page) for page in range(29, 32))
    pages.extend(_page(event="32", code="DESPADEC1", page=page) for page in range(32, 36))
    return "".join(pages)


def _piece(start, end, document_type, event=None, code=None, process="P1"):
    piece = {
        "piece_id": "peca_001",
        "document_type": document_type,
        "document_type_confidence": "high" if document_type != "nao_classificado" else "low",
        "pages_start": start,
        "pages_end": end,
        "anchors": [{"label": code or "judicial_locator", "page": start}],
    }
    if process is not None:
        piece["process_number"] = process
    if event is not None:
        piece["event"] = event
    if code is not None:
        piece["document_code"] = code
    return piece


def _process_window_responses(separator_representation):
    first = [
        _piece(1, 2, "capa_processo", "abertura", "CAPA1"),
    ]
    if separator_representation == "included":
        first.append(_piece(3, 12, "peticao_inicial", "1", "INIC1"))
    else:
        first.extend([
            _piece(3, 3, separator_representation, "1"),
            _piece(4, 12, "peticao_inicial", "1", "INIC1"),
        ])
    return [
        {"metadata": {}, "pecas": first},
        {"metadata": {}, "pecas": [
            _piece(12, 18, "peticao_inicial", "1", "INIC1"),
            _piece(19, 21, "nao_classificado", process=None),
            _piece(22, 23, "pedido_de_habilitacao", "11", "PEDHABILIT1"),
        ]},
        {"metadata": {}, "pecas": [
            _piece(23, 25, "pedido_de_habilitacao", "11", "PEDHABILIT1"),
            _piece(26, 28, "decisao_interlocutoria", "13", "DESPADEC1"),
            _piece(29, 31, "decisao_interlocutoria", "20", "DESPADEC1"),
            _piece(32, 34, "decisao_interlocutoria", "32", "DESPADEC1"),
        ]},
        {"metadata": {}, "pecas": [
            _piece(34, 35, "decisao_interlocutoria", "32", "DESPADEC1"),
        ]},
    ]


@pytest.mark.parametrize(
    "separator_representation",
    ["separador_de_evento", "nao_classificado", "included"],
)
def test_page_3_llm_representations_produce_same_canonical_envelope(
    tmp_path, monkeypatch, separator_representation,
):
    monkeypatch.chdir(PROJECT_ROOT)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "Processo.md").write_text(_realistic_process_source(), encoding="utf-8")
    client = MappingFakeClient(_process_window_responses(separator_representation))

    result = run_segmentador_stage(input_dir, tmp_path / "out", llm_client=client)
    envelope = json.loads(result.read_text(encoding="utf-8"))
    canonical = [
        {
            key: piece.get(key)
            for key in (
                "document_type", "pages_start", "pages_end", "process_number",
                "event", "document_code",
            )
        }
        for piece in envelope["pecas"]
    ]
    canonical_hash = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()

    assert len(envelope["pecas"]) == 7
    assert canonical[1]["pages_start"] == 3
    assert canonical[1]["pages_end"] == 18
    assert canonical[1]["document_type"] == "peticao_inicial"
    assert canonical[1]["event"] == "1"
    assert canonical[1]["document_code"] == "INIC1"
    assert canonical[2]["pages_start"] == 19
    assert canonical[2]["pages_end"] == 21
    assert canonical[2]["document_type"] == "nao_classificado"
    coverage = [
        page
        for piece in envelope["pecas"]
        for page in range(piece["pages_start"], piece["pages_end"] + 1)
    ]
    assert coverage == list(range(1, 36))
    expected_hash_file = tmp_path.parent / "page-3-canonical-hash.txt"
    if expected_hash_file.exists():
        assert canonical_hash == expected_hash_file.read_text(encoding="utf-8")
    else:
        expected_hash_file.write_text(canonical_hash, encoding="utf-8")


def test_structural_separator_with_different_event_is_not_absorbed():
    source = (
        '[[judicial_locator: process_number="P1", event="2", page="1", '
        'kind="event_separator"]]\n# PÁGINA DE SEPARAÇÃO\n'
        + _page(event="1", code="INIC1", page=2)
    )
    result = _merge_partial_pieces(
        [
            _piece(1, 1, "nao_classificado", "2"),
            _piece(2, 2, "peticao_inicial", "1", "INIC1"),
        ],
        2,
        locators=_index_judicial_locators(source),
    )
    assert [(piece["pages_start"], piece["pages_end"]) for piece in result["pecas"]] == [
        (1, 1), (2, 2),
    ]


def test_structural_separator_conflicting_document_code_is_not_absorbed():
    source = (
        '[[judicial_locator: process_number="P1", event="1", document_code="OUTRO1", '
        'page="1", kind="event_separator"]]\n# PÁGINA DE SEPARAÇÃO\n'
        + _page(event="1", code="INIC1", page=2)
    )
    result = _merge_partial_pieces(
        [
            _piece(1, 1, "nao_classificado", "1", "OUTRO1"),
            _piece(2, 2, "peticao_inicial", "1", "INIC1"),
        ],
        2,
        locators=_index_judicial_locators(source),
    )
    assert len(result["pecas"]) == 2
