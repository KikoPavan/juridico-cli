# agents/firac-cli/main.py
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import typer

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

from google import genai
from google.genai import types

app = typer.Typer(add_completion=False)

AGENT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = AGENT_DIR / "config.yaml"
DEFAULT_PROMPT_PATH = AGENT_DIR / "prompt.md"

DEFAULT_PROCESSO_PATH = Path(
    "outputs/processo/01_collector/collector_out_processo_consolidated.json"
)
DEFAULT_EVIDENCE_PATH = Path("outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json")
DEFAULT_LAW_PACK_PATH = Path("outputs/legal/law_pack_v1.json")

DEFAULT_OUT_JSON = Path("outputs/relatorio_firac.json")
DEFAULT_OUT_MD = Path("outputs/relatorio_firac.md")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _strip_yaml_frontmatter(text: str) -> str:
    """
    Remove YAML front matter do início do arquivo (--- ... ---), se existir.
    Importante para prompt.md/SKILL.md: não enviar metadados para o modelo.
    """
    t = text.lstrip()
    if not t.startswith("---"):
        return text
    parts = re.split(r"^\s*---\s*$", text, maxsplit=2, flags=re.M)
    if len(parts) >= 3:
        return parts[2].lstrip("\n")
    return text


def _read_text(path: Path, *, strip_frontmatter: bool = False) -> str:
    text = path.read_text(encoding="utf-8")
    if strip_frontmatter:
        text = _strip_yaml_frontmatter(text)
    return text


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    return data if isinstance(data, dict) else {}


def _cfg_get(cfg: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    """
    Lê cfg com caminho "a.b.c" (para runtime/model/budgets etc.).
    """
    cur: Any = cfg
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _extract_first_complete_json_object(text: str) -> Dict[str, Any]:
    """
    Extrai o primeiro objeto JSON completo do texto, tolerando:
    - markdown fences
    - textos antes/depois
    - necessidade de encontrar fechamento correto de chaves

    Se a resposta vier truncada (MAX_TOKENS), este método falha de forma determinística
    (chaves não balanceadas) em vez de depender de regex gulosa.
    """
    t = text.strip()

    # remove fenced blocks, se existirem
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()

    # encontra o início do primeiro '{'
    start = t.find("{")
    if start < 0:
        raise ValueError("Resposta do modelo não contém '{' (objeto JSON).")

    in_str = False
    esc = False
    depth = 0
    end = -1

    for i in range(start, len(t)):
        ch = t[i]

        if in_str:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == '"':
                in_str = False
            continue

        # fora de string
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
            continue

    if end < 0 or depth != 0:
        raise ValueError(
            "Resposta do modelo parece truncada ou inválida: objeto JSON não fechou."
        )

    raw = t[start:end]
    return json.loads(raw)


def _compress_law_pack(law_pack: Dict[str, Any], top_n: int) -> Dict[str, Any]:
    """
    Reduz o law_pack_v1 (saída do law-cli) para caber no contexto:
    - mantém effective_date/topics/queries
    - seleciona top_n rules por score
    - corta textos/excerpts
    """
    payload = (
        law_pack.get("payload", {}) if isinstance(law_pack.get("payload"), dict) else {}
    )
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        rules = []

    def score_of(r: Any) -> float:
        if isinstance(r, dict):
            try:
                return float(r.get("score") or 0.0)
            except Exception:
                return 0.0
        return 0.0

    rules_sorted = sorted(
        [r for r in rules if isinstance(r, dict)], key=score_of, reverse=True
    )[: max(0, int(top_n))]

    def slim_support(s: Any) -> Dict[str, Any]:
        if not isinstance(s, dict):
            return {}
        loc = s.get("locator", {}) if isinstance(s.get("locator"), dict) else {}
        return {
            "source_id": s.get("source_id"),
            "anchor": s.get("anchor"),
            "excerpt": (str(s.get("excerpt") or "")[:400]).strip(),
            "locator": {
                "path_rag": loc.get("path_rag"),
                "page_ref": loc.get("page_ref"),
                "chunk_id": loc.get("chunk_id"),
                "section_id": loc.get("section_id"),
            },
        }

    slim_rules = []
    for r in rules_sorted:
        support = r.get("support", [])
        sup0 = support[0] if isinstance(support, list) and support else {}
        meta = r.get("meta", {}) if isinstance(r.get("meta"), dict) else {}
        slim_rules.append(
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "citation": r.get("citation"),
                "score": r.get("score"),
                "text": (str(r.get("text") or "")[:650]).strip(),
                "support": [slim_support(sup0)] if sup0 else [],
                "meta": {
                    "doc_id": meta.get("doc_id"),
                    "article_no": meta.get("article_no"),
                    "hierarchy": meta.get("hierarchy"),
                },
            }
        )

    return {
        "schema_version": payload.get("schema_version"),
        "effective_date": payload.get("effective_date"),
        "topics": payload.get("topics"),
        "queries": payload.get("queries"),
        "rules": slim_rules,
    }


def _normative_basis_items(law_pack_ctx: Dict[str, Any]) -> list[Dict[str, Any]]:
    """
    Converte law_pack_ctx.rules para itens renderizáveis, sem depender do LLM.
    """
    out: list[Dict[str, Any]] = []
    rules = law_pack_ctx.get("rules", [])
    if not isinstance(rules, list):
        return out

    for r in rules:
        if not isinstance(r, dict):
            continue
        supports = r.get("support", [])
        if not isinstance(supports, list):
            supports = []

        stmt = str(r.get("text") or "").strip()
        if not stmt:
            stmt = str(r.get("title") or "").strip()

        out.append(
            {
                "id": str(r.get("id") or ""),
                "statement": stmt,
                "epistemic_status": "evidence",
                "supports": supports,
                "notes": str(r.get("citation") or "").strip(),
            }
        )
    return out


def _render_md(rel: Dict[str, Any]) -> str:
    case = rel.get("case", {}) if isinstance(rel.get("case"), dict) else {}
    title = str(case.get("title") or "Relatório FIRAC")
    case_id = str(case.get("case_id") or "")
    parties = case.get("parties") if isinstance(case.get("parties"), list) else []

    def sec(title_: str, items: Any) -> str:
        out = [f"## {title_}"]
        if not isinstance(items, list) or not items:
            out.append("_Sem itens._")
            return "\n".join(out)
        for it in items:
            if not isinstance(it, dict):
                continue
            sid = str(it.get("id") or "")
            stmt = str(it.get("statement") or "").strip()
            status = str(it.get("epistemic_status") or "").strip()

            out.append(f"### {sid}".strip())
            out.append(stmt if stmt else "_(vazio)_")

            if status:
                out.append(f"- **Status:** `{status}`")

            supports = it.get("supports")
            if isinstance(supports, list) and supports:
                out.append("- **Suportes:**")
                for s in supports:
                    if not isinstance(s, dict):
                        continue
                    source_id = str(s.get("source_id") or "")
                    anchor = str(s.get("anchor") or "")
                    excerpt = str(s.get("excerpt") or "").strip()
                    out.append(f"  - `{source_id}` — `{anchor}`")
                    if excerpt:
                        out.append(f"    - Trecho: {excerpt}")

            if it.get("gap_priority") and it.get("recommendation"):
                out.append(
                    f"- **Gap:** `{it.get('gap_priority')}` — {it.get('recommendation')}"
                )

            notes = str(it.get("notes") or "").strip()
            if notes:
                out.append(f"- **Notas:** {notes}")

            out.append("")
        return "\n".join(out).rstrip()

    firac = rel.get("firac", {}) if isinstance(rel.get("firac"), dict) else {}
    normative_basis = rel.get("normative_basis", [])
    gaps = rel.get("gaps", [])
    trunc = rel.get("truncation", {}) if isinstance(rel.get("truncation"), dict) else {}
    meta = rel.get("meta", {}) if isinstance(rel.get("meta"), dict) else {}

    md = [
        f"# {title}",
        f"- **Case ID:** {case_id}" if case_id else "",
        f"- **Partes:** {', '.join(map(str, parties))}" if parties else "",
        "",
        sec("Fatos", firac.get("facts")),
        "",
        sec("Issues", firac.get("issues")),
        "",
        sec("Base normativa (Law Pack)", normative_basis),
        "",
        sec("Rules", firac.get("rules")),
        "",
        sec("Analysis", firac.get("analysis")),
        "",
        sec("Conclusion", firac.get("conclusion")),
        "",
        "## Lacunas (Gaps)",
    ]

    if isinstance(gaps, list) and gaps:
        for g in gaps:
            if not isinstance(g, dict):
                continue
            md.append(
                f"- **{g.get('id')}** — `{g.get('priority')}` — {g.get('description')}"
            )
            md.append(f"  - Recomendação: {g.get('recommendation')}")
    else:
        md.append("_Sem lacunas._")

    md.append("")
    md.append("## Meta / QA")
    md.append(f"- **Gerado em:** {meta.get('generated_at', '')}")
    md.append(f"- **Gerado por:** {meta.get('generated_by', '')}")
    if meta.get("inputs_used"):
        md.append(
            f"- **Inputs usados:** {', '.join(map(str, meta.get('inputs_used') or []))}"
        )
    if meta.get("warnings"):
        md.append("- **Warnings:**")
        for w in meta.get("warnings", []):
            md.append(f"  - {w}")
    if trunc:
        md.append(f"- **Truncado:** {bool(trunc.get('was_truncated'))}")
        dropped = trunc.get("dropped_counts")
        if isinstance(dropped, dict):
            md.append(f"- **Drops:** {json.dumps(dropped, ensure_ascii=False)}")

    return "\n".join([x for x in md if x != ""])


def _build_prompt(
    prompt_template: str,
    processo: Dict[str, Any],
    evidence: Optional[Dict[str, Any]],
    law_pack: Optional[Dict[str, Any]],
    mode: str,
    budgets: Dict[str, int],
) -> str:
    # Regras duras: JSON puro, sem markdown.
    hard_rules = f"""
Você é o agente firac-cli. Gere APENAS um objeto JSON válido (sem markdown, sem comentários), no schema "relatorio_firac" (v1.0).

Regras:
- FIRAC-Core deve funcionar apenas com PROCESSO.
- Se evidence existir e mode=firac_plus, incorpore apenas o que estiver ancorado (supports com source_id+anchor).
- Se law_pack existir, use-o como base normativa (artigos/trechos) e cite SEMPRE com supports (source_id + anchor).
- NÃO invente fatos. Sem suporte -> epistemic_status=premise ou gap.
- Para epistemic_status=evidence ou inference: supports obrigatório (>=1).
- Para epistemic_status=gap: gap_priority (P0-P3) e recommendation obrigatórios.
- Se houver conflito de época/lei aplicável e não for possível resolver com prova/ancoragem, registre GAP P0 pedindo confirmação/critério de vigência.
- Seja conciso: cada statement <= 600 caracteres. Não cole artigos longos; resuma e cite.
- Orçamento (máximo de itens):
  facts={budgets["facts"]}, issues={budgets["issues"]}, rules={budgets["rules"]}, analysis={budgets["analysis"]}, conclusion={budgets["conclusion"]}, gaps={budgets["gaps"]}.
- Se exceder orçamento, marque truncation.was_truncated=true e informe dropped_counts por seção.
"""

    ctx = {
        "mode": mode,
        "processo": processo,
        "evidence": evidence,
        "law_pack": law_pack,  # já comprimido
    }

    if "{HARD_RULES}" in prompt_template or "{CONTEXT_JSON}" in prompt_template:
        return (
            prompt_template.replace("{HARD_RULES}", hard_rules.strip())
            .replace("{CONTEXT_JSON}", json.dumps(ctx, ensure_ascii=False))
            .strip()
        )

    return (
        prompt_template.strip()
        + "\n\n"
        + hard_rules.strip()
        + "\n\nCONTEXT_JSON:\n"
        + json.dumps(ctx, ensure_ascii=False)
    ).strip()


def _genai_client(
    vertexai: bool,
    project: Optional[str],
    location: Optional[str],
    api_version: Optional[str],
) -> genai.Client:
    http_options = None
    if api_version:
        http_options = types.HttpOptions(api_version=api_version)

    if vertexai:
        if not project or not location:
            raise typer.BadParameter(
                "Para vertexai=true, informe --project e --location."
            )
        return genai.Client(
            vertexai=True, project=project, location=location, http_options=http_options
        )

    return genai.Client(http_options=http_options)


def _call_model_json(
    client: genai.Client,
    model: str,
    prompt: str,
    temperature: float,
    max_output_tokens: int,
) -> Dict[str, Any]:
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    text = (resp.text or "").strip()
    if not text:
        raise RuntimeError("Resposta vazia do modelo.")

    try:
        return _extract_first_complete_json_object(text)
    except Exception as e:
        raise RuntimeError(
            f"Falha ao parsear JSON da resposta do modelo (possível truncamento/JSON inválido): {e}"
        ) from e


def _post_validate_and_fix(
    rel: Dict[str, Any], inputs_used: list[str]
) -> Dict[str, Any]:
    warnings: list[str] = []

    if rel.get("schema_version") != "1.0":
        rel["schema_version"] = "1.0"
        warnings.append("schema_version ajustado para 1.0.")

    if "meta" not in rel or not isinstance(rel["meta"], dict):
        rel["meta"] = {}
    rel["meta"].setdefault("generated_by", "firac-cli")
    rel["meta"].setdefault("generated_at", _utc_now_iso())
    rel["meta"]["inputs_used"] = inputs_used
    if warnings:
        rel["meta"].setdefault("warnings", [])
        if isinstance(rel["meta"]["warnings"], list):
            rel["meta"]["warnings"].extend(warnings)

    if "truncation" not in rel or not isinstance(rel["truncation"], dict):
        rel["truncation"] = {
            "was_truncated": False,
            "budgets": {
                "facts": 0,
                "issues": 0,
                "rules": 0,
                "analysis": 0,
                "conclusion": 0,
                "gaps": 0,
            },
            "dropped_counts": {
                "facts": 0,
                "issues": 0,
                "rules": 0,
                "analysis": 0,
                "conclusion": 0,
                "gaps": 0,
            },
        }

    # evidence/inference exige supports>=1; se violar, rebaixar para premise.
    firac = rel.get("firac")
    if isinstance(firac, dict):
        for sec_name in ["facts", "issues", "rules", "analysis", "conclusion"]:
            items = firac.get(sec_name)
            if not isinstance(items, list):
                continue
            for it in items:
                if not isinstance(it, dict):
                    continue
                st = it.get("epistemic_status")
                supports = it.get("supports")
                if st in ("evidence", "inference"):
                    if not isinstance(supports, list) or len(supports) == 0:
                        it["epistemic_status"] = "premise"
                        it.pop("supports", None)
                        warnings.append(
                            f"{sec_name}:{it.get('id', '?')} rebaixado para premise por falta de supports."
                        )
                if st == "gap":
                    if not it.get("gap_priority"):
                        it["gap_priority"] = "P1"
                    if not it.get("recommendation"):
                        it["recommendation"] = (
                            "Colher evidência/documento que suporte esta afirmação e ancorar (source_id/anchor)."
                        )

    gaps = rel.get("gaps")
    if isinstance(gaps, list):
        for g in gaps:
            if not isinstance(g, dict):
                continue
            g.setdefault("priority", "P1")
            g.setdefault(
                "recommendation",
                "Colher evidência/documento e registrar com source_id/anchor.",
            )

    if warnings:
        rel["meta"].setdefault("warnings", [])
        if isinstance(rel["meta"]["warnings"], list):
            rel["meta"]["warnings"].extend(warnings)

    return rel


@app.command()
def run(
    processo_path: Path = typer.Option(
        DEFAULT_PROCESSO_PATH, "--processo", exists=True, readable=True
    ),
    evidence_path: Optional[Path] = typer.Option(None, "--evidence", readable=True),
    law_pack_path: Optional[Path] = typer.Option(None, "--law-pack", readable=True),
    out_json: Path = typer.Option(DEFAULT_OUT_JSON, "--out-json"),
    out_md: Path = typer.Option(DEFAULT_OUT_MD, "--out-md"),
    mode: Optional[str] = typer.Option(
        None, "--mode", help="firac_core | firac_plus (se omitido, auto)"
    ),
    model: str = typer.Option("gemini-2.5-flash", "--model"),
    temperature: float = typer.Option(0.2, "--temperature"),
    max_output_tokens: int = typer.Option(4096, "--max-output-tokens"),
    config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, "--config"),
    prompt_path: Path = typer.Option(DEFAULT_PROMPT_PATH, "--prompt"),
    vertexai: bool = typer.Option(False, "--vertexai"),
    project: Optional[str] = typer.Option(None, "--project"),
    location: Optional[str] = typer.Option(None, "--location"),
    api_version: Optional[str] = typer.Option(None, "--api-version"),
) -> None:
    cfg = _load_yaml_config(config_path)

    # --- runtime / provider ---
    model = str(_cfg_get(cfg, "runtime.model", _cfg_get(cfg, "model", model)))
    temperature = float(
        _cfg_get(cfg, "runtime.temperature", _cfg_get(cfg, "temperature", temperature))
    )
    max_output_tokens = int(
        _cfg_get(
            cfg,
            "runtime.max_output_tokens",
            _cfg_get(cfg, "max_output_tokens", max_output_tokens),
        )
    )

    # --- budgets ---
    budgets_cfg = _cfg_get(cfg, "runtime.budgets", {})
    if not isinstance(budgets_cfg, dict):
        budgets_cfg = {}

    budgets = {
        "facts": int(budgets_cfg.get("facts", _cfg_get(cfg, "budget_facts", 25))),
        "issues": int(budgets_cfg.get("issues", _cfg_get(cfg, "budget_issues", 12))),
        "rules": int(budgets_cfg.get("rules", _cfg_get(cfg, "budget_rules", 18))),
        "analysis": int(
            budgets_cfg.get("analysis", _cfg_get(cfg, "budget_analysis", 25))
        ),
        "conclusion": int(
            budgets_cfg.get("conclusion", _cfg_get(cfg, "budget_conclusion", 10))
        ),
        "gaps": int(budgets_cfg.get("gaps", _cfg_get(cfg, "budget_gaps", 15))),
        "law_pack": int(
            budgets_cfg.get("law_pack", _cfg_get(cfg, "budget_law_pack", 25))
        ),
    }

    # --- paths (opcional) ---
    prompt_path_cfg = _cfg_get(cfg, "paths.prompt_file", None)
    if isinstance(prompt_path_cfg, str) and prompt_path_cfg.strip():
        prompt_path = Path(prompt_path_cfg)

    strip_prompt_fm = bool(
        _cfg_get(cfg, "front_matter.strip_before_send_to_model", True)
    )

    prompt_template = (
        _read_text(prompt_path, strip_frontmatter=strip_prompt_fm)
        if prompt_path.exists()
        else "{HARD_RULES}\n\nUse o CONTEXT_JSON para gerar o relatorio_firac.\n\n{CONTEXT_JSON}"
    )

    processo_raw = _read_json(processo_path)
    processo = (
        processo_raw if isinstance(processo_raw, dict) else {"_raw": processo_raw}
    )

    # Evidence (opcional, sem bloquear)
    evidence: Optional[Dict[str, Any]] = None
    chosen_evidence_path: Optional[Path] = evidence_path
    if chosen_evidence_path is None and DEFAULT_EVIDENCE_PATH.exists():
        chosen_evidence_path = DEFAULT_EVIDENCE_PATH
    if chosen_evidence_path and chosen_evidence_path.exists():
        try:
            ev = _read_json(chosen_evidence_path)
            evidence = ev if isinstance(ev, dict) else {"_raw": ev}
        except Exception:
            evidence = None

    # Law pack (saída do law-cli) (opcional, sem bloquear)
    law_pack_ctx: Optional[Dict[str, Any]] = None
    chosen_law_pack_path: Optional[Path] = law_pack_path
    if chosen_law_pack_path is None and DEFAULT_LAW_PACK_PATH.exists():
        chosen_law_pack_path = DEFAULT_LAW_PACK_PATH
    if chosen_law_pack_path and chosen_law_pack_path.exists():
        try:
            lp = _read_json(chosen_law_pack_path)
            lp_dict = lp if isinstance(lp, dict) else {"_raw": lp}
            law_pack_ctx = _compress_law_pack(lp_dict, top_n=budgets["law_pack"])
        except Exception:
            law_pack_ctx = None

    auto_mode = "firac_plus" if evidence is not None else "firac_core"
    mode_final = (
        mode.strip().lower() if isinstance(mode, str) and mode.strip() else auto_mode
    )
    if mode_final not in ("firac_core", "firac_plus"):
        raise typer.BadParameter("mode inválido. Use firac_core ou firac_plus.")

    inputs_used = ["processo:consolidado_v1"]
    if evidence is not None and mode_final == "firac_plus":
        inputs_used.append("cad_obr:evidence_out_v1")
    if law_pack_ctx is not None:
        inputs_used.append("legal:law_pack_v1")

    prompt = _build_prompt(
        prompt_template=prompt_template,
        processo=processo,
        evidence=evidence,
        law_pack=law_pack_ctx,
        mode=mode_final,
        budgets=budgets,
    )

    client = _genai_client(
        vertexai=vertexai, project=project, location=location, api_version=api_version
    )
    try:
        rel = _call_model_json(
            client=client,
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
    finally:
        try:
            client.close()
        except Exception:
            pass

    rel = _post_validate_and_fix(rel, inputs_used=inputs_used)

    # Enriquecimento determinístico: base normativa (não depende do LLM)
    if law_pack_ctx is not None and "normative_basis" not in rel:
        rel["normative_basis"] = _normative_basis_items(law_pack_ctx)

    _write_json(out_json, rel)
    _write_text(out_md, _render_md(rel))

    typer.echo(f"OK: {out_json}")
    typer.echo(f"OK: {out_md}")


@app.command()
def build(
    processo_path: Path = typer.Option(
        DEFAULT_PROCESSO_PATH, "--processo", exists=True, readable=True
    ),
    evidence_path: Optional[Path] = typer.Option(None, "--evidence", readable=True),
    law_pack_path: Optional[Path] = typer.Option(None, "--law-pack", readable=True),
    out_json: Path = typer.Option(DEFAULT_OUT_JSON, "--out-json"),
    out_md: Path = typer.Option(DEFAULT_OUT_MD, "--out-md"),
    mode: Optional[str] = typer.Option(None, "--mode"),
    model: str = typer.Option("gemini-2.5-flash", "--model"),
    temperature: float = typer.Option(0.2, "--temperature"),
    max_output_tokens: int = typer.Option(4096, "--max-output-tokens"),
    config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, "--config"),
    prompt_path: Path = typer.Option(DEFAULT_PROMPT_PATH, "--prompt"),
    vertexai: bool = typer.Option(False, "--vertexai"),
    project: Optional[str] = typer.Option(None, "--project"),
    location: Optional[str] = typer.Option(None, "--location"),
    api_version: Optional[str] = typer.Option(None, "--api-version"),
) -> None:
    run(
        processo_path=processo_path,
        evidence_path=evidence_path,
        law_pack_path=law_pack_path,
        out_json=out_json,
        out_md=out_md,
        mode=mode,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        config_path=config_path,
        prompt_path=prompt_path,
        vertexai=vertexai,
        project=project,
        location=location,
        api_version=api_version,
    )


if __name__ == "__main__":
    app()
