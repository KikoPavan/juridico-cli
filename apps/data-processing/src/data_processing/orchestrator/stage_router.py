"""
Stage router: maps CLI commands to individual pipeline stages.
Each function here is a thin adapter between the CLI and the stage implementation.
"""

from pathlib import Path
from typing import Literal
import re

from rich.console import Console

console = Console()

CollectorName = Literal["cad_obr", "proc"]


def _convert_via_skill(pdf_path: Path, out_md: Path) -> None:
    import subprocess
    import sys

    _project_root = Path(__file__).parents[5]
    skill_script = _project_root / "platform" / "skills" / "pdf-to-md" / "scripts" / "convert_pdf_to_md.py"

    result = subprocess.run(
        [sys.executable, str(skill_script), "--input", str(pdf_path), "--output", str(out_md),
         "--verbose"],
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stderr:
        sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(
            f"pdf-to-md skill failed (exit {result.returncode}) for {pdf_path.name}: "
            f"{result.stderr.strip()}"
        )


def run_convert_stage(input_path: Path, output_path: Path) -> None:
    """PDF → Markdown conversion stage using PyMuPDF."""
    from ..converters.markdown_engine.engine import Engine, EngineIO

    io = EngineIO(dir_pdf=input_path, dir_md=output_path)
    engine = Engine(io)
    pdfs = engine.list_pdfs()
    console.print(f"[bold]Converting {len(pdfs)} PDF(s)...[/bold]")
    console.print(f"  Input : {input_path}")
    console.print(f"  Output: {output_path}")

    moves = engine.run_batch(_convert_via_skill)
    for mv in moves:
        if mv.ok:
            console.print(f"  [green]OK[/green] {mv.stem}.md ({mv.out_md})")
        else:
            console.print(f"  [red]FAIL[/red] {mv.stem}: {mv.error}")


def run_clean_stage(input_path: Path, output_path: Path) -> None:
    """Legal cleaning stage."""
    from ..cleaners.clean_legal_docs import LegalDocCleaner

    cleaner = LegalDocCleaner()
    results = cleaner.clean_batch(str(input_path), str(output_path))
    ok = sum(1 for _, s, _ in results if s)
    console.print(f"[bold]Cleaned {ok}/{len(results)} file(s)[/bold]")
    for name, success, msg in results:
        icon = "[green]OK[/green]" if success else "[red]FAIL[/red]"
        console.print(f"  {icon} {name} — {msg}")


def run_analyze_stage(input_path: Path, output_path: Path) -> None:
    """Structural rule analysis stage."""
    from ..rule_analysis.analisador_de_regras import GeradorDeRegras

    output_path.mkdir(parents=True, exist_ok=True)
    rules_file = output_path / "regras_propostas.txt"
    gerador = GeradorDeRegras(min_ocorrencias=2, min_comprimento=25)
    frases = gerador.analisar_diretorio(str(input_path))
    if frases:
        gerador.gerar_arquivo_regras(frases, str(rules_file))
        console.print(f"[bold]Rule analysis complete:[/bold] {rules_file}")
    else:
        console.print("[yellow]No repeated phrases found.[/yellow]")

    # Escreve o Frontmatter YAML obrigatório da V1.1 com rastreabilidade neutra (1:1 staging)
    import hashlib
    import yaml
    from datetime import datetime, timezone

    # Heurística mínima: inferir document_type pelo nome do arquivo ou conteúdo
    DOC_TYPE_HINTS = {
        "peti": "peticao_processo",
        "contest": "contestacao_processo",
        "decis": "decisao_processo",
        "cabecalho": "cabecalho_processo",
        "mandato": "mandato_processo",
        "procur": "procuracao",
    }

    for md_file in input_path.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")

        # Se já tem frontmatter, não sobrescrever
        if content.startswith("---"):
            # Copiar para output sem alteração
            import shutil
            shutil.copy2(md_file, output_path / md_file.name)
            console.print(f"  [dim]Frontmatter já presente[/dim] {md_file.name}")
            continue

        # Inferir document_type do nome do arquivo
        stem_lower = md_file.stem.lower()
        document_type = "peticao_processo"  # default brownfield para homologação
        for hint, dtype in DOC_TYPE_HINTS.items():
            if hint in stem_lower:
                document_type = dtype
                break

        # Mapear document_type -> skill_key (usar hyphen, conforme skill_registry.yaml)
        DOC_TO_SKILL = {
            "peticao_processo": "peticao-processo",
            "contestacao_processo": "contestacao-processo",
            "decisao_processo": "decisao-processo",
            "cabecalho_processo": "cabecalho-processo",
            "mandato_processo": "mandato-processo",
            "procuracao": "procuracao",
            "processo": "processo",
        }
        skill_key = DOC_TO_SKILL.get(document_type, document_type)
        target_schema = f"platform/skills/extr-{skill_key}/assets/{document_type}.schema.json"

        raw = md_file.read_bytes()
        source_sha256 = hashlib.sha256(raw).hexdigest()

        fm = {
            "document_type": document_type,
            "skill_key": skill_key,
            "target_schema": target_schema,
            "source_id": md_file.stem,
            "source_sha256": source_sha256,
            "source_filename": md_file.name,
            "language": "pt-BR",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": "cleaned_and_analyzed",
            "integrity": "verified",
        }
        new_content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---\n{content}"
        out_file = output_path / md_file.name
        out_file.write_text(new_content, encoding="utf-8")
        console.print(f"  [green]YAML Injected[/green] {md_file.name} (type={document_type})")


def run_collect_stage(collector: CollectorName, config_path: Path, staging_dir: Path | None = None) -> None:
    """
    Dispatch to the new DataExtractorApp (V1.1 Gemini engine) dynamically.
    Reads normalized Markdown and dispatches approved files using only the
    explicit, registered extr-* skill_key found in frontmatter.
    collector: "cad_obr" | "proc"
    config_path: path to the collector's config.yaml (from project root)
    staging_dir: optional override for staging directory (default: var/staging)
    """
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Config do collector deve ser um dict: {config_path}")

    console.print(f"[bold]Iniciando Extração Gemini (DataExtractor)[/bold] collector: {collector}")

    if staging_dir is None:
        staging_dir = Path("var/staging")
    if not staging_dir.exists():
        console.print(f"[yellow]Pasta staging não encontrada ({staging_dir}). Nada a processar.[/yellow]")
        return

    md_files = list(staging_dir.glob("*.md"))
    if not md_files:
        console.print(f"[yellow]Nenhum .md encontrado em {staging_dir} para extrair.[/yellow]")
        return

    from ..extractor import DataExtractorApp
    app_engine = DataExtractorApp(platform_path="platform", var_dir="var", staging_path=str(staging_dir))

    for md_file in md_files:
        # Parse frontmatter to get document_type and resolve skill_key
        raw_text = md_file.read_text(encoding="utf-8")
        frontmatter = {}
        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                import yaml as _yaml
                try:
                    frontmatter = _yaml.safe_load(parts[1]) or {}
                except _yaml.YAMLError as exc:
                    console.print(
                        f"  [yellow]SKIP[/yellow] {md_file.name}: "
                        f"frontmatter inválido ({exc})"
                    )
                    continue

        if not isinstance(frontmatter, dict):
            console.print(f"  [yellow]SKIP[/yellow] {md_file.name}: frontmatter inválido")
            continue

        status = frontmatter.get("status")
        review_status = frontmatter.get("review_status")
        skill_key = frontmatter.get("skill_key")

        if status != "ready":
            console.print(
                f"  [yellow]SKIP[/yellow] {md_file.name}: status={status!r}, esperado 'ready'"
            )
            continue
        if review_status != "approved":
            console.print(
                f"  [yellow]SKIP[/yellow] {md_file.name}: "
                f"review_status={review_status!r}, esperado 'approved'"
            )
            continue
        if skill_key == "REVISAR_MANUAL":
            console.print(f"  [yellow]SKIP[/yellow] {md_file.name}: revisão manual")
            continue
        if not isinstance(skill_key, str) or not skill_key.startswith("extr-"):
            console.print(
                f"  [yellow]SKIP[/yellow] {md_file.name}: "
                f"skill_key explícito extr-* ausente ou inválido"
            )
            continue

        console.print(f"  [cyan]Extraindo[/cyan] {md_file.name} → bundle: {skill_key}")
        try:
            app_engine.run_extraction(
                bundle_id=skill_key,
                input_filename=md_file.name,
                input_path=md_file,
            )
        except (ValueError, FileNotFoundError) as exc:
            console.print(f"  [red]REJECTED[/red] {md_file.name}: {exc}")


# ===========================================================================
# Nova Esteira Jurídica (opt-in)
# ===========================================================================

def _flatten_nullable_types(schema: dict) -> dict:
    """
    Mantém o schema inalterado.

    Gemini Structured Outputs atual aceita type arrays com null, por exemplo:
    type: ["string", "null"].

    A compatibilização principal do schema ocorre em
    packages/shared-llm/gemini_client.py.
    """
    return schema

def _repair_json_from_text(text: str) -> dict:
    """
    Tenta extrair e reparar um objeto JSON de um texto bruto de LLM.
    Estratégias:
    1. json.loads direto
    2. Extrair bloco entre primeiro '{' e último '}'
    3. Remover markdown fences se presentes
    4. Tentar fechar strings abertas (heurística simples)
    """
    import json

    # Remover markdown fences
    text = text.strip()
    if text.startswith("```"):
        # Remover ```json ... ```
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    # Tentar parse direto
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extrair entre primeiro '{' e último '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Heurística: tentar fechar strings abertas
    # Isso é básico — conta chaves/colchetes e tenta equilibrar
    repaired = candidate if 'candidate' in dir() else text
    open_braces = repaired.count("{") - repaired.count("}")
    open_brackets = repaired.count("[") - repaired.count("]")
    if open_braces > 0:
        repaired += "}" * open_braces
    if open_brackets > 0:
        repaired += "]" * open_brackets

    # Remover trailing comma antes de } ou ]
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Não foi possível reparar o JSON do LLM. "
            f"Erro: {e}\n"
            f"Texto bruto (primeiros 500 chars): {text[:500]}"
        )


def _normalize_document_type(raw_type: str) -> str:
    """
    Normaliza document_type gerado pelo LLM para o valor canônico do enum.
    O LLM pode gerar 'Petição Inicial', 'PETIÇÃO INICIAL', 'peticao_inicial', etc.
    Esta função converte para o formato snake_case sem acentos esperado pelo routing map.
    """
    import unicodedata

    if not raw_type:
        return "nao_classificado"

    # Remover acentos, lowercase, substituir espaços por underscore
    normalized = unicodedata.normalize("NFKD", raw_type)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[\s\-]+", "_", normalized)

    # Mapeamento explícito de variações conhecidas para valores canônicos
    DOC_TYPE_MAP = {
        "peticao_inicial": "peticao_inicial",
        "peticao": "peticao_inicial",
        "contestacao": "contestacao",
        "contestacao_reu": "contestacao",
        "sentenca": "sentenca",
        "sentenca": "sentenca",
        "despacho": "despacho",
        "procuracao": "procuracao",
        "mandato": "mandato",
        "recurso": "recurso",
        "apelacao": "recurso",
        "agravo": "recurso",
        "decisao_interlocutoria": "decisao_interlocutoria",
        "decisao": "decisao_interlocutoria",
        "laudo_pericial": "laudo_pericial",
        "laudo": "laudo_pericial",
        "contrato": "contrato",
        "cabecalho_processo": "cabecalho_processo",
        "cabecalho": "cabecalho_processo",
        "capa_processo": "capa_processo",
        "capa": "cabecalho_processo",
        "citacao": "citacao",
        "intimacao": "intimacao",
        "embargos_declaracao": "recurso",
        "impugnacao": "recurso",
        "memoriais": "recurso",
        "certidao": "certidao",
        "termo": "termo",
        "anexo": "anexo",
        "comprovante": "comprovante",
        "oficio": "oficio",
        "ata": "ata",
        "parecer": "parecer",
        "replica": "replica",
        "acordao": "acordao",
        "nao_classificado": "nao_classificado",
    }

    # Tentativa direta
    if normalized in DOC_TYPE_MAP:
        return DOC_TYPE_MAP[normalized]

    # Tentativa parcial: se contém substring conhecida
    for key, value in DOC_TYPE_MAP.items():
        if key in normalized or normalized in key:
            return value

    return "nao_classificado"


def _enrich_peca_with_provenance(peca: dict, source_file: str, source_path: str,
                                  source_sha256: str, process_group_id: str, index: int,
                                  envelope_metadata: dict | None = None,
                                  source_text: str = "") -> dict:
    """
    Enriquece uma peça com metadados de proveniência do arquivo .md de origem.
    Campos obrigatórios para o yaml-normalizador-juridico que o LLM pode omitir:
      - source_file, source_path, source_sha256, process_group_id, origin_piece_index
    Também garante campos estruturais ausentes com valores default seguros.
    """
    # Normalizar document_type para valor canônico do enum
    raw_type = peca.get("document_type", "")
    peca["document_type"] = _normalize_document_type(raw_type)

    # Proveniência — sempre sobrescrever com dados canônicos do arquivo de origem
    peca["source_file"] = source_file
    peca["source_path"] = source_path
    peca["source_sha256"] = source_sha256
    peca["process_group_id"] = process_group_id
    peca["origin_piece_index"] = index

    _canonicalize_piece_traceability(
        peca,
        envelope_metadata=envelope_metadata or {},
        source_text=source_text,
    )

    return peca


def _materialize_piece(
    peca: dict,
    body: str,
    index: int,
    *,
    next_piece: dict | None = None,
    all_pieces: list[dict] | None = None,
    locators: list[dict] | None = None,
) -> dict:
    """Completa o contrato final usando exclusivamente o Markdown como texto fonte."""
    peca = dict(peca)
    proposed = {
        "pages_start": _first_non_null(
            peca.get("pages_start"), peca.get("page_number_start")
        ),
        "pages_end": _first_non_null(
            peca.get("pages_end"), peca.get("page_number_end")
        ),
        "event": _first_non_null(peca.get("event"), peca.get("event_id")),
        "document_code": peca.get("document_code"),
    }
    peca["piece_id"] = peca.get("piece_id") or f"peca_{index + 1:03d}"
    locator_index = locators if locators is not None else _index_judicial_locators(body)
    materialized_text, start, end = _resolve_piece_text(
        peca,
        body,
        locator_index,
        index=index,
        next_piece=next_piece,
        all_pieces=all_pieces or [peca],
    )
    if not materialized_text:
        available = [
            {
                "physical_page": locator.get("physical_page"),
                "page": locator.get("page"),
                "process_number": locator["attrs"].get("process_number"),
                "event": locator["attrs"].get("event"),
                "document_code": locator["attrs"].get("document_code"),
            }
            for locator in locator_index
        ]
        raise ValueError(
            "Não foi possível materializar peça: "
            f"piece_id={peca['piece_id']!r}, "
            f"document_type={peca.get('document_type')!r}, "
            f"pages_start={peca.get('pages_start')!r}, "
            f"pages_end={peca.get('pages_end')!r}, "
            f"anchors={peca.get('anchors') or []!r}, "
            f"locators_disponiveis={available!r}"
        )
    peca["pages_start"] = start
    peca["pages_end"] = end
    peca["text"] = materialized_text
    _reconcile_piece_from_materialized_locators(peca, proposed)
    peca["text_excerpt"] = (peca.get("text_excerpt") or materialized_text[:500]).strip()
    peca["title"] = (peca.get("title") or peca["document_type"]).strip()[:200]
    peca["summary"] = (peca.get("summary") or peca["text_excerpt"][:500]).strip()
    peca["impacto_sentenca_proposto"] = peca.get("impacto_sentenca_proposto")
    peca["observacoes"] = peca.get("observacoes")
    peca["relevancia_estimada"] = peca.get("relevancia_estimada", 0.5)
    if start is not None and end is not None:
        peca["pages_total"] = int(end) - int(start) + 1
    else:
        peca["pages_total"] = 1
    return peca


_JUDICIAL_LOCATOR_RE = re.compile(r"\[\[judicial_locator:\s*(.*?)\]\]")
_JUDICIAL_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


_SEGMENTATION_DECISION_SCHEMA = {
    "type": "object",
    "required": ["pecas"],
    "additionalProperties": False,
    "properties": {
        "metadata": {"type": "object"},
        "pecas": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["document_type", "document_type_confidence"],
                "properties": {
                    "piece_id": {"type": "string"},
                    "piece_index": {"type": "integer"},
                    "document_type": {"type": "string"},
                    "document_type_confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "pages_start": {"type": "integer", "minimum": 1},
                    "pages_end": {"type": "integer", "minimum": 1},
                    "page_number_start": {"type": "integer", "minimum": 1},
                    "page_number_end": {"type": "integer", "minimum": 1},
                    "title": {"type": "string"},
                    "text_excerpt": {"type": "string"},
                    "summary": {"type": "string"},
                    "relevancia_estimada": {
                        "type": "number", "minimum": 0, "maximum": 1,
                    },
                    "process_number": {"type": "string"},
                    "event": {"type": ["string", "integer"]},
                    "document_code": {"type": "string"},
                    "anchors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["label", "page"],
                            "properties": {
                                "label": {"type": "string"},
                                "page": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                },
            },
        },
    },
}


def _extract_judicial_locators(text: str) -> list[tuple[str, dict]]:
    """Retorna locators literais e seus atributos, na ordem do Markdown."""
    result = []
    for match in _JUDICIAL_LOCATOR_RE.finditer(text or ""):
        result.append((match.group(0), dict(_JUDICIAL_ATTR_RE.findall(match.group(1)))))
    return result


def _index_judicial_locators(text: str) -> list[dict]:
    """Indexa locators por posição, página local e página física ordinal."""
    matches = list(_JUDICIAL_LOCATOR_RE.finditer(text or ""))
    parsed_pages = []
    for match in matches:
        attrs = dict(_JUDICIAL_ATTR_RE.findall(match.group(1)))
        try:
            parsed_pages.append(int(attrs["page"]))
        except (KeyError, TypeError, ValueError):
            parsed_pages.append(None)
    uses_global_page_numbers = bool(parsed_pages) and all(
        current is not None and previous is not None and current > previous
        for previous, current in zip(parsed_pages, parsed_pages[1:])
    )
    result = []
    for index, match in enumerate(matches):
        attrs = dict(_JUDICIAL_ATTR_RE.findall(match.group(1)))
        try:
            page = int(attrs["page"])
        except (KeyError, TypeError, ValueError):
            page = None
        result.append({
            "literal": match.group(0),
            "attrs": attrs,
            "page": page,
            "physical_page": page if uses_global_page_numbers and page is not None else index + 1,
            "start": match.start(),
            "end": match.end(),
            "segment_end": (
                matches[index + 1].start() if index + 1 < len(matches) else len(text)
            ),
        })
    return result


def _trusted_locator_values(locators: list[tuple[str, dict]], field: str) -> list[str]:
    """Retorna valores substantivos, ignorando separadores e tokens vazios."""
    values = []
    for _, attrs in locators:
        value = attrs.get(field)
        if not value or (
            field == "document_code" and attrs.get("kind") == "event_separator"
        ):
            continue
        value = value.strip()
        if field == "document_code" and not re.search(r"[A-Z0-9]", value):
            continue
        values.append(value)
    return values


def _consensus_locator_value(
    locators: list[tuple[str, dict]], field: str,
) -> str | None:
    values = _trusted_locator_values(locators, field)
    unique = list(dict.fromkeys(values))
    return unique[0] if len(unique) == 1 else None


def _is_trusted_document_code(value) -> bool:
    if not isinstance(value, str):
        return False
    value = value.strip()
    return bool(value and re.fullmatch(r"[A-Z0-9][A-Z0-9 _.-]*", value))


def _reconcile_piece_from_materialized_locators(peca: dict, proposed: dict) -> None:
    """Reconcilia identidade local e registra divergências da decisão compacta."""
    locators = _extract_judicial_locators(peca.get("text", ""))
    if not locators:
        return

    process_number = _consensus_locator_value(locators, "process_number")
    event = _consensus_locator_value(locators, "event")
    document_code = _consensus_locator_value(locators, "document_code")
    if document_code is None and _is_trusted_document_code(proposed.get("document_code")):
        document_code = proposed["document_code"].strip()
    applied = {
        "pages_start": peca.get("pages_start"),
        "pages_end": peca.get("pages_end"),
        "event": event,
        "document_code": document_code,
    }
    if process_number is not None:
        peca["process_number"] = process_number
    if event is not None:
        peca["event"] = event
    else:
        peca.pop("event", None)
        peca.pop("event_id", None)
    if document_code is not None:
        peca["document_code"] = document_code
    else:
        peca.pop("document_code", None)

    physical_start = int(peca.get("pages_start") or 1)
    local_pages = []
    for _, attrs in locators:
        try:
            local_pages.append(int(attrs["page"]))
        except (KeyError, TypeError, ValueError):
            local_pages.append(None)
    uses_local_anchor_pages = (
        bool(local_pages)
        and local_pages[0] == peca.get("pages_start")
        and local_pages[-1] == peca.get("pages_end")
        and all(
            current is not None and previous is not None and current > previous
            for previous, current in zip(local_pages, local_pages[1:])
        )
    )
    peca["anchors"] = [
        {
            "label": attrs.get("document_code") or attrs.get("event") or "judicial_locator",
            "page": local_pages[offset] if uses_local_anchor_pages else physical_start + offset,
            **({"process_number": attrs["process_number"]} if attrs.get("process_number") else {}),
            **({"event": attrs["event"]} if attrs.get("event") else {}),
            **({"document_code": attrs["document_code"]} if attrs.get("document_code") else {}),
        }
        for offset, (_, attrs) in enumerate(locators)
    ]

    changes = {
        key: {"proposed": proposed.get(key), "applied": applied.get(key)}
        for key in applied
        if (
            proposed.get(key) != applied.get(key)
            and str(proposed.get(key)) != str(applied.get(key))
        )
    }
    if changes:
        from datetime import datetime, timezone

        audit_trail = peca.get("audit_trail") or []
        audit_trail.append({
            "stage": "segmentador-juridico",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "traceability_reconciled_from_materialized_locators",
            "notes": changes,
        })
        peca["audit_trail"] = audit_trail


def _piece_identity(piece: dict) -> dict:
    anchors = piece.get("anchors") or []
    first_anchor = anchors[0] if anchors else {}
    return {
        "process_number": _first_non_null(
            piece.get("process_number"), piece.get("processo_id"),
            first_anchor.get("process_number"), first_anchor.get("processo_id"),
        ),
        "event": _first_non_null(
            piece.get("event"), piece.get("event_id"),
            first_anchor.get("event"), first_anchor.get("event_id"),
        ),
        "document_code": _first_non_null(
            piece.get("document_code"), first_anchor.get("document_code"),
        ),
    }


def _locator_matches_piece(locator: dict, piece: dict) -> bool:
    identity = _piece_identity(piece)
    comparable = [
        key for key, value in identity.items()
        if value is not None and locator["attrs"].get(key) is not None
    ]
    return not comparable or all(
        str(locator["attrs"][key]) == str(identity[key]) for key in comparable
    )


def _page_interval(
    body: str,
    locators: list[dict],
    piece: dict,
    start_page,
    end_page,
) -> str:
    try:
        start_page = int(start_page)
        end_page = int(end_page)
    except (TypeError, ValueError):
        return ""
    if start_page > end_page:
        return ""

    selected = [
        locator for locator in locators
        if start_page <= locator["physical_page"] <= end_page
    ]
    if not selected:
        return ""
    selected_pages = [locator["physical_page"] for locator in selected]
    if selected_pages[0] != start_page or selected_pages[-1] != end_page:
        return ""
    return body[selected[0]["start"]:selected[-1]["segment_end"]].strip()


def _piece_start_page(piece: dict | None):
    if not piece:
        return None
    anchors = piece.get("anchors") or []
    anchor_pages = [anchor.get("page") for anchor in anchors if anchor.get("page") is not None]
    return _first_non_null(
        piece.get("pages_start"),
        piece.get("page_number_start"),
        min(anchor_pages) if anchor_pages else None,
    )


def _contiguous_locator_groups(locators: list[dict]) -> list[list[dict]]:
    groups = []
    for locator in locators:
        attrs = locator["attrs"]
        identity = (
            attrs.get("process_number"), attrs.get("event"), attrs.get("document_code"),
        )
        if not any(identity):
            if groups:
                groups[-1].append(locator)
            continue
        previous_identity = groups[-1][0]["identity"] if groups else None
        if not groups or identity != previous_identity:
            groups.append([])
        locator = dict(locator)
        locator["identity"] = identity
        groups[-1].append(locator)
    return groups


def _resolve_piece_text(
    piece: dict,
    body: str,
    locators: list[dict],
    *,
    index: int,
    next_piece: dict | None,
    all_pieces: list[dict],
) -> tuple[str, int | None, int | None]:
    canonical_start = piece.get("pages_start")
    canonical_end = piece.get("pages_end")
    text = _page_interval(body, locators, piece, canonical_start, canonical_end)
    if text:
        return text, int(canonical_start), int(canonical_end)

    alias_start = piece.get("page_number_start")
    alias_end = piece.get("page_number_end")
    text = _page_interval(body, locators, piece, alias_start, alias_end)
    if text:
        return text, int(alias_start), int(alias_end)

    anchor_pages = [
        anchor.get("page") for anchor in piece.get("anchors") or []
        if anchor.get("page") is not None
    ]
    if anchor_pages:
        text = _page_interval(body, locators, piece, min(anchor_pages), max(anchor_pages))
        if text:
            return text, int(min(anchor_pages)), int(max(anchor_pages))

    current_start = _piece_start_page(piece)
    next_start = _piece_start_page(next_piece)
    if current_start is not None and next_start is not None:
        starts = [
            locator for locator in locators
            if locator["physical_page"] == int(current_start)
        ]
        next_starts = [
            locator for locator in locators
            if locator["physical_page"] == int(next_start)
            and locator["start"] > (starts[0]["start"] if starts else -1)
        ]
        if starts and next_starts:
            text = body[starts[0]["start"]:next_starts[0]["start"]].strip()
            pages = [
                locator["physical_page"] for locator in locators
                if starts[0]["start"] <= locator["start"] < next_starts[0]["start"]
            ]
            if text and pages:
                return text, min(pages), max(pages)

    groups = _contiguous_locator_groups(locators)
    if len(groups) >= len(all_pieces) and index < len(groups) and groups[index]:
        group = groups[index]
        text = body[group[0]["start"]:group[-1]["segment_end"]].strip()
        pages = [locator["physical_page"] for locator in group]
        if text and pages:
            return text, min(pages), max(pages)

    return "", None, None


def _locator_groups(text: str) -> dict[tuple, list[tuple[str, dict]]]:
    """Agrupa localizadores pela identidade judicial, sem usar página na chave."""
    groups = {}
    for locator in _extract_judicial_locators(text):
        attrs = locator[1]
        key = (
            attrs.get("process_number"),
            attrs.get("event"),
            attrs.get("document_code"),
        )
        groups.setdefault(key, []).append(locator)
    return groups


def _page_bounds(locators: list[tuple[str, dict]]) -> tuple[int | None, int | None]:
    pages = []
    for _, attrs in locators:
        try:
            pages.append(int(attrs["page"]))
        except (KeyError, TypeError, ValueError):
            continue
    return (min(pages), max(pages)) if pages else (None, None)


def _slice_markdown_by_pages(text: str, pages_start, pages_end) -> str:
    """Recorta páginas inclusivas mantendo literalmente os locators do Markdown."""
    if pages_start is None or pages_end is None:
        return text.strip()
    matches = list(_JUDICIAL_LOCATOR_RE.finditer(text))
    selected = []
    for index, match in enumerate(matches):
        attrs = dict(_JUDICIAL_ATTR_RE.findall(match.group(1)))
        try:
            page = int(attrs["page"])
        except (KeyError, TypeError, ValueError):
            continue
        if int(pages_start) <= page <= int(pages_end):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            selected.append(text[match.start():end])
    return "".join(selected).strip()


def _is_compact_segmentation(value) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("pecas"), list):
        return False
    if not value["pecas"]:
        return False
    return all(
        isinstance(piece, dict)
        and bool(piece.get("document_type"))
        and piece.get("document_type_confidence") in {"high", "medium", "low"}
        for piece in value["pecas"]
    )


def _infer_single_piece_type(text: str, source_file: str, document_code: str | None) -> str:
    evidence = " ".join((document_code or "", source_file, text[:1000])).lower()
    hints = {
        "peticao_inicial": ("inic1", "petição inicial", "peticao inicial"),
        "contestacao": ("contes", "contestação", "contestacao"),
        "sentenca": ("sentença", "sentenca"),
        "decisao_interlocutoria": ("decisão interlocutória", "decisao interlocutoria"),
        "procuracao": ("procuraç", "procurac"),
    }
    for document_type, tokens in hints.items():
        if any(token in evidence for token in tokens):
            return document_type
    return "nao_classificado"


def _single_piece_fallback(body: str, source_file: str) -> dict | None:
    groups = _locator_groups(body)
    if len(groups) != 1:
        return None
    (process_number, event, document_code), locators = next(iter(groups.items()))
    pages_start, pages_end = _page_bounds(locators)
    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else Path(source_file).stem
    return {
        "metadata": {},
        "pecas": [{
            "piece_id": "peca_001",
            "document_type": _infer_single_piece_type(body, source_file, document_code),
            "document_type_confidence": "high" if title_match or document_code else "low",
            "pages_start": pages_start,
            "pages_end": pages_end,
            "title": title,
            "text_excerpt": body[:500].strip(),
            "relevancia_estimada": 0.5,
            "process_number": process_number,
            "event": event,
            "document_code": document_code,
            "anchors": [
                {"label": attrs.get("document_code") or title, "page": int(attrs["page"])}
                for _, attrs in locators if attrs.get("page", "").isdigit()
            ],
        }],
    }


def _first_non_null(*values):
    return next((value for value in values if value is not None and value != ""), None)


def _locator_is_in_piece(attrs: dict, pages_start, pages_end) -> bool:
    """Filtra locator por página quando a peça possui intervalo conhecido."""
    if pages_start is None or pages_end is None or attrs.get("page") is None:
        return True
    try:
        page = int(attrs["page"])
        return int(pages_start) <= page <= int(pages_end)
    except (TypeError, ValueError):
        return True


def _canonicalize_piece_traceability(
    peca: dict,
    envelope_metadata: dict | None = None,
    source_text: str = "",
) -> dict:
    """Canonicaliza paginação, identidade, anchors e locators de uma peça."""
    metadata = envelope_metadata or {}

    peca["pages_start"] = _first_non_null(
        peca.get("pages_start"),
        peca.get("page_number_start"),
        peca.get("start_page"),
        peca.get("pagina_inicio"),
    )
    peca["pages_end"] = _first_non_null(
        peca.get("pages_end"),
        peca.get("page_number_end"),
        peca.get("end_page"),
        peca.get("pagina_fim"),
    )

    piece_locators = _extract_judicial_locators(peca.get("text", ""))
    source_locators = []
    if not piece_locators:
        source_locators = [
            (locator["literal"], locator["attrs"])
            for locator in _index_judicial_locators(source_text)
            if (
                peca["pages_start"] is None
                or peca["pages_end"] is None
                or int(peca["pages_start"])
                <= locator["physical_page"]
                <= int(peca["pages_end"])
            )
        ]
    active_locators = piece_locators or source_locators
    locator_attrs = (active_locators or [("", {})])[0][1]
    locator_process = _consensus_locator_value(active_locators, "process_number")
    locator_event = _consensus_locator_value(active_locators, "event")
    locator_document_code = _consensus_locator_value(active_locators, "document_code")

    process_number = _first_non_null(
        locator_process, peca.get("process_number"), peca.get("processo_id"),
        metadata.get("process_number"), metadata.get("processo_id"),
        locator_attrs.get("process_number"),
    )
    event = _first_non_null(
        locator_event, peca.get("event"), peca.get("event_id"),
        metadata.get("event"), metadata.get("event_id"),
        locator_attrs.get("event"),
    )
    document_code = _first_non_null(
        locator_document_code, peca.get("document_code"), metadata.get("document_code"),
    )
    if process_number is not None:
        peca["process_number"] = process_number
    if event is not None:
        peca["event"] = event
    if document_code is not None:
        peca["document_code"] = document_code

    # O texto do modelo pode omitir os marcadores do Markdown fonte. Reinsere
    # somente os locators pertencentes ao intervalo desta peça, sem reconstruí-los.
    text = peca.get("text", "")
    missing_locators = [literal for literal, _ in source_locators if literal not in text]
    if missing_locators:
        peca["text"] = "\n".join(missing_locators) + "\n\n" + text

    anchors = peca.get("anchors") or [{
        "label": peca.get("document_type", "desconhecido"),
        "page": peca.get("pages_start") or 1,
    }]
    for anchor in anchors:
        if anchor.get("page") is None:
            anchor["page"] = peca.get("pages_start") or 1
        if process_number is not None:
            anchor.setdefault("process_number", process_number)
        if event is not None:
            anchor.setdefault("event", event)
        if document_code is not None:
            anchor.setdefault("document_code", document_code)
    peca["anchors"] = anchors
    return peca


def _write_json_atomic(path: Path, value: dict) -> None:
    import json

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
    temporary_path.replace(path)


def run_segmentador_stage(
    input_md_path: Path,
    output_path: Path,
    *,
    llm_client=None,
) -> Path:
    """
    Etapa segmentador-juridico da nova esteira.

    Entrada: arquivos .md limpos (pós-clean)
    Saída:   envelope_segmentacao.json em output_path

    Usa o SkillDispatcher canônico + LLMClient real para segmentar
    documentos jurídicos em peças lógicas classificadas.
    """
    import json
    import hashlib
    import sys

    # Dynamic load do dispatcher canônico
    dispatcher_file = Path("platform/skill-runtime/skill_dispatcher.py")
    if not dispatcher_file.exists():
        raise FileNotFoundError(f"SkillDispatcher não encontrado: {dispatcher_file}")

    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_dispatcher", dispatcher_file)
    dispatcher_mod = importlib.util.module_from_spec(spec)
    sys.modules["skill_dispatcher"] = dispatcher_mod
    spec.loader.exec_module(dispatcher_mod)

    dispatcher = dispatcher_mod.SkillDispatcher(platform_path="platform")

    # Carregar LLMClient real
    shared_llm_file = Path("packages/shared-llm/client.py")
    if not shared_llm_file.exists():
        raise FileNotFoundError(f"shared-llm/client.py não encontrado: {shared_llm_file}")

    spec2 = importlib.util.spec_from_file_location("shared_llm_client", shared_llm_file)
    shared_llm_mod = importlib.util.module_from_spec(spec2)
    shared_llm_mod  # reference to avoid unused import warning
    spec2.loader.exec_module(shared_llm_mod)

    # Coletar .md limpos do staging
    md_files = list(input_md_path.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"Nenhum .md limpo encontrado em {input_md_path}")

    # Processar cada arquivo .md limpo
    # Para simplificar esta fase, processamos o primeiro .md encontrado
    # (suporte a múltiplos arquivos será adicionado em fase posterior)
    md_file = md_files[0]
    raw_text = md_file.read_text(encoding="utf-8")

    # Parse frontmatter se existir (para metadados de proveniência)
    frontmatter = {}
    body = raw_text
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            import yaml as _yaml
            frontmatter = _yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()

    # Computar hash SHA-256 do arquivo de origem
    source_sha256 = hashlib.sha256(md_file.read_bytes()).hexdigest()
    source_file = md_file.name
    source_path = str(md_file.resolve())

    # Inferir process_group_id do frontmatter ou do nome do arquivo
    process_group_id = frontmatter.get("process_group_id", md_file.stem)

    console.print(f"  [cyan]Segmentando[/cyan] {md_file.name} → segmentador-juridico")

    # Despatch via canônico
    dispatch_result = dispatcher.dispatch("segmentador-juridico")
    system_prompt = dispatch_result["system_prompt"]
    skill_config = dispatch_result["skill_config"]
    schema_ref = skill_config.get("schema_ref")

    if not schema_ref or not Path(schema_ref).exists():
        raise FileNotFoundError(f"Schema do segmentador não encontrado: {schema_ref}")

    with open(schema_ref, "r", encoding="utf-8") as sf:
        output_schema = json.load(sf)

    # O contrato do LLM contém apenas decisões compactas. O schema final é
    # aplicado somente depois que Python materializa texto e proveniência.
    decision_schema = _flatten_nullable_types(_SEGMENTATION_DECISION_SCHEMA)

    # Invocar LLM — com estratégia de resiliência
    client = llm_client or shared_llm_mod.LLMClientFactory.create_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": body},
    ]

    console.print("  [dim]Aguardando resposta do LLM (segmentação pode demorar)...[/dim]")

    # Uma resposta incompatível (inclusive fallback genérico de extração do
    # provider) nunca é promovida a Envelope de Processo.
    try:
        envelope = client.generate_structured(messages, schema=decision_schema)
        if not _is_compact_segmentation(envelope):
            raise ValueError("Resposta incompatível com a segmentação compacta")
    except ValueError as exc:
        console.print(
            f"  [yellow]Segmentação estruturada falhou: {exc}[/yellow]\n"
            "  [yellow]Tentando fallback determinístico de peça única...[/yellow]"
        )
        envelope = _single_piece_fallback(body, source_file)
        if envelope is None:
            raise ValueError(
                "Resposta do LLM incompatível e documento sem grupo judicial único"
            ) from exc

    # Persistir a decisão compacta antes de qualquer enriquecimento ou recorte.
    # Este artefato é diagnóstico e deliberadamente não usa o schema final.
    output_path.mkdir(parents=True, exist_ok=True)
    debug_envelope_file = output_path / "envelope_segmentacao_debug.json"
    _write_json_atomic(debug_envelope_file, envelope)

    # =========================================================================
    # Enriquecimento obrigatório de proveniência (correção de handoff)
    # =========================================================================
    # O LLM pode omitir campos de proveniência como source_file, source_path,
    # source_sha256, process_group_id, origin_piece_index. Estes campos são
    # obrigatórios para o yaml-normalizador-juridico. Enriquecemos aqui com
    # dados canônicos do arquivo .md de origem.
    # =========================================================================
    if "metadata" not in envelope:
        envelope["metadata"] = {}
    metadata = envelope["metadata"]
    source_locators = _extract_judicial_locators(body)
    source_locator_attrs = (source_locators or [("", {})])[0][1]
    process_number = _first_non_null(
        frontmatter.get("process_number"), frontmatter.get("processo_id"),
        metadata.get("process_number"), metadata.get("processo_id"),
        source_locator_attrs.get("process_number"),
    )
    event = _first_non_null(
        frontmatter.get("event"), frontmatter.get("event_id"),
        _consensus_locator_value(source_locators, "event"),
    )
    document_code = _first_non_null(
        frontmatter.get("document_code"),
        _consensus_locator_value(source_locators, "document_code"),
    )
    if process_number is not None:
        metadata["process_number"] = process_number
    metadata["event"] = event
    metadata["document_code"] = document_code

    compact_pieces = envelope["pecas"]
    locator_index = _index_judicial_locators(body)
    pecas = [
        _materialize_piece(
            piece,
            body,
            idx,
            next_piece=(compact_pieces[idx + 1] if idx + 1 < len(compact_pieces) else None),
            all_pieces=compact_pieces,
            locators=locator_index,
        )
        for idx, piece in enumerate(compact_pieces)
    ]
    envelope["pecas"] = pecas
    for idx, peca in enumerate(pecas):
        _enrich_peca_with_provenance(
            peca=peca,
            source_file=source_file,
            source_path=source_path,
            source_sha256=source_sha256,
            process_group_id=process_group_id,
            index=idx,
            envelope_metadata=metadata,
            source_text=body,
        )

    # Atualizar metadata com valores canônicos calculados localmente.
    from datetime import datetime, timezone

    locator_pages = _page_bounds(source_locators)
    metadata["processo_id"] = str(_first_non_null(
        metadata.get("processo_id"), process_number, process_group_id,
    ))
    metadata["total_pecas"] = len(pecas)
    metadata["gerado_por"] = "segmentador-juridico"
    metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
    metadata["source_file"] = source_file
    total_page_candidates = [
        frontmatter.get("total_pages"),
        len(locator_index) or None,
        locator_pages[1],
        max((piece.get("pages_end") or 1 for piece in pecas), default=1),
    ]
    metadata["total_pages"] = max(
        int(value) for value in total_page_candidates if value is not None
    )
    metadata["schema_version"] = "1.1.0"

    import jsonschema

    validation_errors = sorted(
        jsonschema.Draft7Validator(output_schema).iter_errors(envelope),
        key=lambda error: list(error.path),
    )
    if validation_errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in validation_errors[:5]
        )
        raise ValueError(f"Envelope do segmentador inválido: {details}")

    # Persistir envelope
    envelope_file = output_path / "envelope_segmentacao.json"
    _write_json_atomic(envelope_file, envelope)

    total_pecas = len(envelope.get("pecas", []))
    console.print(f"  [green]Segmentação concluída[/green] {envelope_file} ({total_pecas} peças)")

    return envelope_file


def run_curador_stage(envelope_path: Path, output_path: Path, modo: str = "padrao") -> Path:
    """
    Etapa curador-relevancia da nova esteira.

    Entrada: envelope_segmentacao.json
    Saída:   envelope_curadoria.json em output_path

    Motor determinístico — não usa LLM.
    """
    import json
    import sys

    # Adicionar o diretório de scripts do curador ao path para importação
    curador_scripts = Path("platform/skills/curador-relevancia/scripts")
    if not curador_scripts.exists():
        raise FileNotFoundError(f"Scripts do curador não encontrados: {curador_scripts}")

    sys.path.insert(0, str(curador_scripts))

    try:
        from curar import CuradorRelevancia
    finally:
        # Limpar sys.path para evitar poluição
        if str(curador_scripts) in sys.path:
            sys.path.remove(str(curador_scripts))

    # Carregar envelope de entrada
    with open(envelope_path, "r", encoding="utf-8") as f:
        envelope_entrada = json.load(f)

    # Adicionar modo de curadoria ao metadata
    if "metadata" not in envelope_entrada:
        envelope_entrada["metadata"] = {}
    envelope_entrada["metadata"]["modo_curadoria"] = modo

    console.print(f"  [cyan]Curadoria[/cyan] {envelope_path.name} → modo={modo}")

    curador = CuradorRelevancia(modo=modo)
    envelope_curado = curador.processar(envelope_entrada)

    # Persistir
    output_path.mkdir(parents=True, exist_ok=True)
    envelope_saida = output_path / "envelope_curadoria.json"
    with open(envelope_saida, "w", encoding="utf-8") as f:
        json.dump(envelope_curado, f, ensure_ascii=False, indent=2)

    pecas = envelope_curado.get("pecas", [])
    contar = {
        "manter": sum(1 for p in pecas if p.get("acao_curatorial") == "manter"),
        "resumir": sum(1 for p in pecas if p.get("acao_curatorial") == "resumir"),
        "remover": sum(1 for p in pecas if p.get("acao_curatorial") == "remover"),
        "revisar": sum(1 for p in pecas if p.get("acao_curatorial") == "revisar"),
    }
    console.print(
        f"  [green]Curadoria concluída[/green] {envelope_saida.name} "
        f"({len(pecas)} peças: {contar})"
    )

    return envelope_saida


def run_normalizador_stage(envelope_curado_path: Path, staging_path: Path) -> int:
    """
    Etapa yaml-normalizador-juridico da nova esteira.

    Entrada: envelope_curadoria.json
    Saída:   N arquivos .md normalizados em staging_path

    Motor determinístico — não usa LLM.
    Retorna número de arquivos .md gerados.
    """
    import json
    import sys

    # Carregar envelope curado
    with open(envelope_curado_path, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    pecas = envelope.get("pecas", [])
    if not pecas:
        console.print("  [yellow]Nenhuma peça no envelope curado — normalização ignorada[/yellow]")
        return 0

    # Filtrar peças elegíveis (acao_curatorial != "remover")
    pecas_elegiveis = [p for p in pecas if p.get("acao_curatorial") != "remover"]
    pecas_removidas = len(pecas) - len(pecas_elegiveis)

    if not pecas_elegiveis:
        console.print("  [yellow]Todas as peças marcadas como remover — nada a normalizar[/yellow]")
        return 0

    # =========================================================================
    # Validação defensiva de campos obrigatórios (correção de handoff)
    # =========================================================================
    # Garante que cada peça elegível tenha todos os campos exigidos pelo
    # yaml-normalizador-juridico. Campos ausentes são preenchidos com defaults
    # seguros para evitar falha silenciosa no process_piece.
    # =========================================================================
    NORM_REQUIRED = [
        "piece_id", "document_type", "acao_curatorial", "modo_aplicado",
        "justificativa_curta", "impacto_processual", "impacto_sentenca_confirmado",
        "prioridade", "compressao_sugerida", "encaminhamento", "audit_trail",
        "text", "anchors", "pages_start", "pages_end", "source_file",
        "source_path", "source_sha256", "process_group_id", "origin_piece_index",
    ]
    for peca in pecas_elegiveis:
        _canonicalize_piece_traceability(
            peca,
            envelope_metadata=envelope.get("metadata", {}),
        )
        piece_id = peca.get("piece_id", "<desconhecido>")
        missing = [f for f in NORM_REQUIRED if f not in peca]
        if missing:
            console.print(
                f"  [yellow]WARN[/yellow] Peça {piece_id} falta campos: {missing} — preenchendo defaults"
            )
        # Defaults defensivos para campos ausentes
        # LLM pode gerar 'text' com nomes alternativos
        if "text" not in peca or not peca.get("text"):
            for alt_key in ("text_content", "conteudo", "content", "full_text", "texto"):
                if alt_key in peca and peca[alt_key]:
                    peca["text"] = peca[alt_key]
                    break
            else:
                peca.setdefault("text", peca.get("text_excerpt", f"[Texto ausente para {piece_id}]"))
        peca.setdefault("source_file", envelope.get("metadata", {}).get("source_file", "unknown"))
        peca.setdefault("source_path", "unknown")
        peca.setdefault("source_sha256", envelope.get("metadata", {}).get("source_sha256", "0" * 64))
        peca.setdefault("process_group_id", envelope.get("metadata", {}).get("processo_id", "unknown"))
        peca.setdefault("origin_piece_index", 0)
        peca.setdefault("modo_aplicado", envelope.get("metadata", {}).get("modo_aplicado", "padrao"))
        peca.setdefault("justificativa_curta", "Sem justificativa disponível")
        if peca.get("document_type") in {
            "peticao_inicial", "contestacao", "decisao", "decisao_interlocutoria",
            "sentenca", "recurso",
        } and peca.get("impacto_processual") in (None, "irrelevante"):
            peca["impacto_processual"] = "relevante"
        else:
            peca.setdefault("impacto_processual", "irrelevante")
        peca.setdefault("impacto_sentenca_confirmado", False)
        peca.setdefault("prioridade", 3)
        peca.setdefault("compressao_sugerida", None)
        peca.setdefault("encaminhamento", None)
        peca.setdefault("audit_trail", [{"stage": "pipeline", "timestamp": "unknown",
                                          "action": "audit_trail_nao_disponível"}])
    # =========================================================================

    console.print(
        f"  [cyan]Normalização[/cyan] {len(pecas_elegiveis)} peças elegíveis "
        f"({pecas_removidas} removidas)"
    )

    # Adicionar scripts do normalizador ao path
    norm_scripts = Path("platform/skills/yaml-normalizador-juridico/scripts")
    if not norm_scripts.exists():
        raise FileNotFoundError(f"Scripts do normalizador não encontrados: {norm_scripts}")

    routing_map = Path("platform/skills/yaml-normalizador-juridico/assets/routing_map.yaml")
    if not routing_map.exists():
        raise FileNotFoundError(f"routing_map.yaml não encontrado: {routing_map}")

    sys.path.insert(0, str(norm_scripts))

    try:
        from apply_yaml_normalization import process_piece, load_routing_map
        from datetime import datetime, timezone

        routing = load_routing_map(routing_map)
        ts = datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")

        staging_path.mkdir(parents=True, exist_ok=True)
        gerados = 0

        for peca in pecas_elegiveis:
            piece_id = peca.get("piece_id", "<desconhecido>")
            ok = process_piece(peca, routing, staging_path, ts)
            if ok:
                gerados += 1
                console.print(f"  [green]Normalizado[/green] {piece_id}")
            else:
                console.print(f"  [red]Erro ao normalizar[/red] {piece_id}")
    finally:
        if str(norm_scripts) in sys.path:
            sys.path.remove(str(norm_scripts))

    console.print(f"  [green]Normalização concluída[/green] {gerados} arquivo(s) .md gerado(s)")
    return gerados


def run_nova_esteira_juridica_stage(
    input_md_path: Path,
    staging_path: Path,
    modo_curadoria: str = "padrao",
) -> int:
    """
    Orquestrador da nova esteira jurídica completa.

    Fluxo:
      .md limpo → segmentador-juridico → envelope JSON
      envelope JSON → curador-relevancia → envelope curado
      envelope curado → yaml-normalizador-juridico → .md normalizados em staging

    Retorna número de .md normalizados escritos em staging.
    """
    import tempfile

    console.rule("[bold magenta]Nova Esteira Jurídica[/bold magenta]")

    # Diretório temporário para artefatos intermediários
    with tempfile.TemporaryDirectory(prefix="juridico_esteira_") as tmp_dir:
        tmp = Path(tmp_dir)

        # 1. Segmentador
        console.rule("[magenta]Etapa: segmentador-juridico[/magenta]")
        envelope_seg_path = run_segmentador_stage(input_md_path, tmp)

        # 2. Curador
        console.rule("[magenta]Etapa: curador-relevancia[/magenta]")
        envelope_cur_path = run_curador_stage(envelope_seg_path, tmp, modo=modo_curadoria)

        # 3. Normalizador → staging
        console.rule("[magenta]Etapa: yaml-normalizador-juridico[/magenta]")
        gerados = run_normalizador_stage(envelope_cur_path, staging_path)

    console.rule("[bold green]Nova Esteira Jurídica concluída[/bold green]")
    return gerados
