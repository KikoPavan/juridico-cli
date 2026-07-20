#!/usr/bin/env python3
"""
validate_output.py — Validador de Saída do segmentador-jurídico
================================================================
Valida um JSON de saída do segmentador-jurídico (Envelope de Processo)
contra o schema formal (assets/output-schema.json).

Uso:
    python validate_output.py <output.json> [--schema <schema.json>] [--verbose]

Retorna:
    Exit code 0: válido
    Exit code 1: inválido (com erros impressos)
    Exit code 2: erro de leitura/parse
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_json(path: str, label: str) -> dict:
    """Carrega e faz parse de um arquivo JSON."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERRO] {label} não encontrado: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[ERRO] {label} inválido (JSON parse): {e}", file=sys.stderr)
        sys.exit(2)


def validate_with_jsonschema(data: dict, schema: dict) -> list[str]:
    """Valida data contra schema usando jsonschema."""
    try:
        import jsonschema
        errors = list(jsonschema.Draft7Validator(schema).iter_errors(data))
        return [
            f"{'.'.join(str(p) for p in e.absolute_path) or 'root'}: {e.message}"
            for e in errors
        ]
    except ImportError:
        return []


def validate_manual(data: dict) -> list[str]:
    """Validação manual sem dependência de jsonschema."""
    errors = []

    # Top-level: metadata e pecas
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        errors.append("metadata: campo obrigatório ausente ou não é objeto")
        return errors

    for field in ["processo_id", "total_pecas", "gerado_por", "timestamp",
                  "source_file", "total_pages", "schema_version"]:
        if field not in meta:
            errors.append(f"metadata.{field}: campo obrigatório ausente")

    if meta.get("gerado_por") != "segmentador-juridico":
        errors.append("metadata.gerado_por: deve ser 'segmentador-juridico'")

    if "total_pecas" in meta and not isinstance(meta["total_pecas"], int):
        errors.append("metadata.total_pecas: deve ser inteiro")

    pecas = data.get("pecas")
    if not isinstance(pecas, list) or len(pecas) == 0:
        errors.append("pecas: campo obrigatório ausente ou array vazio")
        return errors

    if "total_pecas" in meta and isinstance(meta["total_pecas"], int):
        if meta["total_pecas"] != len(pecas):
            errors.append(
                f"metadata.total_pecas ({meta['total_pecas']}) "
                f"≠ len(pecas) ({len(pecas)})"
            )

    valid_types = {
        "peticao_inicial", "contestacao", "replica", "decisao_interlocutoria",
        "sentenca", "acordao", "despacho", "procuracao", "mandato", "contrato",
        "escritura", "laudo_pericial", "parecer", "recurso", "agravo", "apelacao",
        "embargos_declaracao", "impugnacao", "memoriais", "certidao", "ata",
        "oficio", "intimacao", "citacao", "mandado", "termo", "anexo",
        "comprovante", "capa_processo", "nao_classificado"
    }
    valid_confidence = {"high", "medium", "low"}
    seen_ids = set()

    for i, peca in enumerate(pecas):
        prefix = f"pecas[{i}]"

        if not isinstance(peca, dict):
            errors.append(f"{prefix}: não é objeto")
            continue

        # piece_id
        pid = peca.get("piece_id")
        if not pid:
            errors.append(f"{prefix}.piece_id: obrigatório")
        elif pid in seen_ids:
            errors.append(f"{prefix}.piece_id: duplicado: '{pid}'")
        else:
            seen_ids.add(pid)
            if not re.match(r'^peca_\d{3}[a-z]?$', pid):
                errors.append(f"{prefix}.piece_id: formato inválido '{pid}'")

        # document_type
        dtype = peca.get("document_type")
        if dtype is None:
            errors.append(f"{prefix}.document_type: obrigatório")
        elif dtype not in valid_types:
            errors.append(f"{prefix}.document_type: tipo desconhecido '{dtype}'")

        # document_type_confidence
        conf = peca.get("document_type_confidence")
        if not conf:
            errors.append(f"{prefix}.document_type_confidence: obrigatório")
        elif conf not in valid_confidence:
            errors.append(f"{prefix}.document_type_confidence: valor inválido '{conf}'")

        # pages
        ps = peca.get("pages_start")
        pe = peca.get("pages_end")
        pt = peca.get("pages_total")
        if ps is not None and pe is not None:
            if not isinstance(ps, int) or not isinstance(pe, int):
                errors.append(f"{prefix}: pages_start/pages_end devem ser inteiros ou null")
            elif pe < ps:
                errors.append(f"{prefix}: pages_end ({pe}) < pages_start ({ps})")
        if pt is None:
            errors.append(f"{prefix}.pages_total: obrigatório")
        elif not isinstance(pt, int) or pt < 1:
            errors.append(f"{prefix}.pages_total: deve ser inteiro ≥ 1")

        # campos de texto obrigatórios
        for field in ["title", "summary", "text_excerpt", "text"]:
            val = peca.get(field)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(f"{prefix}.{field}: obrigatório e não vazio")

        # summary max length
        summary = peca.get("summary", "")
        if isinstance(summary, str) and len(summary) > 1000:
            errors.append(f"{prefix}.summary: excede 1000 chars ({len(summary)})")

        # anchors como array de objetos {label, page}
        anchors = peca.get("anchors")
        if not isinstance(anchors, list) or len(anchors) == 0:
            errors.append(f"{prefix}.anchors: obrigatório, array não vazio")
        else:
            for j, anchor in enumerate(anchors):
                if not isinstance(anchor, dict):
                    errors.append(f"{prefix}.anchors[{j}]: deve ser objeto {{label, page}}")
                    continue
                if not anchor.get("label") or not isinstance(anchor["label"], str):
                    errors.append(f"{prefix}.anchors[{j}].label: obrigatório, string")
                ap = anchor.get("page")
                if ap is None or not isinstance(ap, int) or ap < 1:
                    errors.append(f"{prefix}.anchors[{j}].page: obrigatório, integer ≥ 1")

        # campos de proveniência obrigatórios
        for field in ["source_file", "source_path", "source_sha256", "process_group_id",
                      "origin_piece_index"]:
            if field not in peca:
                errors.append(f"{prefix}.{field}: campo obrigatório ausente")

        sha = peca.get("source_sha256")
        if sha and not re.match(r'^[a-fA-F0-9]{64}$', str(sha)):
            errors.append(f"{prefix}.source_sha256: formato SHA-256 inválido")

        # relevancia_estimada obrigatório
        rel = peca.get("relevancia_estimada")
        if rel is None:
            errors.append(f"{prefix}.relevancia_estimada: obrigatório")
        elif not isinstance(rel, (int, float)) or rel < 0.0 or rel > 1.0:
            errors.append(f"{prefix}.relevancia_estimada: deve ser número 0.0–1.0")

        # observacoes opcional (pode ser null)
        if "observacoes" not in peca:
            errors.append(f"{prefix}.observacoes: campo deve existir (pode ser null)")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Valida saída do segmentador-jurídico (Envelope de Processo)"
    )
    parser.add_argument("output", help="Arquivo JSON de saída a validar")
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).parent.parent / "assets" / "output-schema.json"),
        help="Caminho para o schema JSON"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Saída detalhada")
    args = parser.parse_args()

    print(f"[segmentador-jurídico] Validando Envelope de Processo: {args.output}")

    data = load_json(args.output, "Output JSON")

    # Tentar validação com jsonschema
    schema_errors = []
    try:
        import jsonschema  # noqa: F401
        schema = load_json(args.schema, "Schema JSON")
        schema_errors = validate_with_jsonschema(data, schema)
        validation_method = "jsonschema"
    except ImportError:
        validation_method = "manual"

    manual_errors = validate_manual(data)

    all_errors = list(dict.fromkeys(schema_errors + manual_errors))

    if args.verbose:
        meta = data.get("metadata", {})
        pecas = data.get("pecas", [])
        print(f"  → processo_id    : {meta.get('processo_id', 'N/A')}")
        print(f"  → total_pecas    : {meta.get('total_pecas', 'N/A')}")
        print(f"  → schema_version : {meta.get('schema_version', 'N/A')}")
        print(f"  → pecas no array : {len(pecas)}")
        if pecas:
            print("\n  Peças identificadas:")
            for p in pecas:
                print(f"    [{p.get('piece_id','?')}] {p.get('document_type','?')} "
                      f"({p.get('document_type_confidence','?')}) "
                      f"p.{p.get('pages_start','?')}-{p.get('pages_end','?')} "
                      f"relevância={p.get('relevancia_estimada','?')} "
                      f"— {p.get('title','')[:60]}")

    if all_errors:
        print(f"\n[FALHA] {len(all_errors)} erro(s) encontrado(s):\n")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"\n[OK] JSON válido. {len(data.get('pecas', []))} peça(s) identificada(s). ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
