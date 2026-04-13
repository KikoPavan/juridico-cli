#!/usr/bin/env python3
"""
validate_yaml_normalizador_juridico.py
=======================================
Valida artefatos .md gerados pela skill yaml-normalizador-juridico
contra o contrato definido em assets/io.schema.json e assets/output_contract.md.

Uso:
    python validate_yaml_normalizador_juridico.py \
        --input-dir <diretorio_com_mds> \
        [--schema <caminho_io.schema.json>] \
        [--routing-map <caminho_routing_map.yaml>] \
        [--report <caminho_relatorio.json>] \
        [--strict]

Saída:
    - Relatório de validação em JSON (stdout ou arquivo)
    - Código de saída 0 (todos válidos) ou 1 (há inválidos) ou 2 (erro de configuração)
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import yaml

logger = logging.getLogger("validate-yaml-normalizador")

# Campos obrigatórios no frontmatter de saída
REQUIRED_FRONTMATTER_FIELDS = [
    "piece_id", "document_type", "skill_key", "source_file", "source_path",
    "source_sha256", "pages_start", "pages_end", "process_group_id",
    "origin_piece_index", "acao_curatorial", "priority", "impacto_processual",
    "impacto_sentenca_confirmado", "review_status", "language", "created_by_skill", "status",
    "normalized_at",
]

VALID_REVIEW_STATUS = {"approved", "pending_review", "unroutable"}
VALID_STATUS = {"ready", "needs_review", "skipped"}
VALID_CURATION_ACTION = {"manter", "resumir", "revisar"}
VALID_IMPACTO_PROCESSUAL = {"nuclear", "relevante", "acessorio", "irrelevante"}
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def parse_md_frontmatter(content: str) -> tuple[dict | None, str]:
    """
    Extrai frontmatter YAML de um arquivo Markdown.
    Retorna (dict_frontmatter | None, body_text).
    """
    if not content.startswith("---"):
        return None, content

    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, content

    yaml_block = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:]).strip()

    try:
        fm = yaml.safe_load(yaml_block)
        return fm if isinstance(fm, dict) else None, body
    except yaml.YAMLError as e:
        logger.warning("YAML inválido no frontmatter: %s", e)
        return None, body


def load_routing_map(path: Path) -> set:
    """Retorna conjunto de skill_keys válidos definidos no routing_map."""
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    keys = set()
    for entry in raw.get("routing", {}).values():
        keys.add(entry.get("skill_key", ""))
    fallback = raw.get("fallback", {}).get("skill_key")
    if fallback:
        keys.add(fallback)
    return keys


def validate_frontmatter(fm: dict, valid_skill_keys: set, strict: bool) -> list[str]:
    """
    Valida o frontmatter de uma peça.
    Retorna lista de erros encontrados (vazia = válido).
    """
    errors = []

    # 1. Campos obrigatórios presentes
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in fm:
            errors.append(f"Campo obrigatório ausente: '{field}'")
        elif fm[field] is None:
            errors.append(f"Campo obrigatório nulo: '{field}'")

    if errors and not strict:
        return errors  # Interrompe cedo se campos faltam

    # 2. created_by_skill deve ser constante
    if fm.get("created_by_skill") != "yaml-normalizador-juridico":
        errors.append(
            f"created_by_skill inválido: '{fm.get('created_by_skill')}' "
            f"(esperado: 'yaml-normalizador-juridico')"
        )

    # 3. review_status válido
    rs = fm.get("review_status")
    if rs and rs not in VALID_REVIEW_STATUS:
        errors.append(f"review_status inválido: '{rs}' (válidos: {VALID_REVIEW_STATUS})")

    # 4. status válido
    st = fm.get("status")
    if st and st not in VALID_STATUS:
        errors.append(f"status inválido: '{st}' (válidos: {VALID_STATUS})")

    # 5. acao_curatorial válida
    ca = fm.get("acao_curatorial")
    if ca and ca not in VALID_CURATION_ACTION:
        errors.append(f"acao_curatorial inválida: '{ca}' (válidos: {VALID_CURATION_ACTION})")

    # 5b. impacto_processual válido
    ip = fm.get("impacto_processual")
    if ip and ip not in VALID_IMPACTO_PROCESSUAL:
        errors.append(f"impacto_processual inválido: '{ip}' (válidos: {VALID_IMPACTO_PROCESSUAL})")

    # 5c. priority deve ser integer 1-5
    pri = fm.get("priority")
    if pri is not None and (not isinstance(pri, int) or pri < 1 or pri > 5):
        errors.append(f"priority deve ser integer 1–5, got: {pri}")

    # 6. source_sha256 formato
    sha = fm.get("source_sha256")
    if sha and not SHA256_RE.match(str(sha)):
        errors.append(f"source_sha256 com formato inválido: '{sha}'")

    # 7. pages_start e pages_end
    ps = fm.get("pages_start")
    pe = fm.get("pages_end")
    if ps is not None and not isinstance(ps, int):
        errors.append(f"pages_start deve ser integer, got: {type(ps).__name__}")
    if pe is not None and not isinstance(pe, int):
        errors.append(f"pages_end deve ser integer, got: {type(pe).__name__}")
    if isinstance(ps, int) and isinstance(pe, int) and pe < ps:
        errors.append(f"pages_end ({pe}) < pages_start ({ps})")

    # 8. document_date formato (se presente)
    dd = fm.get("document_date")
    if dd is not None and not isinstance(dd, type(None)):
        if not DATE_RE.match(str(dd)):
            errors.append(f"document_date com formato inválido: '{dd}' (esperado YYYY-MM-DD)")

    # 9. normalized_at formato
    nat = fm.get("normalized_at")
    if nat and not DATETIME_RE.match(str(nat)):
        errors.append(f"normalized_at com formato inválido: '{nat}'")

    # 10. skill_key registrado no routing_map
    sk = fm.get("skill_key")
    if sk and valid_skill_keys and sk not in valid_skill_keys:
        errors.append(
            f"skill_key '{sk}' não encontrado no routing_map.yaml "
            f"(pode indicar routing_map desatualizado)"
        )

    # 11. impacto_sentenca_confirmado deve ser boolean
    isen = fm.get("impacto_sentenca_confirmado")
    if isen is not None and not isinstance(isen, bool):
        errors.append(f"impacto_sentenca_confirmado deve ser boolean, got: {type(isen).__name__}")

    # 12. audit_trail deve ser lista com ao menos 1 entrada desta skill
    at = fm.get("audit_trail")
    if at is None:
        errors.append("audit_trail ausente no frontmatter")
    elif not isinstance(at, list):
        errors.append(f"audit_trail deve ser lista, got: {type(at).__name__}")
    else:
        has_skill_entry = any(
            isinstance(e, dict) and e.get("stage") == "yaml-normalizador-juridico"
            for e in at
        )
        if not has_skill_entry:
            errors.append("audit_trail não contém entrada de 'yaml-normalizador-juridico'")

    # 13. parties_normalized deve ser lista (mesmo que vazia)
    pn = fm.get("parties_normalized")
    if pn is not None and not isinstance(pn, list):
        errors.append(f"parties_normalized deve ser lista, got: {type(pn).__name__}")

    return errors


def validate_file(
    md_path: Path,
    valid_skill_keys: set,
    strict: bool,
) -> dict:
    """Valida um único arquivo .md. Retorna dict com resultado."""
    result = {
        "file": str(md_path),
        "valid": False,
        "errors": [],
        "warnings": [],
        "piece_id": None,
        "skill_key": None,
        "review_status": None,
    }

    content = md_path.read_text(encoding="utf-8")
    fm, body = parse_md_frontmatter(content)

    if fm is None:
        result["errors"].append("Frontmatter YAML não encontrado ou inválido")
        return result

    result["piece_id"] = fm.get("piece_id")
    result["skill_key"] = fm.get("skill_key")
    result["review_status"] = fm.get("review_status")

    # Validar corpo textual não vazio
    if not body.strip():
        result["warnings"].append("Corpo textual da peça está vazio")

    errors = validate_frontmatter(fm, valid_skill_keys, strict)
    result["errors"] = errors
    result["valid"] = len(errors) == 0

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validador de artefatos yaml-normalizador-juridico"
    )
    parser.add_argument("--input-dir", required=True, help="Diretório com arquivos .md")
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).parent.parent / "assets" / "io.schema.json"),
        help="Caminho do io.schema.json (informativo)"
    )
    parser.add_argument(
        "--routing-map",
        default=str(Path(__file__).parent.parent / "assets" / "routing_map.yaml"),
        help="Caminho do routing_map.yaml"
    )
    parser.add_argument("--report", help="Salvar relatório JSON neste arquivo")
    parser.add_argument(
        "--strict", action="store_true",
        help="Modo estrito: reportar todos os erros mesmo após campos obrigatórios ausentes"
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr
    )

    input_dir = Path(args.input_dir)
    routing_map_path = Path(args.routing_map)

    if not input_dir.exists() or not input_dir.is_dir():
        logger.error("Diretório de input não encontrado: %s", input_dir)
        sys.exit(2)

    # Carregar skill_keys válidos
    valid_skill_keys = set()
    if routing_map_path.exists():
        try:
            valid_skill_keys = load_routing_map(routing_map_path)
            logger.info("Routing map carregado: %d skill_keys válidos", len(valid_skill_keys))
        except Exception as e:
            logger.warning("Não foi possível carregar routing_map: %s", e)
    else:
        logger.warning("routing_map.yaml não encontrado — validação de skill_key desativada")

    # Coletar arquivos
    md_files = sorted(input_dir.glob("*.md"))
    if not md_files:
        logger.warning("Nenhum arquivo .md encontrado em: %s", input_dir)
        report = {"total": 0, "valid": 0, "invalid": 0, "results": []}
        _output_report(report, args.report)
        sys.exit(0)

    logger.info("Validando %d arquivos...", len(md_files))

    results = []
    for md_path in md_files:
        res = validate_file(md_path, valid_skill_keys, args.strict)
        results.append(res)
        status = "✅ VÁLIDO" if res["valid"] else f"❌ INVÁLIDO ({len(res['errors'])} erros)"
        logger.info("[%s] %s → %s", res.get("piece_id", md_path.name), md_path.name, status)
        for err in res["errors"]:
            logger.warning("  ⚠ %s", err)
        for warn in res["warnings"]:
            logger.debug("  ℹ %s", warn)

    total = len(results)
    valid_count = sum(1 for r in results if r["valid"])
    invalid_count = total - valid_count

    report = {
        "total": total,
        "valid": valid_count,
        "invalid": invalid_count,
        "results": results,
    }

    _output_report(report, args.report)

    logger.info(
        "Resultado final: %d/%d válidos | %d inválidos",
        valid_count, total, invalid_count
    )

    sys.exit(0 if invalid_count == 0 else 1)


def _output_report(report: dict, report_path: str | None):
    json_str = json.dumps(report, ensure_ascii=False, indent=2)
    if report_path:
        Path(report_path).write_text(json_str, encoding="utf-8")
        logger.info("Relatório salvo em: %s", report_path)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
