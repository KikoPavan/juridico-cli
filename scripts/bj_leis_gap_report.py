#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def parse_article_no(s: str):
    s = (s or "").strip().upper().rstrip(".")
    if not s:
        return None, None
    if "-" in s:
        base, suf = s.split("-", 1)
        suf = suf.strip() or None
    else:
        base, suf = s, None
    base_i = int(base.replace(".", ""))
    return base_i, suf


def main():
    p = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("outputs/ingest/bj_leis/02_json/rag/L10.406_CC_2002.rag.json")
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    chunks = data.get("chunks") or []
    arts = [
        c
        for c in chunks
        if (c.get("heading_canonical") == "ARTIGO" and c.get("article_no"))
    ]

    base_has_plain = set()
    base_has_any = set()
    base_suffixes = {}

    for c in arts:
        a = str(c.get("article_no"))
        b, suf = parse_article_no(a)
        if b is None:
            continue
        base_has_any.add(b)
        if suf is None:
            base_has_plain.add(b)
        else:
            base_suffixes.setdefault(b, set()).add(suf)

    bases = sorted(base_has_any)
    if not bases:
        print("[ERRO] Nenhum ARTIGO encontrado no RAG.")
        return 2

    # gaps reais: base (numérico) ausente entre min..max
    gaps = []
    prev = bases[0]
    for x in bases[1:]:
        if x != prev + 1:
            # lista missing entre prev e x
            gaps.extend(range(prev + 1, x))
        prev = x

    # sufixo sem base (ex.: existe 48-A mas não existe 48)
    suffix_without_base = sorted(
        [b for b in base_suffixes.keys() if b not in base_has_plain]
    )

    print("== bj_leis GAP REPORT ==")
    print(f"RAG: {p}")
    print(f"ARTIGOS (chunks): {len(arts)}")
    print(f"BASES únicas (com/sem sufixo): {len(base_has_any)}")
    print(f"BASES 'plain' (sem sufixo): {len(base_has_plain)}")
    print(f"Range base: {bases[0]} .. {bases[-1]}")
    print()

    print("[1] Gaps REAIS (bases ausentes no conjunto):")
    if gaps:
        print(f"Total gaps: {len(gaps)}")
        print("Primeiros 50:", ", ".join(map(str, gaps[:50])))
    else:
        print("Nenhum gap detectado (conjunto de bases contínuo).")
    print()

    print("[2] Sufixo sem base (deve ser vazio):")
    if suffix_without_base:
        print(
            "Bases com sufixo mas sem artigo-base:",
            ", ".join(map(str, suffix_without_base[:50])),
        )
    else:
        print("OK (nenhum sufixo sem base).")
    print()

    print("[3] Bases com sufixo (amostra):")
    items = sorted(base_suffixes.items())
    if items:
        for b, sufs in items[:20]:
            print(f"{b}: {', '.join(sorted(sufs))}")
        if len(items) > 20:
            print(f"... ({len(items)} bases com sufixo no total)")
    else:
        print("Nenhuma base com sufixo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
