#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml

try:
    import pdfplumber
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "Dependência ausente: pdfplumber. Instale no venv: uv add pdfplumber"
    ) from e


# Estes símbolos são injetados pelo pipelines/ingest/pdf_convert/run.py
PROFILE_ID: str = globals().get("PROFILE_ID", "bj_leis")
MODE: str = globals().get("MODE", "md_only")
LIMIT: Optional[int] = globals().get("LIMIT", None)

DIR_PDF: str = globals().get("DIR_PDF", "")
DIR_MD: str = globals().get("DIR_MD", "")

pdf_files = globals().get("pdf_files", None)  # lista de Path (injetado)
RULES = globals().get("RULES", None)


def now_utc_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_md_text(pdf_path: Path, pages_text: List[str]) -> str:
    if RULES is None:
        raise SystemExit("RULES não foi injetado (rules.py deve exportar RULES).")

    front = RULES.front_matter(
        profile_id=PROFILE_ID, pdf_path=pdf_path, pages_total=len(pages_text)
    )
    front["generated_at"] = now_utc_iso_z()

    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    out: List[str] = [f"---\n{fm}\n---\n"]

    for i, txt in enumerate(pages_text, start=1):
        out.append(f"[[Pág. {i}]]")
        out.append(txt.strip() if (txt or "").strip() else "")
        out.append("")  # linha em branco entre páginas

    return "\n".join(out).rstrip() + "\n"


def extract_pages_text(pdf_path: Path) -> List[str]:
    pages: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            raw = page.extract_text() or ""
            cleaned = RULES.clean_page_text(raw, page_no=idx, pdf_path=pdf_path)
            pages.append(cleaned)
    return pages


def main_processing_loop() -> None:
    if MODE != "md_only":
        raise SystemExit("Este profile suporta apenas MODE=md_only (PDF→MD).")

    dir_pdf = Path(DIR_PDF).resolve()
    dir_md = Path(DIR_MD).resolve()

    if not dir_pdf.exists():
        raise SystemExit(f"Diretório de entrada (PDF) não encontrado: {dir_pdf}")

    dir_md.mkdir(parents=True, exist_ok=True)

    files: List[Path]
    if isinstance(pdf_files, list) and pdf_files:
        files = [Path(p).resolve() for p in pdf_files]
    else:
        files = sorted(dir_pdf.glob("*.pdf"))
        if LIMIT and LIMIT > 0:
            files = files[:LIMIT]

    print(f"[bj_leis] PDFs: {dir_pdf} ({len(files)})")
    print(f"[bj_leis] MD : {dir_md}")

    ok = 0
    fail = 0

    for pdf_path in files:
        try:
            pages_text = extract_pages_text(pdf_path)
            md_text = build_md_text(pdf_path, pages_text)

            out_md = (dir_md / f"{pdf_path.stem}.md").resolve()
            out_md.write_text(md_text, encoding="utf-8")

            ok += 1
            print(f"[ok] {pdf_path.name} -> {out_md.name}")
        except Exception as e:
            fail += 1
            print(f"[fail] {pdf_path.name}: {e}", file=sys.stderr)

    if fail:
        raise SystemExit(f"[bj_leis] falhas={fail} ok={ok}")
    print(f"[bj_leis] concluído: ok={ok}")


if __name__ == "__main__":
    main_processing_loop()
