#!/usr/bin/env python3
"""
apply_yaml_normalization.py
============================
Script principal da skill yaml-normalizador-juridico.

Recebe um JSON (ou array de JSONs) do curador-relevancia e gera
um arquivo .md individual por peça elegível, com frontmatter YAML
padronizado e o corpo textual original preservado.

Uso:
    python apply_yaml_normalization.py \
        --input <caminho_json_ou_dir> \
        --output-dir <diretorio_saida> \
        [--routing-map <caminho_routing_map.yaml>] \
        [--log-level DEBUG|INFO|WARNING]

Saída:
    - Arquivos .md em <output-dir>
    - Log de execução em stderr
    - Código de saída 0 (sucesso) ou 1 (erros parciais) ou 2 (falha total)

Nota sobre renderização:
    O frontmatter YAML é gerado inteiramente via PyYAML (yaml.dump),
    garantindo escape automático e correto de strings com ':', '#', acentos
    e demais caracteres especiais. O template Jinja2 (frontmatter_template.jinja2)
    serve como referência documentada da estrutura, não como motor de render.
"""

import argparse
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
import yaml  # PyYAML

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SKILL_NAME = "yaml-normalizador-juridico"
SKILL_VERSION = "1.1.0"
DEFAULT_LANGUAGE = "pt-BR"
FALLBACK_SKILL_KEY = "REVISAR_MANUAL"

ACAO_TO_STATUS = {
    "manter":   {"review_status": "approved",       "status": "ready"},
    "resumir":  {"review_status": "approved",       "status": "ready"},
    "revisar":  {"review_status": "pending_review",  "status": "needs_review"},
}

REQUIRED_FIELDS = [
    "piece_id", "document_type", "acao_curatorial", "modo_aplicado",
    "justificativa_curta", "impacto_processual", "impacto_sentenca_confirmado",
    "prioridade", "compressao_sugerida", "encaminhamento", "audit_trail",
    "text", "anchors", "pages_start", "pages_end", "source_file",
    "source_path", "source_sha256", "process_group_id", "origin_piece_index",
]

PT_MONTHS = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
    "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
    "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12",
}

logger = logging.getLogger(SKILL_NAME)


# ---------------------------------------------------------------------------
# Carregamento do routing map
# ---------------------------------------------------------------------------

def load_routing_map(path: Path) -> dict:
    """Carrega o routing_map.yaml e retorna dict {document_type: skill_key}."""
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    routing = {}
    for doc_type, entry in raw.get("routing", {}).items():
        if not entry.get("deprecated", False):
            routing[doc_type] = entry.get("skill_key", FALLBACK_SKILL_KEY)

    fallback_key = raw.get("fallback", {}).get("skill_key", FALLBACK_SKILL_KEY)
    routing["__fallback__"] = fallback_key
    return routing


def resolve_skill_key(document_type: str, routing: dict) -> tuple[str, bool]:
    """
    Retorna (skill_key, is_routable).
    is_routable=False indica que o tipo não está no mapa.
    """
    if document_type in routing:
        key = routing[document_type]
        return key, key != FALLBACK_SKILL_KEY
    return routing.get("__fallback__", FALLBACK_SKILL_KEY), False


# ---------------------------------------------------------------------------
# Normalização de dados
# ---------------------------------------------------------------------------

def normalize_text_body(text: str) -> str:
    """Sanitização mínima do corpo textual — preserva conteúdo."""
    # Normalizar quebras de linha Windows
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Colapsar mais de 3 linhas em branco consecutivas para 2
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    # Trim de início e fim
    return text.strip()


def normalize_date(raw_date: str | None) -> str | None:
    """Normaliza datas para ISO-8601 (YYYY-MM-DD) ou retorna None."""
    if not raw_date:
        return None

    raw = raw_date.strip()

    # Já no formato ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # DD/MM/YYYY
    m = re.match(r"^(\d{1,2})/(\d{2})/(\d{4})$", raw)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"

    # "DD de Mês de YYYY"
    m = re.match(
        r"^(\d{1,2})\s+de\s+([a-záéíóúãõâêôç]+)\s+de\s+(\d{4})$",
        raw, re.IGNORECASE
    )
    if m:
        d, month_str, y = m.groups()
        month_num = PT_MONTHS.get(month_str.lower())
        if month_num:
            return f"{y}-{month_num}-{d.zfill(2)}"

    logger.warning("Data não reconhecida: '%s' → null", raw_date)
    return None


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_party(name: str) -> str | None:
    """Normaliza nome de parte: maiúsculas, sem acento, sem pontuação extra."""
    cleaned = _strip_accents(name).upper()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)  # Remove pontuação
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else None


def normalize_parties(parties_raw: list | None) -> list:
    """Retorna lista de partes normalizadas."""
    if not parties_raw:
        return []
    result = []
    for p in parties_raw:
        normalized = normalize_party(str(p))
        if normalized:
            result.append(normalized)
    return result


def build_tags(piece: dict, is_routable: bool) -> list:
    """Gera lista de tags automáticas conforme normalization_rules.md §9."""
    tags = []
    if piece.get("acao_curatorial") == "revisar":
        tags.append("requer_revisao")
    if not is_routable:
        tags.append("nao_roteavel")
    if piece.get("impacto_sentenca_confirmado"):
        tags.append("impacto_sentenca")
    pri = piece.get("prioridade")
    if isinstance(pri, int) and pri <= 2:
        tags.append("prioridade_alta")
    elif pri == "alta":
        tags.append("prioridade_alta")  # compatibilidade com legado
    return tags


# ---------------------------------------------------------------------------
# Geração do frontmatter
# ---------------------------------------------------------------------------

def build_frontmatter_context(piece: dict, routing: dict, ts: str) -> dict:
    """Monta o contexto completo para renderização do template Jinja2."""
    skill_key, is_routable = resolve_skill_key(piece["document_type"], routing)

    acao = piece.get("acao_curatorial", "revisar")
    status_map = ACAO_TO_STATUS.get(acao, {"review_status": "pending_review", "status": "needs_review"})

    if not is_routable:
        status_map = {"review_status": "unroutable", "status": "needs_review"}

    document_date = normalize_date(piece.get("document_date"))
    parties_normalized = normalize_parties(piece.get("parties_raw"))

    # Tags com verificação de data futura
    tags = build_tags(piece, is_routable)
    if document_date:
        try:
            doc_dt = datetime.fromisoformat(document_date)
            now_dt = datetime.now()
            if doc_dt.date() > now_dt.date():
                tags.append("data_futura")
        except ValueError:
            pass

    # Audit trail: preservar + acrescentar entrada desta skill
    audit_trail = list(piece.get("audit_trail", []))

    return {
        # Identificação
        "piece_id": piece["piece_id"],
        "document_type": piece["document_type"],
        "skill_key": skill_key,
        # Rastreabilidade
        "source_file": piece["source_file"],
        "source_path": piece["source_path"],
        "source_sha256": piece["source_sha256"],
        "pages_start": piece["pages_start"],
        "pages_end": piece["pages_end"],
        "process_group_id": piece["process_group_id"],
        "origin_piece_index": piece["origin_piece_index"],
        # Decisão curatorial
        "acao_curatorial": acao,
        "priority": piece.get("prioridade", 3),
        "impacto_processual": piece.get("impacto_processual", "irrelevante"),
        "impacto_sentenca_confirmado": piece.get("impacto_sentenca_confirmado", False),
        # Status
        "review_status": status_map["review_status"],
        "status": status_map["status"],
        # Controle
        "language": piece.get("language", DEFAULT_LANGUAGE),
        "normalized_at": ts,
        # Jurídicos opcionais
        "title": piece.get("title") or None,
        "document_date": document_date,
        "parties_normalized": parties_normalized,
        "court": piece.get("court") or None,
        "judge": piece.get("judge") or None,
        "tags": tags,
        "notes": piece.get("justificativa_curta") or None,
        # Auditoria
        "audit_trail": audit_trail,
    }


def render_frontmatter(ctx: dict, template_path: Path = None) -> str:
    """
    Renderiza o frontmatter YAML via PyYAML, garantindo escape correto de
    strings com ':', '#', acentos e demais caracteres especiais.

    O parâmetro template_path é mantido por compatibilidade de assinatura,
    mas não é usado na renderização: o PyYAML é o único motor de saída YAML.
    """
    # Construir audit_trail completo (preservado + entrada desta skill)
    audit_trail_full = list(ctx.get("audit_trail", []))
    audit_trail_full.append({
        "stage": SKILL_NAME,
        "timestamp": ctx["normalized_at"],
        "action": "frontmatter_gerado",
        "notes": f"skill_key={ctx['skill_key']}; review_status={ctx['review_status']}",
    })

    # Construir o dict na ordem desejada usando dict literal ordenado (Python 3.7+)
    frontmatter = {
        # Seção: Identificação
        "piece_id":           ctx["piece_id"],
        "document_type":      ctx["document_type"],
        "skill_key":          ctx["skill_key"],
        # Seção: Rastreabilidade
        "source_file":        ctx["source_file"],
        "source_path":        ctx["source_path"],
        "source_sha256":      ctx["source_sha256"],
        "pages_start":        ctx["pages_start"],
        "pages_end":          ctx["pages_end"],
        "process_group_id":   ctx["process_group_id"],
        "origin_piece_index": ctx["origin_piece_index"],
        # Seção: Curadoria
        "acao_curatorial":    ctx["acao_curatorial"],
        "priority":           ctx["priority"],
        "impacto_processual": ctx["impacto_processual"],
        "impacto_sentenca_confirmado":   bool(ctx["impacto_sentenca_confirmado"]),
        # Seção: Status
        "review_status":      ctx["review_status"],
        "status":             ctx["status"],
        # Seção: Controle
        "language":           ctx.get("language", DEFAULT_LANGUAGE),
        "created_by_skill":   SKILL_NAME,
        "normalized_at":      ctx["normalized_at"],
        # Seção: Jurídicos opcionais
        "title":              ctx.get("title"),
        "document_date":      ctx.get("document_date"),
        "parties_normalized": ctx.get("parties_normalized") or [],
        "court":              ctx.get("court"),
        "judge":              ctx.get("judge"),
        # Seção: Anotações
        "tags":               ctx.get("tags") or [],
        "notes":              ctx.get("notes"),
        # Seção: Auditoria
        "audit_trail":        audit_trail_full,
    }

    # Serializar com PyYAML — allow_unicode=True preserva pt-BR sem escapes \uXXXX
    yaml_body = yaml.dump(
        frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )

    return f"---\n{yaml_body}---"


# ---------------------------------------------------------------------------
# Processamento de peças
# ---------------------------------------------------------------------------

def validate_required_fields(piece: dict) -> list[str]:
    """Retorna lista de campos obrigatórios ausentes."""
    return [f for f in REQUIRED_FIELDS if f not in piece]


def process_piece(
    piece: dict,
    routing: dict,
    output_dir: Path,
    ts: str,
) -> bool:
    """Processa uma peça e gera o arquivo .md. Retorna True em sucesso."""
    piece_id = piece.get("piece_id", "<desconhecido>")

    # Validar campos obrigatórios
    missing = validate_required_fields(piece)
    if missing:
        logger.error("[%s] Campos obrigatórios ausentes: %s", piece_id, missing)
        return False

    # Peças marcadas como remover: não gerar artefato
    acao = piece.get("acao_curatorial")
    if acao == "remover":
        logger.info("[%s] Ignorada — acao_curatorial=remover", piece_id)
        return True  # Não é erro; apenas não gera arquivo

    # Montar contexto
    try:
        ctx = build_frontmatter_context(piece, routing, ts)
    except Exception as e:
        logger.error("[%s] Erro ao montar contexto: %s", piece_id, e)
        return False

    # Renderizar frontmatter via PyYAML
    try:
        frontmatter = render_frontmatter(ctx)
    except Exception as e:
        logger.error("[%s] Erro ao renderizar frontmatter: %s", piece_id, e)
        return False

    # Normalizar corpo textual
    body = normalize_text_body(piece.get("text", ""))

    # Montar conteúdo final
    content = f"{frontmatter}\n\n{body}\n"

    # Nome do arquivo
    process_group_id = piece.get("process_group_id", "unknown")
    filename = f"{process_group_id}__{piece_id}.md"
    output_path = output_dir / filename

    # Persistir
    try:
        output_path.write_text(content, encoding="utf-8")
        logger.info("[%s] Artefato gerado: %s", piece_id, output_path)
        return True
    except Exception as e:
        logger.error("[%s] Erro ao escrever arquivo: %s", piece_id, e)
        return False


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------

def load_input(input_path: Path) -> list[dict]:
    """Carrega um JSON (objeto ou array) como lista de peças."""
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Input JSON inválido: esperado dict ou list, got {type(data)}")


def main():
    parser = argparse.ArgumentParser(
        description=f"{SKILL_NAME} v{SKILL_VERSION} — Normalizador YAML jurídico"
    )
    parser.add_argument("--input", required=True, help="Caminho do JSON de entrada")
    parser.add_argument("--output-dir", required=True, help="Diretório de saída dos .md")
    parser.add_argument(
        "--routing-map",
        default=str(Path(__file__).parent.parent / "assets" / "routing_map.yaml"),
        help="Caminho do routing_map.yaml"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr
    )

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    routing_map_path = Path(args.routing_map)

    if not input_path.exists():
        logger.error("Arquivo de input não encontrado: %s", input_path)
        sys.exit(2)

    output_dir.mkdir(parents=True, exist_ok=True)

    if not routing_map_path.exists():
        logger.error("routing_map.yaml não encontrado: %s", routing_map_path)
        sys.exit(2)

    # Timestamp de execução
    ts = datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")

    # Carregar routing
    try:
        routing = load_routing_map(routing_map_path)
        logger.info("Routing map carregado: %d tipos mapeados", len(routing) - 1)
    except Exception as e:
        logger.error("Falha ao carregar routing map: %s", e)
        sys.exit(2)

    # Carregar peças
    try:
        pieces = load_input(input_path)
        logger.info("Peças carregadas: %d", len(pieces))
    except Exception as e:
        logger.error("Falha ao carregar input: %s", e)
        sys.exit(2)

    # Processar
    success = 0
    errors = 0
    skipped = 0

    for piece in pieces:
        acao = piece.get("acao_curatorial")
        if acao == "remover":
            skipped += 1
            logger.info("[%s] Pulada (remover)", piece.get("piece_id", "?"))
            continue

        ok = process_piece(piece, routing, output_dir, ts)
        if ok:
            success += 1
        else:
            errors += 1

    logger.info(
        "Conclusão: %d geradas | %d puladas | %d erros",
        success, skipped, errors
    )

    if errors > 0 and success == 0:
        sys.exit(2)  # Falha total
    elif errors > 0:
        sys.exit(1)  # Erros parciais
    else:
        sys.exit(0)  # Sucesso


if __name__ == "__main__":
    main()
