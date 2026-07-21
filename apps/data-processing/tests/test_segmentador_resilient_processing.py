"""Regressões do processamento resiliente específico do segmentador."""

import copy
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "apps" / "data-processing" / "src"
sys.path.insert(0, str(SRC_DIR))

from data_processing.orchestrator.stage_router import (  # noqa: E402
    _build_segmentation_windows,
    _index_judicial_locators,
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
