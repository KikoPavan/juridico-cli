#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from sentence_transformers import SentenceTransformer

DEFAULT_COLLECTION = "legal_library_chunks_v1"
DEFAULT_QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
DEFAULT_MODEL = os.environ.get(
    "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


@dataclass(frozen=True)
class Chunk:
    text: str
    anchor: str
    payload: Dict[str, Any]
    point_id: str


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def _stable_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "::".join(parts)))


def _infer_doc_kind_and_court(dataset_name: str) -> Tuple[str, Optional[str]]:
    ds = dataset_name.lower()
    if ds.startswith("bj_juris_"):
        court = ds.replace("bj_juris_", "").upper()
        return "jurisprudencia", court or None
    if ds.startswith("bj_leis"):
        return "lei", None
    if ds.startswith("bj_doutrina"):
        return "doutrina", None
    return "desconhecido", None


def _extract_chunks(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return []
    for k in ("chunks", "segments", "passages", "items"):
        v = obj.get(k)
        if isinstance(v, list):
            return v
    data = obj.get("data")
    if isinstance(data, dict):
        for k in ("chunks", "segments", "passages", "items"):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


def _chunk_text(d: Dict[str, Any]) -> str:
    for k in ("text", "content", "chunk", "passage", "body", "md", "markdown"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    meta = d.get("meta")
    if isinstance(meta, dict):
        v = meta.get("text")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _chunk_anchor(d: Dict[str, Any], fallback: str) -> str:
    for k in ("anchor", "ancora", "ref", "reference"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    meta = d.get("meta")
    if isinstance(meta, dict):
        v = meta.get("anchor")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return fallback


def _load_manifest_map(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    m: Dict[str, Dict[str, Any]] = {}
    if not base_dir.exists():
        return m
    for p in base_dir.rglob("manifesto.yml"):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
            doc_id = data.get("doc_id") or data.get("id") or p.parent.name
            if isinstance(doc_id, str) and doc_id:
                m[doc_id] = data
        except Exception:
            continue
    return m


def _doc_sha256(
    doc_id: str, rag_path: Path, manifest_map: Dict[str, Dict[str, Any]]
) -> Tuple[str, str]:
    manifest = manifest_map.get(doc_id, {})
    source_id = manifest.get("source_id") or manifest.get("source") or doc_id
    sha256 = manifest.get("sha256") or manifest.get("hash_sha256")
    if not sha256 or not isinstance(sha256, str):
        sha256 = _sha256_file(rag_path)
    return str(source_id), str(sha256)


def build_points_from_rag(
    rag_path: Path,
    dataset_name: str,
    manifest_map: Dict[str, Dict[str, Any]],
) -> List[Chunk]:
    doc_id = rag_path.name.replace(".rag.json", "").replace(".json", "")
    doc_kind, court = _infer_doc_kind_and_court(dataset_name)
    source_id, sha256 = _doc_sha256(doc_id, rag_path, manifest_map)

    try:
        obj = json.loads(rag_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []

    chunks_raw = _extract_chunks(obj)
    if not chunks_raw:
        return []

    out: List[Chunk] = []
    for i, cd in enumerate(chunks_raw):
        if not isinstance(cd, dict):
            continue
        text = _chunk_text(cd)
        if not text:
            continue

        anchor = _chunk_anchor(cd, f"chunk:{i}")

        payload: Dict[str, Any] = {
            "dataset": dataset_name,
            "doc_id": doc_id,
            "source_id": source_id,
            "sha256": sha256,
            "anchor": anchor,
            "doc_kind": doc_kind,
            "court": court,
            "path_rag": str(rag_path.as_posix()),
            "chunk_index": i,
        }

        meta = cd.get("meta")
        if isinstance(meta, dict):
            for k in (
                "title",
                "date",
                "tags",
                "ementa",
                "relator",
                "classe",
                "numero_processo",
            ):
                if k in meta and meta[k] is not None:
                    payload[k] = meta[k]

        pid = _stable_id(str(source_id), str(anchor), str(i))
        out.append(Chunk(text=text, anchor=anchor, payload=payload, point_id=pid))
    return out


def ensure_collection(client: QdrantClient, collection: str, vector_size: int) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if collection in existing:
        return
    client.create_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        hnsw_config=qm.HnswConfigDiff(m=16, ef_construct=128),
        optimizers_config=qm.OptimizersConfigDiff(default_segment_number=2),
    )


def batched(it: List[Any], n: int) -> Iterable[List[Any]]:
    for i in range(0, len(it), n):
        yield it[i : i + n]


def _filter_doc(dataset: str, doc_id: str) -> qm.Filter:
    return qm.Filter(
        must=[
            qm.FieldCondition(key="dataset", match=qm.MatchValue(value=dataset)),
            qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id)),
        ]
    )


def _existing_doc_sha(
    client: QdrantClient, collection: str, dataset: str, doc_id: str
) -> Optional[str]:
    points, _ = client.scroll(
        collection_name=collection,
        scroll_filter=_filter_doc(dataset, doc_id),
        limit=1,
        with_payload=True,
        with_vectors=False,
    )
    if not points:
        return None
    payload = points[0].payload or {}
    sha = payload.get("sha256")
    return str(sha) if sha else None


def _delete_doc_points(
    client: QdrantClient, collection: str, dataset: str, doc_id: str
) -> None:
    client.delete(
        collection_name=collection,
        points_selector=qm.FilterSelector(filter=_filter_doc(dataset, doc_id)),
        wait=True,
    )


def cmd_init(args: argparse.Namespace) -> None:
    client = QdrantClient(url=args.qdrant_url, timeout=60)
    model = SentenceTransformer(args.model, device="cpu")
    dim = len(model.encode(["teste"], normalize_embeddings=True)[0])
    ensure_collection(client, args.collection, dim)
    print(f"[OK] coleção pronta: {args.collection} (dim={dim})")


def cmd_index(args: argparse.Namespace) -> None:
    client = QdrantClient(url=args.qdrant_url, timeout=180)
    model = SentenceTransformer(args.model, device="cpu")

    dim = len(model.encode(["teste"], normalize_embeddings=True)[0])
    ensure_collection(client, args.collection, dim)

    rag_dir = Path(args.rag_dir)
    if not rag_dir.exists():
        raise SystemExit(f"rag_dir não existe: {rag_dir}")

    base_juridica_dir = (
        Path(args.base_juridica_dir)
        if args.base_juridica_dir
        else Path("base_juridica")
    )
    manifest_map = _load_manifest_map(base_juridica_dir)

    rag_files = sorted(rag_dir.glob("*.rag.json"))
    if not rag_files:
        raise SystemExit(f"nenhum *.rag.json em: {rag_dir}")

    total_points = 0
    skipped = 0
    changed = 0
    new = 0

    for rf in rag_files:
        doc_id = rf.name.replace(".rag.json", "").replace(".json", "")
        _, sha256 = _doc_sha256(doc_id, rf, manifest_map)

        if not args.full:
            existing_sha = _existing_doc_sha(
                client, args.collection, args.dataset, doc_id
            )
            if existing_sha == sha256:
                print(f"[SKIP] {rf.name} (inalterado sha256={sha256[:12]}...)")
                skipped += 1
                continue
            if existing_sha is None:
                print(f"[NEW ] {rf.name} (sha256={sha256[:12]}...)")
                new += 1
            else:
                print(
                    f"[CHG ] {rf.name} (sha antigo={existing_sha[:12]}... -> novo={sha256[:12]}...)"
                )
                _delete_doc_points(client, args.collection, args.dataset, doc_id)
                changed += 1
        else:
            _delete_doc_points(client, args.collection, args.dataset, doc_id)

        points = build_points_from_rag(rf, args.dataset, manifest_map)
        if not points:
            print(f"[WARN] {rf.name}: 0 chunks (estrutura não reconhecida)")
            continue

        texts = [p.text for p in points]
        vectors = model.encode(
            texts,
            batch_size=args.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        qpoints = [
            qm.PointStruct(
                id=p.point_id,
                vector=vectors[i].tolist(),
                payload=p.payload,
            )
            for i, p in enumerate(points)
        ]

        for b in batched(qpoints, args.upsert_batch):
            client.upsert(collection_name=args.collection, points=b, wait=True)

        total_points += len(qpoints)
        print(f"[OK ] {rf.name}: {len(qpoints)} chunks")

    print(
        f"[OK] indexação concluída: {total_points} chunks em {args.collection} | "
        f"skipped={skipped} new={new} changed={changed} full={'yes' if args.full else 'no'}"
    )


def cmd_query(args: argparse.Namespace) -> None:
    client = QdrantClient(url=args.qdrant_url, timeout=60)
    model = SentenceTransformer(args.model, device="cpu")

    if args.doc_kind == "jurisprudencia" and not args.court:
        raise SystemExit("Para jurisprudência, court é obrigatório (ex.: STJ).")

    qvec = model.encode([args.query], normalize_embeddings=True)[0].tolist()

    must = [qm.FieldCondition(key="doc_kind", match=qm.MatchValue(value=args.doc_kind))]
    if args.court:
        must.append(
            qm.FieldCondition(key="court", match=qm.MatchValue(value=args.court))
        )

    flt = qm.Filter(must=must)

    # compat: qdrant-client novo usa query_points; versões antigas usam search
    if hasattr(client, "query_points"):
        sig = inspect.signature(client.query_points)
        kwargs = {"collection_name": args.collection, "limit": args.top_k}
        if "query" in sig.parameters:
            kwargs["query"] = qvec
        elif "query_vector" in sig.parameters:
            kwargs["query_vector"] = qvec
        if "query_filter" in sig.parameters:
            kwargs["query_filter"] = flt
        elif "filter" in sig.parameters:
            kwargs["filter"] = flt
        if "with_payload" in sig.parameters:
            kwargs["with_payload"] = True
        res = client.query_points(**kwargs)
        res = getattr(res, "points", res)
    else:
        res = client.search(
            collection_name=args.collection,
            query_vector=qvec,
            query_filter=flt,
            limit=args.top_k,
            with_payload=True,
        )

    out = []
    for r in res:
        payload = r.payload or {}
        out.append(
            {
                "score": r.score,
                "doc_id": payload.get("doc_id"),
                "source_id": payload.get("source_id"),
                "anchor": payload.get("anchor"),
                "court": payload.get("court"),
                "path_rag": payload.get("path_rag"),
                "sha256": (payload.get("sha256") or "")[:12],
            }
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    ap.add_argument("--collection", default=DEFAULT_COLLECTION)
    ap.add_argument("--model", default=DEFAULT_MODEL)

    ap_init = sub.add_parser("init")
    ap_init.set_defaults(func=cmd_init)

    ap_idx = sub.add_parser("index")
    ap_idx.add_argument("--dataset", required=True)
    ap_idx.add_argument("--rag-dir", required=True)
    ap_idx.add_argument("--base-juridica-dir", default="base_juridica")
    ap_idx.add_argument("--batch-size", type=int, default=64)
    ap_idx.add_argument("--upsert-batch", type=int, default=128)
    ap_idx.add_argument("--full", action="store_true", help="reindexa tudo (força)")
    ap_idx.set_defaults(func=cmd_index)

    ap_q = sub.add_parser("query")
    ap_q.add_argument("--query", required=True)
    ap_q.add_argument("--doc-kind", required=True, choices=["lei", "jurisprudencia"])
    ap_q.add_argument("--court", default=None)
    ap_q.add_argument("--top-k", type=int, default=8)
    ap_q.set_defaults(func=cmd_query)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
