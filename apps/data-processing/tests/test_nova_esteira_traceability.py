"""Regressão determinística de rastreabilidade da nova esteira jurídica."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "apps" / "data-processing" / "src"
CURADOR_SCRIPTS = PROJECT_ROOT / "platform" / "skills" / "curador-relevancia" / "scripts"
NORMALIZADOR_SCRIPT = (
    PROJECT_ROOT
    / "platform"
    / "skills"
    / "yaml-normalizador-juridico"
    / "scripts"
    / "apply_yaml_normalization.py"
)
FIXTURE = Path(__file__).parent / "fixtures" / "peticao_inicial_evento_1_minima.md"
LOCATOR_PAGE_1 = (
    '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", '
    'event="1", document_code="INIC1", page="1"]]'
)

sys.path.insert(0, str(SRC_DIR))
from data_processing.orchestrator.stage_router import (  # noqa: E402
    _SEGMENTATION_DECISION_SCHEMA,
    _canonicalize_piece_traceability,
    _is_compact_segmentation,
    _single_piece_fallback,
    _slice_markdown_by_pages,
    run_segmentador_stage,
)

sys.path.insert(0, str(CURADOR_SCRIPTS))
from curar import CuradorRelevancia  # noqa: E402

_normalizer_spec = importlib.util.spec_from_file_location(
    "yaml_normalizador_apply", NORMALIZADOR_SCRIPT
)
normalizer = importlib.util.module_from_spec(_normalizer_spec)
assert _normalizer_spec.loader is not None
_normalizer_spec.loader.exec_module(normalizer)


def _base_piece(document_type="peticao_inicial", impacto=None):
    return {
        "piece_id": "peca_001",
        "document_type": document_type,
        "document_type_confidence": "high",
        "pages_start": None,
        "pages_end": None,
        "page_number_start": 1,
        "page_number_end": 15,
        "pages_total": 15,
        "title": "Petição Inicial",
        "summary": "Peça inaugural.",
        "impacto_sentenca_proposto": None,
        "text_excerpt": "PETIÇÃO INICIAL",
        "text": "# PETIÇÃO INICIAL\n\nParte autora formula seus pedidos.",
        "anchors": [],
        "observacoes": None,
        "source_file": "Petição Inicial_evento_1.md",
        "source_path": "/fixture/Petição Inicial_evento_1.md",
        "source_sha256": "a" * 64,
        "process_group_id": "processo-fixture",
        "origin_piece_index": 0,
        "relevancia_estimada": 0.1,
        "confianca_classificacao": 0.95,
        "impacto_processual": impacto,
        "impacto_sentenca_confirmado": False,
    }


def _metadata():
    return {
        "processo_id": "4000153-37.2026.8.26.0136/SP",
        "event_id": "1",
        "document_code": "INIC1",
    }


def _parse_output(path: Path):
    content = path.read_text(encoding="utf-8")
    _, yaml_block, body = content.split("---", 2)
    return yaml.safe_load(yaml_block), body


def test_segmentador_canonicalizes_aliases_reinjects_locators_and_enriches_anchor():
    piece = _base_piece()
    source_text = FIXTURE.read_text(encoding="utf-8")

    _canonicalize_piece_traceability(piece, _metadata(), source_text)

    assert piece["pages_start"] == 1
    assert piece["pages_end"] == 15
    assert LOCATOR_PAGE_1 in piece["text"]
    assert piece["process_number"] == _metadata()["processo_id"]
    assert piece["event"] == "1"
    assert piece["document_code"] == "INIC1"
    assert piece["anchors"] == [{
        "label": "peticao_inicial",
        "page": 1,
        "process_number": "4000153-37.2026.8.26.0136/SP",
        "event": "1",
        "document_code": "INIC1",
    }]


def test_compact_schema_excludes_full_text_and_rejects_extractor_shape():
    item_properties = _SEGMENTATION_DECISION_SCHEMA["properties"]["pecas"]["items"][
        "properties"
    ]
    assert "text" not in item_properties
    assert "text_content" not in item_properties
    assert not _is_compact_segmentation({
        "peticao_identification": {},
        "parties": [],
        "fundamentos_legais": [],
        "pedidos": [],
    })


def test_page_slice_and_single_piece_fallback_preserve_source_markdown():
    source_text = FIXTURE.read_text(encoding="utf-8")

    assert _slice_markdown_by_pages(source_text, 1, 15) == source_text.strip()
    fallback = _single_piece_fallback(source_text, "Petição Inicial_evento_1.md")

    assert fallback is not None
    piece = fallback["pecas"][0]
    assert piece["document_type"] == "peticao_inicial"
    assert (piece["pages_start"], piece["pages_end"]) == (1, 15)
    assert piece["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert piece["event"] == "1"
    assert piece["document_code"] == "INIC1"


def test_run_segmentador_stage_falls_back_and_writes_schema_valid_envelope(
    tmp_path, monkeypatch,
):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source_text = FIXTURE.read_text(encoding="utf-8")
    (input_dir / "Petição Inicial_evento_1.md").write_text(
        source_text, encoding="utf-8"
    )
    monkeypatch.setenv("LLM_PROVIDER", "dummy")
    monkeypatch.chdir(PROJECT_ROOT)

    envelope_path = run_segmentador_stage(input_dir, output_dir)
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (PROJECT_ROOT / "platform/skills/segmentador-juridico/assets/output-schema.json")
        .read_text(encoding="utf-8")
    )

    assert set(envelope) == {"metadata", "pecas"}
    piece = envelope["pecas"][0]
    assert piece["text"] == source_text.strip()
    assert LOCATOR_PAGE_1 in piece["text"]
    assert piece["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert piece["event"] == "1"
    assert piece["document_code"] == "INIC1"
    assert (piece["pages_start"], piece["pages_end"]) == (1, 15)
    assert {anchor["page"] for anchor in piece["anchors"]} == {1, 15}
    assert not list(Draft7Validator(schema).iter_errors(envelope))


def test_canonical_pages_and_existing_anchor_values_take_precedence():
    piece = _base_piece()
    piece.update({
        "pages_start": 2,
        "pages_end": 4,
        "process_number": "processo-explicito",
        "event": "9",
        "document_code": "EXP1",
        "anchors": [{"label": "existente", "page": 2, "event": "8"}],
    })

    _canonicalize_piece_traceability(piece, _metadata())

    assert (piece["pages_start"], piece["pages_end"]) == (2, 4)
    assert piece["anchors"][0] == {
        "label": "existente",
        "page": 2,
        "process_number": "processo-explicito",
        "event": "8",
        "document_code": "EXP1",
    }


@pytest.mark.parametrize(
    "document_type",
    ["peticao_inicial", "contestacao", "decisao", "sentenca", "recurso"],
)
def test_curador_never_defaults_protected_types_to_irrelevante(document_type):
    piece = _base_piece(document_type=document_type, impacto=None)
    result = CuradorRelevancia().processar({"metadata": _metadata(), "pecas": [piece]})

    assert result["pecas"][0]["impacto_processual"] == "relevante"


def test_curador_preserves_nuclear_and_keeps_non_protected_rules():
    nuclear = _base_piece(impacto="nuclear")
    non_protected = _base_piece(document_type="certidao", impacto="irrelevante")

    assert CuradorRelevancia()._enrich_peca(nuclear)["impacto_processual"] == "nuclear"
    assert CuradorRelevancia()._enrich_peca(non_protected)["impacto_processual"] == "irrelevante"


def test_pipeline_fixture_preserves_frontmatter_and_locator(tmp_path):
    piece = _base_piece()
    _canonicalize_piece_traceability(
        piece,
        envelope_metadata=_metadata(),
        source_text=FIXTURE.read_text(encoding="utf-8"),
    )
    curated = CuradorRelevancia().processar({"metadata": _metadata(), "pecas": [piece]})
    curated_piece = copy.deepcopy(curated["pecas"][0])

    ok = normalizer.process_piece(
        curated_piece,
        {"peticao_inicial": "EXTR_PETICAO_PROCESSO", "__fallback__": "REVISAR_MANUAL"},
        tmp_path,
        "2026-07-19T12:00:00-03:00",
    )

    assert ok
    output = tmp_path / "processo-fixture__peca_001.md"
    frontmatter, body = _parse_output(output)
    assert frontmatter["pages_start"] == 1
    assert frontmatter["pages_end"] == 15
    assert frontmatter["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert str(frontmatter["event"]) == "1"
    assert frontmatter["document_code"] == "INIC1"
    assert frontmatter["impacto_processual"] == "relevante"
    assert LOCATOR_PAGE_1 in body


def test_normalizer_uses_locator_as_identity_fallback(tmp_path):
    piece = _base_piece()
    piece["text"] = FIXTURE.read_text(encoding="utf-8")
    piece.update({
        "acao_curatorial": "manter",
        "modo_aplicado": "padrao",
        "justificativa_curta": "Peça protegida",
        "prioridade": 2,
        "compressao_sugerida": None,
        "encaminhamento": "extr-peticao-processo",
        "audit_trail": [{
            "stage": "curador-relevancia",
            "timestamp": "2026-07-19T12:00:00Z",
            "action": "decisao_curatorial_aplicada",
        }],
    })

    assert normalizer.process_piece(
        piece,
        {"peticao_inicial": "EXTR_PETICAO_PROCESSO", "__fallback__": "REVISAR_MANUAL"},
        tmp_path,
        "2026-07-19T12:00:00-03:00",
    )
    frontmatter, body = _parse_output(tmp_path / "processo-fixture__peca_001.md")
    assert frontmatter["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert str(frontmatter["event"]) == "1"
    assert frontmatter["document_code"] == "INIC1"
    assert LOCATOR_PAGE_1 in body
