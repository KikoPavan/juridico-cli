from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
import yaml

app = typer.Typer(
    add_completion=False,
    help="law-cli — gera law_pack_v1.json consultando leis no Qdrant (via index_library_qdrant.py)",
)

AGENT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = AGENT_DIR / "config.yaml"

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


def _load_project_cfg() -> dict:
    if yaml is None or not DEFAULT_CONFIG_PATH.exists():
        return {}
    data = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    return data if isinstance(data, dict) else {}


def _cfg_get(cfg: dict, *keys, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return default if cur is None else cur


DATE_RE_1 = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
DATE_RE_2 = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


@dataclass
class Config:
    agent_name: str
    agent_version: str
    script: str
    doc_kind: str
    top_k: int
    out_path: str


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(root: Path) -> Config:
    """
    Compat:
      - Formato antigo:
          agent_name, agent_version, index_query: {script, doc_kind, top_k}, (out_path opcional)
      - Formato novo (padrão do projeto):
          agent: {name, version}, paths: {output_file}, jobs: [{script, doc_kind, top_k, ...}]
    """
    p = root / "agents" / "law-cli" / "config.yaml"
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config.yaml inválido: esperado mapeamento YAML no topo.")

    def _pick_out_path(d: dict) -> Path:
        # novo padrão: paths.output_file
        paths = d.get("paths") or {}
        if isinstance(paths, dict):
            of = paths.get("output_file") or paths.get("out_path")
            if of:
                return Path(str(of))
        # legado: out_path no topo (se existir)
        op = d.get("out_path") or d.get("output_file")
        if op:
            return Path(str(op))
        return Path("outputs/legal/law_pack_v1.json")

    out_path = _pick_out_path(raw)

    # --- Formato antigo (legado) ---
    if "agent_name" in raw:
        iq = raw.get("index_query") or {}
        if not isinstance(iq, dict):
            iq = {}
        script = iq.get("script")
        if not script:
            raise KeyError(
                "index_query.script ausente no config.yaml (formato antigo)."
            )
        return Config(
            agent_name=str(raw["agent_name"]),
            agent_version=str(raw.get("agent_version", "0.0.0")),
            script=str(script),
            doc_kind=str(iq.get("doc_kind", "lei")),
            top_k=int(iq.get("top_k", 10)),
            out_path=out_path,
        )

    # --- Formato novo (padrão do projeto) ---
    agent_block = raw.get("agent") or {}
    if not isinstance(agent_block, dict):
        agent_block = {}

    jobs = raw.get("jobs") or []
    job0 = (
        jobs[0] if isinstance(jobs, list) and jobs and isinstance(jobs[0], dict) else {}
    )

    script = job0.get("script")
    if not script:
        # fallback: caso alguém ainda tenha "index_query" junto do formato novo
        iq = raw.get("index_query") or {}
        script = iq.get("script") if isinstance(iq, dict) else None
    if not script:
        raise KeyError(
            "script ausente no config.yaml (jobs[0].script ou index_query.script)."
        )

    doc_kind = job0.get("doc_kind", "lei")
    top_k = int(job0.get("top_k", 10))

    return Config(
        agent_name=str(agent_block.get("name") or "law-cli"),
        agent_version=str(agent_block.get("version") or "0.0.0"),
        script=str(script),
        doc_kind=str(doc_kind),
        top_k=top_k,
        out_path=out_path,
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def flatten_strings(obj: Any, limit_chars: int = 180_000) -> str:
    parts: List[str] = []

    def walk(x: Any) -> None:
        if len(" ".join(parts)) >= limit_chars:
            return
        if isinstance(x, str):
            s = x.strip()
            if s:
                parts.append(s)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return (" ".join(parts))[:limit_chars]


def pick_effective_date(text: str) -> Optional[date]:
    keywords = [
        "escritura",
        "contrato",
        "hipoteca",
        "assinatura",
        "registro",
        "procura",
        "lavrada",
        "outorg",
    ]
    window = 160
    candidates: List[Tuple[int, date]] = []

    def add(idx: int, dt: date, ctx: str) -> None:
        score = sum(1 for k in keywords if k in ctx)
        candidates.append((-(score * 10) + idx, dt))

    for m in DATE_RE_1.finditer(text):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = date(y, mo, d)
        except ValueError:
            continue
        idx = m.start()
        ctx = text[max(0, idx - window) : idx + window].lower()
        add(idx, dt, ctx)

    for m in DATE_RE_2.finditer(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = date(y, mo, d)
        except ValueError:
            continue
        idx = m.start()
        ctx = text[max(0, idx - window) : idx + window].lower()
        add(idx, dt, ctx)

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def build_queries(process_text: str) -> Tuple[List[str], List[str]]:
    t = process_text.lower()
    topics: List[str] = []

    def has(s: str) -> bool:
        return s in t

    if has("hipoteca"):
        topics.append("hipoteca")
    if has("escritura"):
        topics.append("escritura pública")
    if has("procura"):
        topics.append("procuração poderes representação")
    if has("contrato social"):
        topics.append("contrato social limitação de poderes")
    if has("nul"):
        topics.append("nulidade")
    if has("anul"):
        topics.append("anulabilidade")
    if has("prescri") or has("decad"):
        topics.append("prescrição decadência")

    queries = [
        "nulidade ato jurídico escritura pública hipoteca requisitos",
        "anulabilidade ato jurídico vícios poderes procuração representação",
        "procuração poderes insuficientes sociedade limitação atos não administrativos",
        "garantia hipotecária validade requisitos formais registro",
        "prazo prescricional decadência ação anulatória nulidade ato jurídico cobrança",
    ]
    if topics:
        queries.append(" ".join(topics))

    out: List[str] = []
    seen = set()
    for q in queries:
        qn = " ".join(q.split())
        if qn not in seen:
            seen.add(qn)
            out.append(qn)
    return out, topics


def extract_json_array(stdout: str) -> List[Dict[str, Any]]:
    i = stdout.find("[")
    j = stdout.rfind("]")
    if i == -1 or j == -1 or j <= i:
        raise RuntimeError(
            "Não encontrei JSON array no stdout do index_library_qdrant.py"
        )
    return json.loads(stdout[i : j + 1])


def run_query(
    root: Path, script: str, doc_kind: str, query: str, top_k: int
) -> List[Dict[str, Any]]:
    cmd = [
        "python",
        str(root / script),
        "query",
        "--doc-kind",
        doc_kind,
        "--query",
        query,
        "--top-k",
        str(top_k),
    ]
    p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            f"Falha no query (rc={p.returncode}): {p.stderr.strip() or p.stdout.strip()}"
        )
    return extract_json_array(p.stdout)


def resolve_chunk_text(
    root: Path, path_rag: str, anchor: str
) -> Tuple[Dict[str, Any], str]:
    rag_path = root / path_rag
    obj = json.loads(rag_path.read_text(encoding="utf-8"))
    chunks = obj.get("chunks", [])
    if not isinstance(chunks, list) or not chunks:
        raise RuntimeError(f"Arquivo rag sem chunks: {path_rag}")

    m = re.match(r"^chunk:(\d+)$", anchor.strip())
    if not m:
        raise RuntimeError(f"Anchor inesperado: {anchor} (esperado chunk:N)")

    n = int(m.group(1))

    # Regra confirmada no seu projeto: chunk:N => índice N
    idx: Optional[int] = None
    if 0 <= n < len(chunks):
        idx = n
    elif 0 <= (n - 1) < len(chunks):
        idx = n - 1

    if idx is None:
        raise RuntimeError(
            f"Índice fora do range: {anchor} len(chunks)={len(chunks)} rag={path_rag}"
        )

    ch = chunks[idx]
    if not isinstance(ch, dict):
        raise RuntimeError(f"Chunk inválido em idx={idx} rag={path_rag}")

    text = ch.get("text") if isinstance(ch.get("text"), str) else ""
    return ch, text


def build_impl(
    processo: Path,
    juntadas: List[Path],
    effective_date: Optional[str],
    out: Optional[Path],
    top_k: Optional[int],
) -> Path:
    root = repo_root_from_here()
    cfg = load_config(root)

    proc_obj = json.loads(processo.read_text(encoding="utf-8"))
    proc_text = flatten_strings(proc_obj)

    junt_texts: List[str] = []
    for jp in juntadas:
        j_obj = json.loads(jp.read_text(encoding="utf-8"))
        junt_texts.append(flatten_strings(j_obj, limit_chars=80_000))

    combined_text = proc_text + "\n" + ("\n".join(junt_texts) if junt_texts else "")

    eff: Optional[date] = None
    if effective_date:
        eff = date.fromisoformat(effective_date)
    else:
        # prioridade: juntadas (procuração/escritura costuma estar ali), depois processo
        if junt_texts:
            eff = pick_effective_date("\n".join(junt_texts))
        if eff is None:
            eff = pick_effective_date(proc_text)

    queries, topics = build_queries(combined_text)

    hits_all: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []

    use_top_k = int(top_k) if top_k else cfg.top_k

    for q in queries:
        try:
            hits_all.extend(run_query(root, cfg.script, cfg.doc_kind, q, use_top_k))
        except Exception as e:
            errors.append(f"query='{q}': {e}")
            break

    best: Dict[str, Dict[str, Any]] = {}
    for h in hits_all:
        source_id = h.get("source_id") or h.get("doc_id") or "unknown"
        anchor = h.get("anchor") or ""
        path_rag = h.get("path_rag") or ""
        score = float(h.get("score") or 0.0)

        if not anchor or not path_rag:
            continue

        key = f"{source_id}|{anchor}"
        if key in best and score <= float(best[key]["score"]):
            continue

        try:
            ch, txt = resolve_chunk_text(root, path_rag, anchor)
        except Exception as e:
            warnings.append(f"{key}: não consegui extrair texto ({e})")
            continue

        article_no = ch.get("article_no")
        heading = ch.get("heading_canonical") or ""
        title = (
            f"Art. {article_no} — {heading}".strip(" —")
            if article_no
            else (heading or source_id)
        )

        excerpt = (txt or "")[:900]
        rule = {
            "id": f"{source_id}:{anchor}",
            "title": title,
            "citation": h.get("doc_id") or source_id,
            "text": txt or excerpt,
            "score": score,
            "support": [
                {
                    "source_id": source_id,
                    "anchor": anchor,
                    "excerpt": excerpt,
                    "locator": {
                        "path_rag": path_rag,
                        "page_ref": ch.get("page_ref"),
                        "chunk_id": ch.get("chunk_id"),
                        "section_id": ch.get("section_id"),
                    },
                }
            ],
            "meta": {
                "doc_id": h.get("doc_id"),
                "sha256": h.get("sha256"),
                "article_no": article_no,
                "hierarchy": ch.get("hierarchy"),
            },
        }
        best[key] = rule

    rules = sorted(best.values(), key=lambda x: float(x["score"]), reverse=True)

    gaps = []
    if eff is None:
        gaps.append(
            {
                "id": "G001",
                "priority": "P0",
                "text": "effective_date não encontrada no PROCESSO/JUNTADAS. Informe --effective-date para recorte temporal (vigência/prazos).",
            }
        )
    gaps.append(
        {
            "id": "G010",
            "priority": "P1",
            "text": "Vigência (valid_from/valid_to) não está no payload do Qdrant; law-cli não consegue filtrar automaticamente por lei vigente. Recomenda-se incluir vigência na indexação.",
        }
    )

    if not rules and not errors:
        warnings.append(
            "Nenhuma regra foi montada. Verifique hits do query e path_rag/anchor."
        )

    now = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    job_id = os.environ.get("JOB_ID", "job_law_cli")
    run_id = os.environ.get(
        "RUN_ID", f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    )

    out_path = out or (root / cfg.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    inputs = {
        "processo": {"path": str(processo), "sha256": sha256_file(processo)},
        "juntadas": [{"path": str(jp), "sha256": sha256_file(jp)} for jp in juntadas],
        "index_query": {
            "script": cfg.script,
            "doc_kind": cfg.doc_kind,
            "top_k": use_top_k,
        },
    }

    envelope = {
        "agent_name": cfg.agent_name,
        "agent_version": cfg.agent_version,
        "job_id": job_id,
        "run_id": run_id,
        "created_at": now,
        "status": "failed" if errors else ("partial" if warnings else "ok"),
        "inputs": inputs,
        "warnings": warnings,
        "errors": errors,
        "payload": {
            "schema_version": "law_pack_v1",
            "effective_date": eff.isoformat() if eff else None,
            "effective_date_evidence": None,
            "queries": queries,
            "topics": topics,
            "rules": rules[:200],
            "gaps": gaps,
        },
    }

    out_path.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    processo: Optional[Path] = typer.Option(
        None, "--processo", exists=True, file_okay=True, dir_okay=False
    ),
    juntada: List[Path] = typer.Option(
        [], "--juntada", exists=True, file_okay=True, dir_okay=False
    ),
    effective_date: Optional[str] = typer.Option(
        None, "--effective-date", help="YYYY-MM-DD"
    ),
    out: Optional[Path] = typer.Option(None, "--out"),
    top_k: Optional[int] = typer.Option(None, "--top-k"),
):
    if ctx.invoked_subcommand is None:
        if processo is None:
            raise typer.BadParameter("Informe --processo.")
        out_path = build_impl(processo, juntada, effective_date, out, top_k)
        typer.echo(str(out_path))


@app.command("build")
def build_cmd(
    processo: Path = typer.Option(
        ..., "--processo", exists=True, file_okay=True, dir_okay=False
    ),
    juntada: List[Path] = typer.Option(
        [], "--juntada", exists=True, file_okay=True, dir_okay=False
    ),
    effective_date: Optional[str] = typer.Option(
        None, "--effective-date", help="YYYY-MM-DD"
    ),
    out: Optional[Path] = typer.Option(None, "--out"),
    top_k: Optional[int] = typer.Option(None, "--top-k"),
):
    cfg = _load_project_cfg()
    if out is None:
        out = Path(
            _cfg_get(
                cfg, "jobs", "build", "out", default="outputs/legal/law_pack_v1.json"
            )
        )
    if top_k is None:
        top_k = int(_cfg_get(cfg, "jobs", "build", "top_k", default=10))

    out_path = build_impl(processo, juntada, effective_date, out, top_k)
    typer.echo(str(out_path))


# Alias de compatibilidade: permite `law-cli run` (padrão dos outros agentes)
app.command("run")(build_cmd)
if __name__ == "__main__":
    app()
