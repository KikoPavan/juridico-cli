#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz  # PyMuPDF


@dataclass(frozen=True)
class ExtractionMeta:
    pages_total: int
    primary_tool: str = "pymupdf"
    method: str = "text"


def extract_pages_pymupdf(pdf_path: Path) -> tuple[List[str], ExtractionMeta]:
    doc = fitz.open(pdf_path)
    pages: List[str] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        txt = page.get_text("text") or ""
        pages.append(txt)
    meta = ExtractionMeta(pages_total=doc.page_count)
    doc.close()
    return pages, meta


def main_processing_loop() -> None:
    """
    Stage 1 (independente): PDF -> MD
    Esperado: run.py injeta:
      - RULES (instância em rules.py)
      - DIR_PDF, DIR_MD
      - pdf_files (lista de Paths)
      - MODE (opcional; default md_only)
      - LIMIT (opcional)
    """
    mode = (globals().get("MODE") or "md_only").strip().lower()
    if mode != "md_only":
        raise SystemExit(
            "Este convert_stj.py foi definido como PDF->MD apenas. Use --mode md_only."
        )

    if globals().get("RULES") is None:
        raise SystemExit("RULES não foi injetado pelo run.py (profile runner).")

    if globals().get("DIR_PDF") is None or globals().get("DIR_MD") is None:
        raise SystemExit("DIR_PDF/DIR_MD não foram injetados pelo run.py.")

    rules = globals()["RULES"]
    dir_md = Path(globals()["DIR_MD"])
    dir_md.mkdir(parents=True, exist_ok=True)

    limit = globals().get("LIMIT")
    if limit is not None:
        try:
            limit = int(limit)
        except Exception:
            limit = None

    files = list(globals().get("pdf_files") or [])
    if limit:
        files = files[:limit]

    for pdf_path in files:
        pdf_path = Path(pdf_path)
        stem = pdf_path.stem

        raw_pages, extraction = extract_pages_pymupdf(pdf_path)

        cleaned_pages: List[str] = []
        for idx, raw in enumerate(raw_pages, start=1):
            t = rules.clean_page_text(raw or "")
            # cabeçalho repetido só nas páginas 2+
            if idx >= 2 and hasattr(rules, "strip_repeated_header_block"):
                t = rules.strip_repeated_header_block(t)
            cleaned_pages.append((t or "").strip())

        full_text = "\n\n".join([p for p in cleaned_pages if p]).strip()
        raw_full_text = "\n\n".join([p for p in raw_pages if p]).strip()

        meta = rules.extract_metadata(
            full_text=full_text,
            stem=stem,
            raw_full_text=raw_full_text,
        )

        fm = rules.build_front_matter_str(
            meta=meta,
            pages_total=extraction.pages_total,
            source_pdf=str(pdf_path),
            extraction=extraction,
        )

        # corpo do MD com âncoras por página (necessário para RAG/QA posterior via MD)
        body_parts: List[str] = []
        for pno, txt in enumerate(cleaned_pages, start=1):
            block = f"[[Pág. {pno}]]\n{(txt or '').strip()}".strip()
            body_parts.append(block)
        body = "\n\n".join([b for b in body_parts if b]).strip() + "\n"

        out_md = dir_md / f"{stem}.md"
        out_md.write_text(fm + "\n" + body, encoding="utf-8")
