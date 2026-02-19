#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

ANCHOR_RE = re.compile(r"\[\[Pág\.\s*(\d+)\]\]", re.IGNORECASE)
PAGE_ANCHOR_LINE_RE = re.compile(r"(?im)^\[\[Pág\.\s*(\d+)\]\]\s*$")

# Detecta “Art.” no início de linha (pode existir no índice também)
ART_START_RE = re.compile(
    r"(?mi)^\s*Art\.?\s*[0-9]{1,5}(?:\.[0-9]{3})*(?:\s*-\s*[A-Za-z]{1,2})?\s*(?:[º°]|o)?\s*\.?",
    re.IGNORECASE,
)

# article_no esperado em bj_leis
ART_NO_RE = re.compile(r"^\d{1,5}(?:\.\d{3})*(?:-[A-Z]{1,2})?$")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_rag_files(pattern: str) -> List[Path]:
    paths = [Path(p) for p in glob.glob(pattern, recursive=True)]
    return sorted([p for p in paths if p.is_file() and p.suffix.lower() == ".json"])


def extract_pages_from_chunk_text(txt: str) -> List[int]:
    return [int(x) for x in ANCHOR_RE.findall(txt or "")]


def norm_leis_article_id(article_no: str) -> str:
    """
    Normaliza para dedup:
    - '2.046' -> '2046'
    - '2046'  -> '2046'
    - '1.358-J' -> '1358-J'
    """
    a = (article_no or "").strip()
    if not a:
        return ""
    if "-" in a:
        base, suf = a.split("-", 1)
        base = base.replace(".", "").strip()
        suf = suf.strip().upper()
        return f"{base}-{suf}"
    return a.replace(".", "").strip()


def _strip_accents(s: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", s or "")
        if unicodedata.category(c) != "Mn"
    )


def _norm_key(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"^#{1,8}\s*", "", s).strip()  # remove markdown heading
    m = re.match(r"^\*\*(.+?)\*\*$", s)  # unbold
    if m:
        s = (m.group(1) or "").strip()
    s = _strip_accents(s)
    s = re.sub(r"\s+", " ", s).strip().upper()
    return s


def _page_has_index_heading(lines: List[str]) -> bool:
    # aceita "ÍNDICE", "**ÍNDICE**", "##### ÍNDICE", "ÍNDICE REMISSIVO", etc.
    for ln in lines:
        k = _norm_key(ln)
        if k.startswith("INDICE"):
            return True
    return False


def chunk_has_index_heading(text: str) -> bool:
    # procura um heading “ÍNDICE” dentro do próprio chunk (linha dedicada)
    lines = (text or "").splitlines()
    return _page_has_index_heading(lines)


def find_index_start_page_in_md(md_path: Path) -> Optional[int]:
    """
    Retorna a primeira página (N) cujo conteúdo contém heading de ÍNDICE
    **APÓS** detectar início real dos artigos em página que NÃO é página de índice.

    Evita falso-positivo quando o índice/sumário inicial contém linhas “Art. …”.
    """
    if not md_path.exists():
        return None

    text = md_path.read_text(encoding="utf-8", errors="replace")

    cur_page: Optional[int] = None
    buf: List[str] = []
    started_articles = False

    def process_page(page_no: int, lines: List[str]) -> Optional[int]:
        nonlocal started_articles

        is_index_page = _page_has_index_heading(lines)
        page_text = "\n".join(lines)

        # só marca início real dos artigos se NÃO for página de índice
        if (
            (not started_articles)
            and (not is_index_page)
            and ART_START_RE.search(page_text)
        ):
            started_articles = True

        # só aceita índice como “índice final” depois que artigos começaram
        if started_articles and is_index_page:
            return page_no

        return None

    for ln in text.splitlines():
        m = PAGE_ANCHOR_LINE_RE.match((ln or "").strip())
        if m:
            if cur_page is not None:
                hit = process_page(cur_page, buf)
                if hit is not None:
                    return hit
            cur_page = int(m.group(1))
            buf = []
            continue

        if cur_page is None:
            continue

        buf.append(ln)

    if cur_page is not None:
        hit = process_page(cur_page, buf)
        if hit is not None:
            return hit

    return None


@dataclass
class ValidationResult:
    path: Path
    doc_id: str
    profile_id: str
    ok: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


def validate_one_rag(rag_path: Path) -> ValidationResult:
    rag = load_json(rag_path)

    doc_id = str(rag.get("doc_id") or "")
    profile_id = str(rag.get("profile_id") or "")
    stem = str(rag.get("stem") or rag_path.stem)
    chunks = rag.get("chunks")

    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {"stem": stem}

    if not doc_id:
        errors.append("Top-level: 'doc_id' ausente/vazio.")
    if not profile_id:
        errors.append("Top-level: 'profile_id' ausente/vazio.")
    if not isinstance(chunks, list) or not chunks:
        errors.append("Top-level: 'chunks' ausente/vazio ou não-lista.")
        return ValidationResult(
            rag_path, doc_id, profile_id, False, errors, warnings, stats
        )

    seen_chunk_id: set[str] = set()
    missing_anchor = 0
    empty_text = 0

    max_page_any = 0
    max_page_artigo = 0
    artigo_count = 0

    is_leis = profile_id == "bj_leis"
    seen_art_norm: set[str] = set()
    dup_art_norm: List[str] = []
    invalid_art_format = 0

    # para checar “índice dentro de ARTIGO”
    artigos_with_index_heading: List[str] = []

    for ch in chunks:
        if not isinstance(ch, dict):
            errors.append("Chunk não é objeto (dict).")
            continue

        chunk_id = str(ch.get("chunk_id") or "")
        if not chunk_id:
            errors.append("Chunk sem 'chunk_id'.")
        else:
            if chunk_id in seen_chunk_id:
                errors.append(f"Duplicação de chunk_id: {chunk_id}")
            seen_chunk_id.add(chunk_id)

        heading = str(ch.get("heading_canonical") or "")
        text = str(ch.get("text") or "").strip()

        if not text:
            empty_text += 1

        pages_in_text = extract_pages_from_chunk_text(text)
        if pages_in_text:
            max_page_any = max(max_page_any, max(pages_in_text))

        anchors = ch.get("anchors")
        anchors_ok = isinstance(anchors, list) and any(
            isinstance(a, str) and ANCHOR_RE.search(a) for a in anchors
        )

        if not anchors_ok and not pages_in_text:
            missing_anchor += 1

        if heading == "ARTIGO":
            artigo_count += 1
            if pages_in_text:
                max_page_artigo = max(max_page_artigo, max(pages_in_text))

            if chunk_has_index_heading(text):
                # aqui só pega heading de índice em linha dedicada (não “índice” em texto comum)
                artigos_with_index_heading.append(
                    str(ch.get("article_no") or "").strip() or chunk_id
                )

            if is_leis:
                art_no = str(ch.get("article_no") or "").strip()
                if not art_no:
                    errors.append(
                        f"[bj_leis] Chunk ARTIGO sem 'article_no' (chunk_id={chunk_id})."
                    )
                else:
                    if not ART_NO_RE.match(art_no.upper()):
                        invalid_art_format += 1
                    norm = norm_leis_article_id(art_no)
                    if norm in seen_art_norm:
                        dup_art_norm.append(norm)
                    else:
                        seen_art_norm.add(norm)

    stats.update(
        {
            "chunks_total": len(chunks),
            "artigos": artigo_count,
            "max_page_any": max_page_any,
            "max_page_artigo": max_page_artigo,
            "missing_anchor": missing_anchor,
            "empty_text": empty_text,
        }
    )

    if empty_text:
        errors.append(f"{empty_text} chunk(s) com 'text' vazio.")

    if missing_anchor:
        errors.append(
            f"{missing_anchor} chunk(s) sem âncora em 'anchors' e sem [[Pág. N]] no 'text'."
        )

    if is_leis:
        if dup_art_norm:
            sample = ", ".join(dup_art_norm[:10])
            errors.append(
                f"[bj_leis] Duplicações após normalização de article_no (ex.: {sample})."
            )

        if invalid_art_format:
            warnings.append(
                f"[bj_leis] {invalid_art_format} article_no fora do padrão esperado (não fatal)."
            )

        md_src = None
        sources = rag.get("sources") or {}
        if isinstance(sources, dict):
            md_src = sources.get("md")

        if md_src:
            md_path = Path(str(md_src))
            idx_page = find_index_start_page_in_md(md_path)
            stats["md_source"] = str(md_path)
            stats["index_start_page_after_articles"] = idx_page

            if idx_page is not None:
                # REGRA CORRETA:
                # - vazamento por página só existe se artigo aparece em página > página do índice
                if max_page_artigo > idx_page:
                    errors.append(
                        f"[bj_leis] Vazamento do índice: max_page_artigo={max_page_artigo} "
                        f"> index_start_page={idx_page} (verifique stop em 'ÍNDICE')."
                    )
                # - se for a mesma página, só é erro se o chunk ARTIGO tiver heading de ÍNDICE dentro dele
                elif max_page_artigo == idx_page and artigos_with_index_heading:
                    sample = ", ".join(artigos_with_index_heading[:10])
                    errors.append(
                        f"[bj_leis] Possível vazamento: índice e último artigo na mesma página ({idx_page}) "
                        f"e encontrei heading de ÍNDICE dentro de ARTIGO (ex.: {sample})."
                    )
        else:
            warnings.append(
                "[bj_leis] 'sources.md' ausente; não deu para checar corte do índice via MD."
            )

    ok = not errors
    return ValidationResult(rag_path, doc_id, profile_id, ok, errors, warnings, stats)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--glob",
        default="outputs/ingest/**/02_json/rag/*.rag.json",
        help="Glob para localizar os RAGs (default: outputs/ingest/**/02_json/rag/*.rag.json)",
    )
    ap.add_argument(
        "--profile", default="", help="Filtra por profile_id (ex.: bj_leis)"
    )
    ap.add_argument("--fail-fast", action="store_true", help="Para no primeiro FAIL")
    args = ap.parse_args()

    files = iter_rag_files(args.glob)
    if not files:
        raise SystemExit(f"Nenhum RAG encontrado com: {args.glob}")

    total = 0
    passed = 0
    failed = 0

    print("== RAG VALIDATION ==")
    print(f"glob   : {args.glob}")
    print(f"files  : {len(files)}")
    if args.profile:
        print(f"filter : profile_id == {args.profile}")
    print()

    for p in files:
        r = validate_one_rag(p)

        if args.profile and r.profile_id != args.profile:
            continue

        total += 1
        if r.ok:
            passed += 1
            print(f"[PASS] {p}  (profile={r.profile_id} doc_id={r.doc_id})")
        else:
            failed += 1
            print(f"[FAIL] {p}  (profile={r.profile_id} doc_id={r.doc_id})")
            for e in r.errors:
                print(f"  - {e}")
            for w in r.warnings:
                print(f"  ~ {w}")
            if args.fail_fast:
                break

    print()
    print(f"SUMMARY: total={total} pass={passed} fail={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
