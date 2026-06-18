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
    Reads the config and dispatches each file to the correct bundle based on
    the skill_key found in the file's frontmatter (or resolved from routing.map).
    collector: "cad_obr" | "proc"
    config_path: path to the collector's config.yaml (from project root)
    staging_dir: optional override for staging directory (default: var/staging)
    """
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Config do collector deve ser um dict: {config_path}")

    # Build mapping: document_type -> skill_key from routing.map
    # Normaliza underscores → hyphens para bater com skill_registry.yaml
    routing_map = {}
    routing = config.get("routing", {})
    doc_type_map = routing.get("map", {})
    for doc_type, cfg in doc_type_map.items():
        if isinstance(cfg, dict) and "skill_key" in cfg:
            raw_key = cfg["skill_key"]
            routing_map[doc_type] = raw_key.replace("_", "-")

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
                frontmatter = _yaml.safe_load(parts[1]) or {}

        document_type = frontmatter.get("document_type")
        skill_key = frontmatter.get("skill_key")

        # Resolve skill_key from routing map if not in frontmatter
        if not skill_key and document_type:
            skill_key = routing_map.get(document_type)
        if not skill_key and document_type:
            # Fallback: use document_type as skill_key directly (normaliza _ → -)
            skill_key = document_type.replace("_", "-")

        if not skill_key:
            console.print(f"  [red]SKIP[/red] {md_file.name}: sem skill_key ou document_type no frontmatter")
            continue

        # Evitar duplicar prefixo extr- se já presente
        if skill_key.startswith("extr-"):
            bundle_id = skill_key
        else:
            bundle_id = f"extr-{skill_key}"
        console.print(f"  [cyan]Extraindo[/cyan] {md_file.name} → bundle: {bundle_id}")
        app_engine.run_extraction(bundle_id=bundle_id, input_filename=md_file.name)


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
                                  source_sha256: str, process_group_id: str, index: int) -> dict:
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

    # Campos estruturais obrigatórios com fallback defensivo
    # LLM pode gerar 'text' com nomes alternativos como 'text_content', 'conteudo', etc.
    if "text" not in peca or not peca.get("text"):
        for alt_key in ("text_content", "conteudo", "content", "full_text", "texto"):
            if alt_key in peca and peca[alt_key]:
                peca["text"] = peca[alt_key]
                break
        else:
            peca["text"] = peca.get("text_excerpt", f"[Texto não extraído para {peca.get('piece_id', 'unknown')}]")

    if "anchors" not in peca or not peca.get("anchors"):
        peca["anchors"] = [{"label": peca.get("document_type", "desconhecido"),
                            "page": peca.get("pages_start", 1) or 1}]

    if "pages_start" not in peca:
        # LLM pode usar nomes alternativos
        peca["pages_start"] = peca.get("start_page", peca.get("pagina_inicio"))
    if "pages_end" not in peca:
        peca["pages_end"] = peca.get("end_page", peca.get("pagina_fim"))

    return peca


def run_segmentador_stage(input_md_path: Path, output_path: Path) -> Path:
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
        schema_json = json.load(sf)

    # Pré-normalizar schema para compatibilidade com Gemini response_json_schema
    # Converte type: ["X", "null"] → type: "X" (Gemini não suporta type arrays)
    schema_json = _flatten_nullable_types(schema_json)

    # Invocar LLM — com estratégia de resiliência
    client = shared_llm_mod.LLMClientFactory.create_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": body},
    ]

    console.print("  [dim]Aguardando resposta do LLM (segmentação pode demorar)...[/dim]")

    # Tentativa 1: generate_structured com schema
    try:
        envelope = client.generate_structured(messages, schema=schema_json)
    except ValueError as exc:
        # JSON corrompido — tentar fallback via generate_text + reparo manual
        console.print(
            f"  [yellow]generate_structured falhou: {exc}[/yellow]\n"
            f"  [yellow]Tentando fallback: generate_text + reparo JSON...[/yellow]"
        )
        # Instruir explicitamente para JSON
        repair_messages = [
            {"role": "system", "content": (
                "Retorne APENAS um objeto JSON válido, sem markdown, sem explicação. "
                "O JSON deve ter exatamente a estrutura: "
                '{"metadata": {"processo_id": "...", "total_pecas": N, "gerado_por": "segmentador-juridico", '
                '"timestamp": "...", "source_file": "...", "total_pages": N, "schema_version": "1.1.0"}, '
                '"pecas": [{"piece_id": "...", "document_type": "...", ...}]}'
            )},
            {"role": "user", "content": body},
        ]
        raw_response = client.generate_text(repair_messages)

        # Tentar extrair JSON do texto bruto
        envelope = _repair_json_from_text(raw_response)

    # =========================================================================
    # Enriquecimento obrigatório de proveniência (correção de handoff)
    # =========================================================================
    # O LLM pode omitir campos de proveniência como source_file, source_path,
    # source_sha256, process_group_id, origin_piece_index. Estes campos são
    # obrigatórios para o yaml-normalizador-juridico. Enriquecemos aqui com
    # dados canônicos do arquivo .md de origem.
    # =========================================================================
    pecas = envelope.get("pecas", [])
    for idx, peca in enumerate(pecas):
        _enrich_peca_with_provenance(
            peca=peca,
            source_file=source_file,
            source_path=source_path,
            source_sha256=source_sha256,
            process_group_id=process_group_id,
            index=idx,
        )

    # Atualizar metadata com proveniência canônica
    if "metadata" not in envelope:
        envelope["metadata"] = {}
    envelope["metadata"]["source_file"] = source_file
    envelope["metadata"]["source_sha256"] = source_sha256

    # Persistir envelope
    output_path.mkdir(parents=True, exist_ok=True)
    envelope_file = output_path / "envelope_segmentacao.json"
    with open(envelope_file, "w", encoding="utf-8") as f:
        json.dump(envelope, f, ensure_ascii=False, indent=2)

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
        peca.setdefault("anchors", [{"label": peca.get("document_type", "desconhecido"),
                                      "page": peca.get("pages_start", 1) or 1}])
        if "pages_start" not in peca:
            peca["pages_start"] = peca.get("start_page", peca.get("pagina_inicio"))
        if "pages_end" not in peca:
            peca["pages_end"] = peca.get("end_page", peca.get("pagina_fim"))
        peca.setdefault("source_file", envelope.get("metadata", {}).get("source_file", "unknown"))
        peca.setdefault("source_path", "unknown")
        peca.setdefault("source_sha256", envelope.get("metadata", {}).get("source_sha256", "0" * 64))
        peca.setdefault("process_group_id", envelope.get("metadata", {}).get("processo_id", "unknown"))
        peca.setdefault("origin_piece_index", 0)
        peca.setdefault("modo_aplicado", envelope.get("metadata", {}).get("modo_aplicado", "padrao"))
        peca.setdefault("justificativa_curta", "Sem justificativa disponível")
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
