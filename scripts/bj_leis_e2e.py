#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CHUNKS_KEY_CANDIDATES = ("chunks", "items", "data")
TEXT_KEYS = ("text", "content", "md", "body", "chunk_text")

PAGE_RE = re.compile(r"\[\[Pág\.\s*(\d+)\]\]", re.IGNORECASE)


def run_cmd(cmd: List[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    cp = subprocess.run(cmd, text=True)
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)


def read_json(p: Path) -> Any:
    if not p.exists():
        raise SystemExit(f"[ERRO] Arquivo não encontrado: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def pick_doc_stem(pdf_dir: Path, doc: Optional[str]) -> str:
    if doc:
        return doc.replace(".pdf", "").replace(".md", "")
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"[ERRO] Nenhum PDF em: {pdf_dir}")
    return pdfs[0].stem


def extract_chunks(rag: Any) -> List[Dict[str, Any]]:
    if isinstance(rag, dict):
        for k in CHUNKS_KEY_CANDIDATES:
            v = rag.get(k)
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    if isinstance(rag, list) and rag and isinstance(rag[0], dict):
        return rag
    return []


def get_text(d: Dict[str, Any]) -> str:
    for k in TEXT_KEYS:
        v = d.get(k)
        if isinstance(v, str):
            return v
    return ""


def get_article_no_raw(c: Dict[str, Any]) -> Optional[str]:
    # campo padrão do seu RAG: article_no
    v = c.get("article_no")
    if isinstance(v, (str, int)):
        return str(v).strip()

    # fallback: tenta outros nomes (não deveria ser necessário no seu caso)
    for k in ("article_id", "art_id", "id", "key"):
        v = c.get(k)
        if isinstance(v, (str, int)):
            return str(v).strip()
    return None


def normalize_article_no(article_no: str) -> Tuple[Optional[int], Optional[str], str]:
    """
    Ex.: "2.046" -> (2046, None, "2046")
         "48-A"  -> (48, "A", "48-A")
         "1.620."-> (1620, None, "1620")
    Retorna: (base_int, suffix, normalized_id_str)
    """
    s = article_no.strip().upper().rstrip(".")
    if "-" in s:
        base_s, suf = s.split("-", 1)
        suf = suf.strip() or None
    else:
        base_s, suf = s, None

    base_s2 = base_s.replace(".", "").strip()
    if not base_s2.isdigit():
        return (None, suf, s)

    base_i = int(base_s2)
    norm = f"{base_i}-{suf}" if suf else f"{base_i}"
    return (base_i, suf, norm)


def parse_pages_from_text(t: str) -> List[int]:
    return [int(m.group(1)) for m in PAGE_RE.finditer(t)]


def find_art_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in chunks:
        hc = c.get("heading_canonical")
        a = get_article_no_raw(c)
        if not a:
            continue
        # seu RAG usa heading_canonical=="ARTIGO" (e no seu caso todos vieram ARTIGO)
        if isinstance(hc, str) and hc.strip().upper() == "ARTIGO":
            out.append(c)
        else:
            # fallback: se não tiver heading_canonical, mas tiver article_no, considera
            out.append(c)
    return out


def pick_art_2046(art_chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    base = None
    first_suffix = None
    for c in art_chunks:
        raw = get_article_no_raw(c)
        if not raw:
            continue
        base_i, suf, _ = normalize_article_no(raw)
        if base_i == 2046 and suf is None:
            base = c
            break
        if base_i == 2046 and first_suffix is None:
            first_suffix = c
    return base or first_suffix


def validate_outputs(doc_stem: str) -> None:
    base = Path("outputs/ingest/bj_leis")
    qa_path = base / f"03_report/qa/{doc_stem}.qa.json"
    rag_path = base / f"02_json/rag/{doc_stem}.rag.json"
    md_path = base / f"01_md/{doc_stem}.md"

    qa = read_json(qa_path)
    rag = read_json(rag_path)
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    chunks = extract_chunks(rag)
    if not chunks:
        if isinstance(rag, dict):
            raise SystemExit(
                f"[ERRO] RAG sem lista de chunks. Keys do topo: {sorted(rag.keys())}"
            )
        raise SystemExit("[ERRO] RAG sem lista de chunks (estrutura inesperada).")

    art_chunks = find_art_chunks(chunks)
    if not art_chunks:
        raise SystemExit("[ERRO] Não encontrei chunks com article_no no RAG.")

    # --- duplicações: checar por ID NORMALIZADO (remove '.' só para comparar)
    norm_ids: List[str] = []
    raw_ids: List[str] = []
    for c in art_chunks:
        raw = get_article_no_raw(c)
        if not raw:
            continue
        raw_ids.append(raw)
        _, _, nid = normalize_article_no(raw)
        norm_ids.append(nid)

    seen = set()
    dups_norm = []
    for nid in norm_ids:
        if nid in seen:
            dups_norm.append(nid)
        else:
            seen.add(nid)
    dups_norm = sorted(set(dups_norm))

    # --- checagem forte: nenhum ARTIGO pode ter [[Pág. >=178]]
    offenders: List[Tuple[str, int]] = []
    max_page_seen = 0
    for c in art_chunks:
        raw = get_article_no_raw(c) or "?"
        t = get_text(c)
        pages = parse_pages_from_text(t)
        if pages:
            pmax = max(pages)
            if pmax > max_page_seen:
                max_page_seen = pmax
            if pmax >= 178:
                offenders.append((raw, pmax))
    offenders.sort(key=lambda x: x[1], reverse=True)

    # --- checagem específica: Art. 2046 não pode conter ÍNDICE nem pág>=178
    c2046 = pick_art_2046(art_chunks)
    ok2046 = True
    det2046 = "OK"
    if not c2046:
        ok2046 = False
        det2046 = "Não encontrei chunk do Art. 2.046 no RAG (normalizado para 2046)"
    else:
        t = get_text(c2046)
        up = t.upper()
        if "ÍNDICE" in up:
            ok2046 = False
            det2046 = "Art. 2.046 contém 'ÍNDICE' (vazamento)"
        else:
            pages = parse_pages_from_text(t)
            if any(p >= 178 for p in pages):
                ok2046 = False
                det2046 = f"Art. 2.046 contém [[Pág. >=178]] (máx={max(pages) if pages else 0})"

    md_has_index = "ÍNDICE" in md_text.upper()

    qa_flags = {}
    if isinstance(qa, dict):
        for k in (
            "index_stop_hit",
            "index_leak_art_2046",
            "duplicates",
            "article_count",
            "started_articles",
        ):
            if k in qa:
                qa_flags[k] = qa[k]

    # Métrica informativa: quantos article_no têm ponto (isso é NORMAL no seu RAG)
    dotted_raw = []
    for r in raw_ids:
        base_part = r.split("-", 1)[0]
        if "." in base_part:
            dotted_raw.append(r)

    print("\n========================")
    print("VALIDAÇÃO bj_leis (RAG)")
    print("========================")
    print(f"doc: {doc_stem}")
    print(f"qa : {qa_path}")
    print(f"rag: {rag_path}")
    print(f"md : {md_path}")

    if qa_flags:
        print("\n[QA] flags encontradas:")
        for k, v in qa_flags.items():
            print(f" - {k}: {v}")
    else:
        print("\n[QA] (sem flags padronizadas detectadas; validação segue pelo RAG/MD)")

    print("\n[RAG] métricas:")
    print(f" - chunks totais: {len(chunks)}")
    print(f" - chunks com article_no: {len(art_chunks)}")
    print(f" - ids normalizados: {len(norm_ids)}")
    print(
        f" - duplicações (ID normalizado): {len(dups_norm)}"
        + (f" (ex.: {dups_norm[:10]})" if dups_norm else "")
    )
    print(
        f" - article_no com ponto (formato normal): {len(dotted_raw)} (ex.: {dotted_raw[:10]})"
    )

    print("\n[MD] índice:")
    print(f" - contém 'ÍNDICE': {md_has_index}")

    print("\n[PÁGINAS] máximos em chunks ARTIGO:")
    print(f" - maior [[Pág. N]] visto em ARTIGO: {max_page_seen}")
    if offenders:
        print(
            f" - [ALERTA] chunks ARTIGO com [[Pág. >=178]]: {len(offenders)} (top 10 abaixo)"
        )
        for a, p in offenders[:10]:
            print(f"   - Art {a} -> máx pág {p}")
    else:
        print(" - [OK] nenhum chunk ARTIGO contém [[Pág. >=178]]")

    print("\n[CHECK] Art. 2.046:")
    print(f" - {det2046}")

    failures = []
    if dups_norm:
        failures.append(
            "Há duplicações após normalização (ex.: '2.046' e '2046' coexistindo)"
        )
    if offenders:
        failures.append("Há chunk(s) ARTIGO contendo páginas do índice (>=178)")
    if not ok2046:
        failures.append("Art. 2.046 com vazamento de índice/pág>=178 ou não encontrado")

    if isinstance(qa, dict) and qa.get("index_leak_art_2046") is True:
        failures.append("QA sinalizou index_leak_art_2046=true")

    print("\n[RESULTADO]")
    if failures:
        for f in failures:
            print(f" - [FALHA] {f}")
        raise SystemExit(2)

    print(
        " - [OK] bj_leis consistente (sem duplicações pós-normalização, sem páginas do índice em ARTIGO, Art. 2.046 limpo)"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Executa PDF→MD + MD→RAG + validações para bj_leis (end-to-end)."
    )
    ap.add_argument(
        "--doc",
        help="Stem do documento (ex.: L10.406_CC_2002). Se omitido, usa o primeiro PDF.",
    )
    ap.add_argument("--skip-pdf", action="store_true", help="Pula o estágio PDF→MD.")
    ap.add_argument("--skip-rag", action="store_true", help="Pula o estágio MD→RAG.")
    args = ap.parse_args()

    pdf_dir = Path("input/base_juridica/bj_leis/00_pdf")
    doc_stem = pick_doc_stem(pdf_dir, args.doc)

    if not args.skip_pdf:
        run_cmd(
            [
                "uv",
                "run",
                "python",
                "pipelines/ingest/pdf_convert/run.py",
                "--profile",
                "bj_leis",
                "--mode",
                "md_only",
            ]
        )

    if not args.skip_rag:
        run_cmd(
            [
                "uv",
                "run",
                "python",
                "pipelines/ingest/md_rag/run.py",
                "--profiles",
                "bj_leis",
            ]
        )

    validate_outputs(doc_stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
