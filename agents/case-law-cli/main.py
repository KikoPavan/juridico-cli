# agents/case-law-cli/main.py
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
import yaml
from dotenv import load_dotenv

# --- NOVA SDK GOOGLE GENAI (google-genai) ---
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERRO CRÍTICO: Biblioteca 'google-genai' não instalada.")
    print("Instale com: uv add google-genai python-dotenv")
    raise

# --- QDRANT + EMBEDDINGS ---
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm
except ImportError:
    print("ERRO CRÍTICO: Biblioteca 'qdrant-client' não instalada.")
    print("Instale com: uv add qdrant-client")
    raise

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERRO CRÍTICO: Biblioteca 'sentence-transformers' não instalada.")
    print("Instale com: uv add sentence-transformers")
    raise


app = typer.Typer(add_completion=False)

DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "legal_library_chunks_v1")
DEFAULT_EMBED_MODEL = os.getenv(
    "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

DEFAULT_TOP_K = 8
DEFAULT_SELECT_PER_THESIS = 3


@dataclass
class Candidate:
    thesis: str
    score: float
    payload: Dict[str, Any]
    meta: Dict[str, Any]
    chunk_text: str


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_project_root() -> Path:
    # agents/case-law-cli/main.py -> agents/ -> repo root
    return Path(__file__).resolve().parents[2]


def resolve_path(project_root: Path, p: str) -> Path:
    pp = Path(p)
    return pp if pp.is_absolute() else (project_root / pp).resolve()


def ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _safe_json_parse(text: str) -> Optional[Any]:
    try:
        return json.loads(_strip_code_fences(text))
    except Exception:
        return None


def _get_api_key() -> str:
    for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        v = os.getenv(k)
        if v:
            return v
    raise RuntimeError(
        "API key não encontrada. Defina GEMINI_API_KEY ou GOOGLE_API_KEY no .env."
    )


def gemini_json(
    model: str,
    prompt: str,
    temperature: float,
    max_output_tokens: int,
) -> Dict[str, Any]:
    client = genai.Client(api_key=_get_api_key())
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
        ),
    )
    parsed = _safe_json_parse(getattr(resp, "text", "") or "")
    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Gemini retornou JSON inválido para response_mime_type=application/json."
        )
    return parsed


def load_firac_json(project_root: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    paths = config.get("paths") or {}
    raw = (
        paths.get("input_relatorio_firac_json")
        or paths.get("input_file")
        or paths.get("input_relatorio_firac")
        or "outputs/relatorio_firac.json"
    )
    p = resolve_path(project_root, str(raw))

    if p.suffix.lower() == ".md":
        alt = p.with_suffix(".json")
        if alt.exists():
            p = alt

    if not p.exists():
        raise FileNotFoundError(f"FIRAC não encontrado: {p}")

    if p.suffix.lower() != ".json":
        raise RuntimeError(
            f"FIRAC precisa ser JSON para extração determinística. Caminho atual: {p} "
            f"(use outputs/relatorio_firac.json)."
        )

    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_theses_from_firac(firac: Dict[str, Any]) -> List[str]:
    """
    Extrai 'teses/questões nucleares' do FIRAC de forma robusta.
    Prioriza listas em firac['issues'], mas também faz varredura recursiva por chaves prováveis.
    """
    KEY_HINTS = (
        "tese",
        "thesis",
        "questao",
        "questão",
        "questoes",
        "questões",
        "issue",
        "nuclear",
        "nucleo",
        "nucleares",
        "pergunta",
        "problema",
    )

    def norm(s: str) -> str:
        s = s.strip()
        s = re.sub(r"^\s*[\-\*\d\.\)\]]+\s*", "", s)  # remove "- ", "1) ", "1. "
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def add_candidate(acc: List[str], s: Any) -> None:
        if not isinstance(s, str):
            return
        t = norm(s)
        if not t:
            return
        if len(t) < 10 or len(t) > 280:
            return
        acc.append(t)

    def from_obj(acc: List[str], obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = str(k).lower()
                if any(h in kl for h in KEY_HINTS):
                    if isinstance(v, str):
                        add_candidate(acc, v)
                    elif isinstance(v, list):
                        for it in v:
                            add_candidate(acc, it)
                    elif isinstance(v, dict):
                        for vv in v.values():
                            add_candidate(acc, vv)
                from_obj(acc, v)
        elif isinstance(obj, list):
            for it in obj:
                from_obj(acc, it)

    out: List[str] = []

    issues = firac.get("issues")
    if isinstance(issues, list):
        for it in issues:
            if isinstance(it, str):
                add_candidate(out, it)
            elif isinstance(it, dict):
                for k in (
                    "thesis",
                    "tese",
                    "tese_nuclear",
                    "questao_nuclear",
                    "questão_nuclear",
                    "question",
                    "issue",
                    "title",
                    "name",
                    "summary",
                    "descricao",
                    "descrição",
                ):
                    if k in it:
                        v = it.get(k)
                        if isinstance(v, str):
                            add_candidate(out, v)
                        elif isinstance(v, list):
                            for s in v:
                                add_candidate(out, s)

    if not out:
        from_obj(out, firac)

    seen = set()
    deduped: List[str] = []
    for t in out:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(t)

    return deduped


def extract_case_context(firac: Dict[str, Any]) -> str:
    s = firac.get("summary")
    if isinstance(s, str) and s.strip():
        return s.strip()
    if isinstance(s, dict):
        parts = []
        for v in s.values():
            if isinstance(v, str) and v.strip():
                parts.append(v.strip())
        if parts:
            return "\n".join(parts)
    case_id = firac.get("case_id")
    return f"case_id: {case_id}" if case_id else ""


def build_qdrant_filter(doc_kind: str, court: Optional[str]) -> qm.Filter:
    must: List[qm.FieldCondition] = [
        qm.FieldCondition(key="doc_kind", match=qm.MatchValue(value=doc_kind)),
    ]
    if court:
        must.append(qm.FieldCondition(key="court", match=qm.MatchValue(value=court)))
    return qm.Filter(must=must)


def infer_single_court_for_jurisprudencia(
    client: QdrantClient, collection: str
) -> Optional[str]:
    try:
        points, _ = client.scroll(
            collection_name=collection,
            limit=20,
            with_payload=True,
            with_vectors=False,
            scroll_filter=build_qdrant_filter("jurisprudencia", None),
        )
    except TypeError:
        points, _ = client.scroll(
            collection_name=collection,
            limit=20,
            with_payload=True,
            with_vectors=False,
            filter=build_qdrant_filter("jurisprudencia", None),
        )

    courts = set()
    for p in points or []:
        payload = getattr(p, "payload", None) or {}
        c = payload.get("court")
        if isinstance(c, str) and c.strip():
            courts.add(c.strip())
    return next(iter(courts)) if len(courts) == 1 else None


def embed_texts(model: SentenceTransformer, texts: List[str]) -> List[List[float]]:
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def qdrant_search(
    client: QdrantClient,
    collection: str,
    query_vector: List[float],
    q_filter: qm.Filter,
    top_k: int,
) -> List[Any]:
    if hasattr(client, "query_points"):
        return client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
            query_filter=q_filter,
        ).points
    return client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
        query_filter=q_filter,
    )


def load_rag_meta_and_chunk(
    project_root: Path, path_rag: str, chunk_index: Optional[int]
) -> Tuple[Dict[str, Any], str]:
    p = resolve_path(project_root, path_rag)
    if not p.exists():
        return {}, ""
    with p.open("r", encoding="utf-8") as f:
        d = json.load(f)
    meta = d.get("meta") or {}

    txt = ""
    chunks = d.get("chunks") or []
    if isinstance(chunk_index, int) and 0 <= chunk_index < len(chunks):
        ch = chunks[chunk_index]
        if isinstance(ch, dict):
            for k in ("text", "content", "chunk"):
                v = ch.get(k)
                if isinstance(v, str) and v.strip():
                    txt = v.strip()
                    break
    if txt and len(txt) > 1200:
        txt = txt[:1200] + "…"
    return meta, txt


def build_citacao_padrao(meta: Dict[str, Any], payload: Dict[str, Any]) -> str:
    tribunal = (payload.get("court") or meta.get("court") or "").strip() or "TRIBUNAL"
    classe = (meta.get("class") or "").strip()
    doc_id = (payload.get("doc_id") or "").strip()
    relator = (meta.get("relator") or "").strip()
    julg = (meta.get("judgment_date") or "").strip()
    src = (meta.get("source_pdf") or payload.get("source_id") or "").strip()

    parts = [tribunal]
    if classe or doc_id:
        parts.append(f"{classe} {doc_id}".strip())
    if relator:
        parts.append(f"Rel. {relator}")
    if julg:
        parts.append(f"Julg. {julg}")
    if src:
        parts.append(str(src))
    return " – ".join(parts)


def llm_enrich_precedentes(
    runtime_cfg: Dict[str, Any],
    theses: List[str],
    case_context: str,
    selected: List[Candidate],
) -> Dict[str, Dict[str, Any]]:
    model = runtime_cfg.get("model", "gemini-2.5-flash")
    temperature = float(runtime_cfg.get("temperature", 0.0))
    max_output_tokens = int(runtime_cfg.get("max_output_tokens", 2048))

    items = []
    for c in selected:
        p = c.payload
        items.append(
            {
                "thesis": c.thesis,
                "doc_id": p.get("doc_id"),
                "court": p.get("court"),
                "class": c.meta.get("class"),
                "relator": c.meta.get("relator"),
                "judgment_date": c.meta.get("judgment_date"),
                "publication_date": c.meta.get("publication_date"),
                "anchor": p.get("anchor"),
                "chunk_text": c.chunk_text,
            }
        )

    prompt = f"""
Você é um assistente jurídico. Sua tarefa é avaliar, para cada item, a aderência do precedente à tese e ao recorte fático.
Responda APENAS em JSON (objeto), com a chave sendo doc_id e o valor contendo:
- "adesao": "alta" | "média" | "baixa"
- "distincao": string curta (pode ser vazia)
- "sintese": string curta (pode ser vazia)

Teses:
{json.dumps(theses, ensure_ascii=False, indent=2)}

Recorte fático (FIRAC summary):
{case_context}

Itens:
{json.dumps(items, ensure_ascii=False, indent=2)}
""".strip()

    return gemini_json(
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def write_outputs(
    md_path: Path,
    json_path: Path,
    theses: List[str],
    precedentes: List[Dict[str, Any]],
    audit: Dict[str, Any],
) -> None:
    ensure_parent_dir(md_path)
    ensure_parent_dir(json_path)

    out_json = {
        "agent": audit.get("agent"),
        "run": audit.get("run"),
        "inputs": audit.get("inputs"),
        "qdrant": audit.get("qdrant"),
        "queries": audit.get("queries"),
        "selection": {"count": len(precedentes), "items": precedentes},
        "generated_at": now_iso(),
    }
    json_path.write_text(
        json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines: List[str] = []
    lines.append("# Jurisprudência selecionada (auditável)\n")

    if theses:
        lines.append("## Teses nucleares (FIRAC)\n")
        for t in theses:
            lines.append(f"- {t}")
        lines.append("")

    by_thesis: Dict[str, List[Dict[str, Any]]] = {}
    for p in precedentes:
        by_thesis.setdefault(p.get("tese_associada") or "—", []).append(p)

    for t, items in by_thesis.items():
        lines.append(f"## Tese: {t}\n")
        for it in items:
            lines.append(f"- **{it.get('citacao_padrao', '')}**")
            if it.get("sintese"):
                lines.append(f"  - Síntese: {it['sintese']}")
            if it.get("distincao"):
                lines.append(f"  - Distinção: {it['distincao']}")
            lines.append(f"  - Adesão: {it.get('adesao', '')}")
            refs = it.get("refs") or {}
            lines.append(
                "  - Ref: "
                f"source_id={refs.get('source_id', '')} | "
                f"anchor={refs.get('anchor', '')} | "
                f"sha256={refs.get('sha256', '')}"
            )
        lines.append("")

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


@app.command()
def run(
    config_path: str = typer.Argument(
        ..., help="Caminho para o config.yaml do case-law-cli"
    ),
) -> None:
    load_dotenv()

    project_root = get_project_root()
    cfg_path = resolve_path(project_root, config_path)
    config = load_config(cfg_path)

    runtime_cfg = config.get("runtime") or {}
    paths_cfg = config.get("paths") or {}
    search_cfg = config.get("search") or {}
    filters_cfg = config.get("filters") or {}

    agent_name = "case-law-cli"
    agent_version = str(config.get("version") or "v1")

    firac = load_firac_json(project_root, config)
    theses = extract_theses_from_firac(firac)

    if not theses:
        raise SystemExit(
            "FIRAC não trouxe teses/questões nucleares. "
            "Verifique outputs/relatorio_firac.json (campo 'issues' e/ou 'matrix')."
        )

    case_context = extract_case_context(firac)

    out_md_raw = (
        paths_cfg.get("output_jurisprudencia")
        or paths_cfg.get("output_file")  # compat antigo
        or "outputs/jurisprudencia/jurisprudencia.md"
    )
    out_json_raw = (
        paths_cfg.get("output_jurisprudencia_json")
        or "outputs/jurisprudencia/jurisprudencia.json"
    )

    out_md = resolve_path(project_root, str(out_md_raw))
    out_json = resolve_path(project_root, str(out_json_raw))

    qdrant_url = str(search_cfg.get("qdrant_url") or DEFAULT_QDRANT_URL)
    collection = str(search_cfg.get("collection") or DEFAULT_COLLECTION)
    top_k = int(search_cfg.get("top_k") or DEFAULT_TOP_K)
    select_per_thesis = int(
        search_cfg.get("select_per_thesis") or DEFAULT_SELECT_PER_THESIS
    )

    court = filters_cfg.get("court")
    if not court:
        client_tmp = QdrantClient(url=qdrant_url, timeout=60)
        court = infer_single_court_for_jurisprudencia(client_tmp, collection)

    q_filter = build_qdrant_filter(doc_kind="jurisprudencia", court=court)

    embed_model_name = str(search_cfg.get("embed_model") or DEFAULT_EMBED_MODEL)
    st_model = SentenceTransformer(embed_model_name, device="cpu")

    client = QdrantClient(url=qdrant_url, timeout=180)

    run_id = str(uuid.uuid4())
    queries_audit: List[Dict[str, Any]] = []

    all_selected: List[Candidate] = []
    for thesis in theses:
        q_text = thesis
        if case_context:
            q_text = f"{thesis}\n\nRecorte fático:\n{case_context}"

        qvec = embed_texts(st_model, [q_text])[0]
        results = qdrant_search(client, collection, qvec, q_filter, top_k=top_k)

        candidates: List[Candidate] = []
        cand_audit_items: List[Dict[str, Any]] = []

        for r in results or []:
            payload = getattr(r, "payload", None) or {}
            score = float(getattr(r, "score", 0.0) or 0.0)

            path_rag = payload.get("path_rag") or ""
            chunk_index = payload.get("chunk_index")
            meta, chunk_text = ({}, "")
            if isinstance(path_rag, str) and path_rag.strip():
                meta, chunk_text = load_rag_meta_and_chunk(
                    project_root,
                    path_rag,
                    chunk_index if isinstance(chunk_index, int) else None,
                )

            candidates.append(
                Candidate(
                    thesis=thesis,
                    score=score,
                    payload=payload,
                    meta=meta,
                    chunk_text=chunk_text,
                )
            )

            cand_audit_items.append(
                {
                    "score": score,
                    "doc_id": payload.get("doc_id"),
                    "source_id": payload.get("source_id"),
                    "sha256": payload.get("sha256"),
                    "anchor": payload.get("anchor"),
                    "chunk_index": payload.get("chunk_index"),
                    "court": payload.get("court"),
                    "path_rag": payload.get("path_rag"),
                }
            )

        queries_audit.append(
            {
                "thesis": thesis,
                "query_text": q_text,
                "filters": {"doc_kind": "jurisprudencia", "court": court},
                "top_k": top_k,
                "candidates": cand_audit_items,
            }
        )

        seen_doc = set()
        picked: List[Candidate] = []
        for c in sorted(candidates, key=lambda x: x.score, reverse=True):
            doc_id = (c.payload.get("doc_id") or "").strip()
            if not doc_id or doc_id in seen_doc:
                continue
            seen_doc.add(doc_id)
            picked.append(c)
            if len(picked) >= select_per_thesis:
                break

        all_selected.extend(picked)

    best_by_doc: Dict[str, Candidate] = {}
    for c in all_selected:
        doc_id = (c.payload.get("doc_id") or "").strip()
        if not doc_id:
            continue
        if (doc_id not in best_by_doc) or (c.score > best_by_doc[doc_id].score):
            best_by_doc[doc_id] = c

    selected = list(best_by_doc.values())

    enrich: Dict[str, Dict[str, Any]] = {}
    if selected and (
        runtime_cfg.get("provider") == "gemini" or not runtime_cfg.get("provider")
    ):
        try:
            enrich = llm_enrich_precedentes(runtime_cfg, theses, case_context, selected)
        except Exception as e:
            enrich = {"__error__": {"message": str(e)}}

    precedentes_out: List[Dict[str, Any]] = []
    for c in selected:
        payload = c.payload
        meta = c.meta
        doc_id = (payload.get("doc_id") or "").strip() or "UNKNOWN_DOC"

        e = enrich.get(doc_id, {}) if isinstance(enrich, dict) else {}
        adesao = e.get("adesao") if isinstance(e, dict) else None
        distincao = e.get("distincao") if isinstance(e, dict) else ""
        sintese = e.get("sintese") if isinstance(e, dict) else ""

        if adesao not in ("alta", "média", "baixa"):
            adesao = "média" if selected else "baixa"

        precedentes_out.append(
            {
                "tese_associada": c.thesis,
                "citacao_padrao": build_citacao_padrao(meta, payload),
                "adesao": adesao,
                "distincao": distincao or "",
                "sintese": sintese or "",
                "score": c.score,
                "refs": {
                    "doc_id": payload.get("doc_id"),
                    "source_id": payload.get("source_id"),
                    "sha256": payload.get("sha256"),
                    "anchor": payload.get("anchor"),
                    "chunk_index": payload.get("chunk_index"),
                    "path_rag": payload.get("path_rag"),
                    "court": payload.get("court"),
                    "dataset": payload.get("dataset"),
                    "meta": {
                        "class": meta.get("class"),
                        "relator": meta.get("relator"),
                        "judgment_date": meta.get("judgment_date"),
                        "publication_date": meta.get("publication_date"),
                        "source_pdf": meta.get("source_pdf"),
                        "document_type": meta.get("document_type"),
                        "doc_subtype": meta.get("doc_subtype"),
                        "language": meta.get("language"),
                    },
                },
            }
        )

    audit = {
        "agent": {"name": agent_name, "version": agent_version},
        "run": {"run_id": run_id, "started_at": now_iso()},
        "inputs": {
            "firac_keys": sorted(list(firac.keys())),
            "theses_count": len(theses),
        },
        "qdrant": {
            "url": qdrant_url,
            "collection": collection,
            "doc_kind": "jurisprudencia",
            "court": court,
            "embed_model": embed_model_name,
        },
        "queries": queries_audit,
    }

    write_outputs(out_md, out_json, theses, precedentes_out, audit)

    print(f"[OK] Gerado: {out_md}")
    print(f"[OK] Gerado: {out_json}")


def main() -> None:
    app()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        sys.exit(1)
