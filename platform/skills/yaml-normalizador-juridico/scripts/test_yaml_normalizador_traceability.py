"""Testes unitários de rastreabilidade do yaml-normalizador-juridico."""

from pathlib import Path

import yaml

from apply_yaml_normalization import canonicalize_piece, process_piece


LOCATOR = (
    '[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", '
    'event="1", document_code="INIC1", page="1"]]'
)


def _piece():
    return {
        "piece_id": "peca_001",
        "document_type": "peticao_inicial",
        "acao_curatorial": "manter",
        "modo_aplicado": "padrao",
        "justificativa_curta": "Peça central protegida",
        "impacto_processual": "irrelevante",
        "impacto_sentenca_confirmado": False,
        "prioridade": 2,
        "compressao_sugerida": None,
        "encaminhamento": "extr-peticao-processo",
        "audit_trail": [{
            "stage": "curador-relevancia",
            "timestamp": "2026-07-19T12:00:00Z",
            "action": "decisao_curatorial_aplicada",
        }],
        "text": f"{LOCATOR}\n\n# PETIÇÃO INICIAL\n\nDos pedidos.",
        "anchors": [],
        "pages_start": None,
        "pages_end": None,
        "page_number_start": 1,
        "page_number_end": 15,
        "source_file": "Petição Inicial_evento_1.md",
        "source_path": "/fixture/Petição Inicial_evento_1.md",
        "source_sha256": "a" * 64,
        "process_group_id": "processo-fixture",
        "origin_piece_index": 0,
    }


def _frontmatter_and_body(path: Path):
    content = path.read_text(encoding="utf-8")
    _, yaml_block, body = content.split("---", 2)
    return yaml.safe_load(yaml_block), body


def test_canonicalize_aliases_locator_identity_and_protected_impact():
    piece = _piece()
    canonicalize_piece(piece)

    assert (piece["pages_start"], piece["pages_end"]) == (1, 15)
    assert piece["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert piece["event"] == "1"
    assert piece["document_code"] == "INIC1"
    assert piece["impacto_processual"] == "relevante"
    assert piece["anchors"][0]["process_number"] == piece["process_number"]


def test_explicit_traceability_takes_precedence_over_locator():
    piece = _piece()
    piece.update({
        "pages_start": 2,
        "pages_end": 4,
        "process_number": "processo-explicito",
        "event": "9",
        "document_code": "EXP1",
        "impacto_processual": "nuclear",
    })
    canonicalize_piece(piece)

    assert (piece["pages_start"], piece["pages_end"]) == (2, 4)
    assert piece["process_number"] == "processo-explicito"
    assert piece["event"] == "9"
    assert piece["document_code"] == "EXP1"
    assert piece["impacto_processual"] == "nuclear"


def test_process_piece_renders_traceability_and_preserves_locator(tmp_path):
    piece = _piece()
    assert process_piece(
        piece,
        {"peticao_inicial": "EXTR_PETICAO_PROCESSO", "__fallback__": "REVISAR_MANUAL"},
        tmp_path,
        "2026-07-19T12:00:00-03:00",
    )

    fm, body = _frontmatter_and_body(tmp_path / "processo-fixture__peca_001.md")
    assert fm["pages_start"] == 1
    assert fm["pages_end"] == 15
    assert fm["process_number"] == "4000153-37.2026.8.26.0136/SP"
    assert str(fm["event"]) == "1"
    assert fm["document_code"] == "INIC1"
    assert fm["impacto_processual"] == "relevante"
    assert LOCATOR in body
