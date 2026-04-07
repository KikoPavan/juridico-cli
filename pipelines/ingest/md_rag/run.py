#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# -----------------------------
# Util: projeto / profile
# -----------------------------
def find_project_root(start: Path) -> Path:
    start = start.resolve()
    for p in [start] + list(start.parents):
        if (p / "pyproject.toml").exists():
            return p
    return start


def resolve_profile_yaml(project_root: Path, profile_arg: str) -> Path:
    """
    Procura profile.yaml em:
      1) md_rag/profiles/<name>/profile.yaml
      2) pdf_convert/profiles/<name>/profile.yaml  (reuso de dirs.md)
    """
    candidates = [
        project_root
        / "pipelines"
        / "ingest"
        / "md_rag"
        / "profiles"
        / profile_arg
        / "profile.yaml",
        project_root
        / "pipelines"
        / "ingest"
        / "pdf_convert"
        / "profiles"
        / profile_arg
        / "profile.yaml",
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    raise SystemExit(
        f"Profile não encontrado para '{profile_arg}'. "
        f"Esperado em md_rag/profiles ou pdf_convert/profiles."
    )


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Profile inválido (YAML não é objeto): {path}")
    return data


def resolve_dirs(project_root: Path, data: Dict[str, Any]) -> Dict[str, Path]:
    dirs = data.get("dirs") or {}
    if not isinstance(dirs, dict):
        raise SystemExit("Profile inválido: 'dirs' deve ser objeto.")
    out: Dict[str, Path] = {}
    for key in ("md", "json", "rep"):
        v = dirs.get(key)
        if not v:
            continue
        out[key] = (project_root / str(v)).resolve()
    return out


def derive_json_rep_from_md(md_dir: Path) -> Tuple[Path, Path]:
    md_dir = md_dir.resolve()
    if md_dir.name == "01_md":
        base = md_dir.parent
        return (base / "02_json").resolve(), (base / "03_report").resolve()
    base = md_dir.parent
    return (base / "02_json").resolve(), (base / "03_report").resolve()


def now_utc_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_stem(md_path: Path, md_root: Path) -> str:
    rel = md_path.resolve().relative_to(md_root.resolve())
    return rel.with_suffix("").as_posix().replace("/", "__")


def _outputs_for_stem(stem: str, json_dir: Path, rep_dir: Path) -> list[Path]:
    raw_p = (json_dir / "raw" / f"{stem}.raw.json").resolve()
    rag_p = (json_dir / "rag" / f"{stem}.rag.json").resolve()
    qa_p = (rep_dir / "qa" / f"{stem}.qa.json").resolve()
    rep_p = (rep_dir / "logs" / f"{stem}.md_rag.report.md").resolve()
    return [raw_p, rag_p, qa_p, rep_p]


def _is_fresh(md_path: Path, stem: str, json_dir: Path, rep_dir: Path) -> bool:
    """
    True => já processado e atualizado:
      - todos os artefatos existem
      - todos têm mtime >= mtime do MD
    """
    md_mtime = md_path.stat().st_mtime
    outs = _outputs_for_stem(stem, json_dir, rep_dir)
    for p in outs:
        if not p.exists():
            return False
        try:
            if p.stat().st_mtime < md_mtime:
                return False
        except OSError:
            return False
    return True


# -----------------------------
# MD parsing
# -----------------------------
FRONT_RE = re.compile(r"(?s)\A---\n(.*?)\n---\n", re.IGNORECASE)
PAGE_ANCHOR_RE = re.compile(r"(?im)^\[\[Pág\.\s*(\d+)\]\]\s*$")


@dataclass
class MdDoc:
    stem: str
    md_path: Path
    front: Dict[str, Any]
    body: str
    pages: Dict[int, str]  # page_no -> text


def parse_md(md_path: Path, *, stem: Optional[str] = None) -> MdDoc:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    stem2 = stem or md_path.stem

    front: Dict[str, Any] = {}
    body = text

    m = FRONT_RE.search(text)
    if m:
        fm_raw = m.group(1)
        try:
            fm_obj = yaml.safe_load(fm_raw) or {}
            if isinstance(fm_obj, dict):
                front = fm_obj
        except Exception:
            front = {}
        body = text[m.end() :]

    pages: Dict[int, List[str]] = {}
    cur_p: Optional[int] = None

    for ln in body.splitlines():
        ma = PAGE_ANCHOR_RE.match((ln or "").strip())
        if ma:
            cur_p = int(ma.group(1))
            pages.setdefault(cur_p, [])
            continue
        if cur_p is None:
            continue
        pages[cur_p].append(ln)

    pages2: Dict[int, str] = {}
    for p in sorted(pages.keys()):
        pages2[p] = "\n".join(pages[p]).strip()

    return MdDoc(stem=stem2, md_path=md_path, front=front, body=body, pages=pages2)


# -----------------------------
# RAG rules (STJ)
# -----------------------------
class STJRagRules:
    RAG_RULES_VERSION = "stj-md-rag-v1"
    REQUIRED = ("EMENTA", "VOTO", "TERMO_DE_JULGAMENTO")

    _HEADING_ONLY_RE = re.compile(
        r"^\s*(?:\*\*)?\s*(EMENTA|ACÓRDÃO|ACORDAO|RELATÓRIO|RELATORIO|VOTO|TERMO|TERMO\s+DE\s+JULGAMENTO|AUTUAÇÃO|AUTUACAO|AGRAVO\s+INTERNO|CERTIDÃO\s+DE\s+JULGAMENTO|CERTIDAO\s+DE\s+JULGAMENTO|CERTIDAO)\s*(?:\*\*)?\s*$",
        re.IGNORECASE,
    )

    _MAP = {
        "EMENTA": "EMENTA",
        "ACORDAO": "ACORDAO_RESULTADO",
        "RELATORIO": "RELATORIO",
        "VOTO": "VOTO",
        "TERMO": "TERMO_DE_JULGAMENTO",
        "TERMO DE JULGAMENTO": "TERMO_DE_JULGAMENTO",
        "AUTUACAO": "AUTUACAO",
        "AGRAVO INTERNO": "AGRAVO_INTERNO",
        "CERTIDAO DE JULGAMENTO": "TERMO_DE_JULGAMENTO",
        "CERTIDAO": "TERMO_DE_JULGAMENTO",
    }

    @staticmethod
    def _strip_accents(s: str) -> str:
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s or "")
            if unicodedata.category(c) != "Mn"
        )

    @classmethod
    def _norm(cls, s: str) -> str:
        s = cls._strip_accents((s or "").strip())
        s = re.sub(r"\s+", " ", s)
        return s.upper().strip()

    @classmethod
    def _extract_heading_raw(cls, line: str) -> Optional[str]:
        s = (line or "").strip()
        if not s:
            return None
        m = re.match(r"^\*\*(.+?)\*\*$", s)
        core = (m.group(1) or "").strip() if m else s
        if not cls._HEADING_ONLY_RE.match(s):
            return None
        return core

    @classmethod
    def _canon(cls, heading_raw: str) -> Optional[str]:
        key = cls._norm(heading_raw)
        return cls._MAP.get(key)

    @staticmethod
    def _page_blocks(content_by_page: Dict[int, List[str]]) -> List[str]:
        blocks: List[str] = []
        for p in sorted(content_by_page.keys()):
            txt = "\n".join(content_by_page.get(p) or []).strip()
            if not txt:
                continue
            blocks.append(f"[[Pág. {p}]]\n{txt}".strip())
        return blocks

    @staticmethod
    def _chunk_blocks(
        blocks: List[str], *, min_chars: int, max_chars: int
    ) -> List[str]:
        chunks: List[str] = []
        buf = ""
        for b in blocks:
            b2 = (b or "").strip()
            if not b2:
                continue
            cand = b2 if not buf else (buf + "\n\n" + b2)
            if len(cand) <= max_chars:
                buf = cand
                continue
            if buf:
                chunks.append(buf)
            buf = b2
        if buf:
            chunks.append(buf)

        out: List[str] = []
        for c in chunks:
            if out and len(out[-1]) < min_chars:
                out[-1] = (out[-1] + "\n\n" + c).strip()
            else:
                out.append(c)
        return [x.strip() for x in out if x.strip()]

    def build(
        self, doc: MdDoc, *, profile_id: str, out_json_dir: Path, out_rep_dir: Path
    ) -> None:
        md_path = doc.md_path
        stem = doc.stem
        doc_id = f"{profile_id}:{stem}"

        raw_md = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "stem": stem,
            "generated_at": now_utc_iso_z(),
            "sources": {"md": str(md_path)},
            "meta": dict(doc.front or {}),
            "pages_total": len(doc.pages),
            "pages": [
                {"page": p, "text": doc.pages[p]} for p in sorted(doc.pages.keys())
            ],
        }

        sections: List[Dict[str, Any]] = []
        chunks: List[Dict[str, Any]] = []

        ementa_seen = 0
        section_seq = 0
        chunk_seq = 0
        current: Optional[Dict[str, Any]] = None

        def new_section(
            heading_raw: str, heading_canon: str, start_page: int, occ: int
        ) -> Dict[str, Any]:
            nonlocal section_seq
            section_seq += 1
            return {
                "section_id": f"{stem}::S{section_seq:03d}",
                "heading_raw": heading_raw,
                "heading_canonical": heading_canon,
                "start_page": start_page,
                "end_page": start_page,
                "occurrence_index": occ,
                "chunk_policy": "AUTO",
                "_content_by_page": {},
            }

        for page_no in sorted(doc.pages.keys()):
            page_text = doc.pages.get(page_no) or ""
            for ln in page_text.split("\n"):
                h_raw = self._extract_heading_raw(ln)
                if h_raw:
                    canon_base = self._canon(h_raw)
                    if not canon_base:
                        continue
                    canon = canon_base
                    occ = 1
                    if canon_base == "EMENTA":
                        ementa_seen += 1
                        occ = ementa_seen
                        if ementa_seen >= 2:
                            canon = "EMENTA_REAPRESENTADA"
                    current = new_section(h_raw, canon, page_no, occ)
                    sections.append(current)
                    continue

                if current is not None:
                    current["end_page"] = page_no
                    cbp = current["_content_by_page"]
                    cbp.setdefault(page_no, []).append(ln)

        for s in sections:
            canon = s.get("heading_canonical")
            if canon in ("EMENTA", "VOTO", "TERMO_DE_JULGAMENTO", "AUTUACAO"):
                s["chunk_policy"] = "CHUNK"
            else:
                s["chunk_policy"] = "NO_CHUNKS"

        anchor_re = re.compile(r"\[\[Pág\.\s*\d+\]\]", re.IGNORECASE)

        for s in sections:
            canon = s.get("heading_canonical")
            if s.get("chunk_policy") != "CHUNK":
                continue
            if canon == "EMENTA_REAPRESENTADA":
                continue

            content_by_page: Dict[int, List[str]] = s.get("_content_by_page") or {}
            blocks = self._page_blocks(content_by_page)
            if not blocks:
                continue

            if canon == "EMENTA":
                chunk_texts = [("\n\n".join(blocks)).strip()]
            elif canon == "VOTO":
                chunk_texts = self._chunk_blocks(blocks, min_chars=800, max_chars=1500)
            else:
                chunk_texts = self._chunk_blocks(blocks, min_chars=500, max_chars=1500)
                if len(chunk_texts) > 2:
                    chunk_texts = [chunk_texts[0], "\n\n".join(chunk_texts[1:]).strip()]

            for ct in chunk_texts:
                ct2 = (ct or "").strip()
                if not ct2:
                    continue
                pages = [int(x) for x in re.findall(r"\[\[Pág\.\s*(\d+)\]\]", ct2)]
                if pages:
                    p_start, p_end = min(pages), max(pages)
                    anchors: List[str] = []
                    for p in pages:
                        a = f"[[Pág. {p}]]"
                        if a not in anchors:
                            anchors.append(a)
                else:
                    p_start = int(s.get("start_page") or 1)
                    p_end = int(s.get("end_page") or p_start)
                    anchors = [f"[[Pág. {p_start}]]"]
                    if not anchor_re.search(ct2):
                        ct2 = (anchors[0] + "\n" + ct2).strip()

                chunk_seq += 1
                chunks.append(
                    {
                        "chunk_id": f"{stem}::C{chunk_seq:04d}",
                        "section_id": s.get("section_id"),
                        "heading_canonical": canon,
                        "text": f"{canon}\n\n{ct2}".strip(),
                        "page_ref": {"start": p_start, "end": p_end},
                        "anchors": anchors,
                    }
                )

        for s in sections:
            s.pop("_content_by_page", None)

        rag = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "stem": stem,
            "generated_at": now_utc_iso_z(),
            "sources": {"md": str(md_path)},
            "meta": dict(doc.front or {}),
            "normalizations": {
                "rules_version": self.RAG_RULES_VERSION,
                "rag_source": "markdown",
                "heading_canonicalization": dict(self._MAP),
            },
            "sections": sections,
            "chunks": chunks,
        }

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        present = {str(s.get("heading_canonical") or "") for s in (sections or [])}
        missing = [x for x in self.REQUIRED if x not in present]
        if missing:
            errors.append(
                {
                    "code": "MISSING_REQUIRED_SECTIONS",
                    "msg": "Seções mínimas ausentes.",
                    "details": {"missing": missing},
                }
            )

        for ch in chunks:
            txt = (ch.get("text") or "").strip()
            if not anchor_re.search(txt):
                errors.append(
                    {
                        "code": "MISSING_ANCHOR",
                        "msg": "Chunk sem âncora [[Pág. N]].",
                        "details": {"chunk_id": ch.get("chunk_id")},
                    }
                )

        status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
        qa = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "stem": stem,
            "generated_at": now_utc_iso_z(),
            "status": status,
            "ingest_to_qdrant_allowed": status in ("PASS", "PASS_WITH_WARNINGS"),
            "checks": {
                "required_sections_expected": list(self.REQUIRED),
                "required_sections_found": sorted([x for x in present if x]),
            },
            "errors": errors,
            "warnings": warnings,
        }

        rep = [
            f"# MD→RAG Report — {stem}",
            "",
            f"- profile: {profile_id}",
            f"- md: {md_path}",
            f"- pages: {len(doc.pages)}",
            f"- chunks: {len(chunks)}",
            f"- qa.status: {status}",
            "",
        ]
        if errors:
            rep.append("## Errors")
            for e in errors:
                rep.append(f"- {e.get('code')}: {e.get('msg')}")
        if warnings:
            rep.append("## Warnings")
            for w in warnings:
                rep.append(f"- {w.get('code')}: {w.get('msg')}")
        rep_md = "\n".join(rep).strip() + "\n"

        raw_dir = out_json_dir / "raw"
        rag_dir = out_json_dir / "rag"
        qa_dir = out_rep_dir / "qa"
        logs_dir = out_rep_dir / "logs"

        raw_dir.mkdir(parents=True, exist_ok=True)
        rag_dir.mkdir(parents=True, exist_ok=True)
        qa_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        (raw_dir / f"{stem}.raw.json").write_text(
            json.dumps(raw_md, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (rag_dir / f"{stem}.rag.json").write_text(
            json.dumps(rag, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (qa_dir / f"{stem}.qa.json").write_text(
            json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (logs_dir / f"{stem}.md_rag.report.md").write_text(rep_md, encoding="utf-8")


# -----------------------------
# RAG rules (LEIS)
# -----------------------------
class LeisRagRules:
    """
    MD→RAW/RAG/QA para leis (bj_leis):
    - Chunks por Art. N (mantém âncoras [[Pág. N]] adicionadas aqui)
    - Captura hierarquia LIVRO/TÍTULO/SUBTÍTULO/CAPÍTULO/Seção/Subseção a partir dos headings do MD
    - Para ao encontrar "ÍNDICE" após ter iniciado artigos (evita capturar sumário e evita arrastar o último artigo)
    - Dedup global de artigo (evita duplicatas como 1.358-J vindas do índice)
    - Expande "Art. X. a Y." em artigos individuais (revogados em faixa)
    - Normaliza "Art. 1º/1°/1 o" → "Art. 1." e aceita "Art" sem ponto
    """

    RAG_RULES_VERSION = "leis-md-rag-v2"

    _ANCHOR_RE = re.compile(r"\[\[Pág\.\s*(\d+)\]\]", re.IGNORECASE)
    _MD_HEADING_RE = re.compile(r"^(#{1,8})\s*(.+?)\s*$")
    _BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*$")

    # Artigo normal:
    # - aceita "Art" com/sem ponto
    # - base: 1.620 / 2046 / 10
    # - sufixo opcional: -A / -J / -AA (1-2 letras)
    # - aceita ordinal º / ° / o (com ou sem espaço)
    _ART_RE = re.compile(
        r"^Art\.?\s*([0-9]{1,5}(?:\.[0-9]{3})*)\s*(?:-\s*([A-Za-z]{1,2}))?\s*(?:[º°]|o)?\s*\.?\s*(.*)$",
        re.IGNORECASE,
    )

    # Faixa: "Art. 1.620. a 1.629. (Revogados...)"
    _ART_RANGE_RE = re.compile(
        r"^Art\.?\s*([0-9]{1,5}(?:\.[0-9]{3})*)\.?\s*(?:a|à|-|–|—)\s*([0-9]{1,5}(?:\.[0-9]{3})*)\.?\s*(.*)$",
        re.IGNORECASE,
    )

    @staticmethod
    def _strip_accents(s: str) -> str:
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s or "")
            if unicodedata.category(c) != "Mn"
        )

    @classmethod
    def _norm(cls, s: str) -> str:
        s2 = cls._strip_accents((s or "").strip())
        s2 = re.sub(r"\s+", " ", s2)
        return s2.upper().strip()

    @staticmethod
    def _unbold(s: str) -> str:
        s2 = (s or "").strip()
        m = re.match(r"^\*\*(.+?)\*\*$", s2)
        return (m.group(1) if m else s2).strip()

    @classmethod
    def _clean_heading_text(cls, s: str) -> str:
        return cls._unbold((s or "").strip())

    @classmethod
    def _is_candidate_name_line(cls, s: str) -> bool:
        s2 = (s or "").strip()
        if not s2:
            return False
        if s2.startswith("Art") or s2.startswith("§") or s2.startswith("Parágrafo"):
            return False
        if any(ch.isdigit() for ch in s2):
            return False
        if len(s2) > 120:
            return False
        return bool(cls._BOLD_ONLY_RE.match(s2))

    @staticmethod
    def _fmt_dot(n: int) -> str:
        # 1620 -> 1.620 ; 2046 -> 2.046 ; 999 -> 999
        return f"{n:,}".replace(",", ".")

    @staticmethod
    def _to_int_base(s: str) -> int:
        return int((s or "").replace(".", ""))

    @classmethod
    def _canon_article_no(
        cls, base_raw: str, suf_raw: str = ""
    ) -> Tuple[str, str, str]:
        """
        Canonicaliza número do artigo para evitar duplicações por pontuação:
          - "1597" e "1.597" -> base_txt "1.597"
          - sufixo -> sempre uppercase e sem espaços
        Retorna (art_no, base_txt, suf_txt)
        """
        base_i = cls._to_int_base(base_raw)
        base_txt = cls._fmt_dot(base_i)
        suf_txt = (suf_raw or "").strip().upper().replace(" ", "")
        art_no = f"{base_txt}-{suf_txt}" if suf_txt else base_txt
        return art_no, base_txt, suf_txt

    @staticmethod
    def _parse_art_num(s: str) -> Optional[int]:
        """
        Extrai número inteiro base de "1.620", "2046", "10", "1-A", "1-J", etc.
        Retorna int ou None se não for artigo válido.
        """
        if not s:
            return None
        s = s.strip()
        # Remove sufixo alfabético (A, J, AA, etc.) e ordinal
        s = re.sub(r"-[A-Za-z]+$", "", s)
        s = re.sub(r"[º°]$", "", s)
        s = s.strip()
        if not s:
            return None
        # Remove pontos
        s = s.replace(".", "")
        if not s.isdigit():
            return None
        return int(s)

    @staticmethod
    def _ctx_lines(ctx: Dict[str, Dict[str, str]]) -> List[str]:
        order = ["LIVRO", "TITULO", "SUBTITULO", "CAPITULO", "SECAO", "SUBSECAO"]
        out: List[str] = []
        for k in order:
            v = ctx.get(k) or {}
            num = (v.get("num") or "").strip()
            name = (v.get("name") or "").strip()
            if not num and not name:
                continue
            if name:
                out.append(f"{k} {num} — {name}".strip(" —"))
            else:
                out.append(f"{k} {num}".strip())
        return out

    @classmethod
    def _is_index_start(cls, s: str) -> bool:
        # aceita "ÍNDICE", "**ÍNDICE**", "##### ÍNDICE", "ÍNDICE REMISSIVO", etc.
        t = (s or "").strip()
        t = re.sub(r"^#{1,8}\s*", "", t).strip()
        t = cls._unbold(t)
        t = cls._norm(t)
        return t.startswith("INDICE")

    def build(
        self, doc: MdDoc, *, profile_id: str, out_json_dir: Path, out_rep_dir: Path
    ) -> None:
        md_path = doc.md_path
        stem = doc.stem
        doc_id = f"{profile_id}:{stem}"

        raw_md = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "stem": stem,
            "generated_at": now_utc_iso_z(),
            "sources": {"md": str(md_path)},
            "meta": dict(doc.front or {}),
            "pages_total": len(doc.pages),
            "pages": [
                {"page": p, "text": doc.pages[p]} for p in sorted(doc.pages.keys())
            ],
        }

        sections: List[Dict[str, Any]] = []
        chunks: List[Dict[str, Any]] = []

        section_seq = 0
        chunk_seq = 0

        ctx: Dict[str, Dict[str, str]] = {
            "LIVRO": {},
            "TITULO": {},
            "SUBTITULO": {},
            "CAPITULO": {},
            "SECAO": {},
            "SUBSECAO": {},
        }
        awaiting_name_for: Optional[str] = None
        last_section_idx: Optional[int] = None

        # estado do artigo atual
        cur_art_no: Optional[str] = None
        cur_lines: List[str] = []
        cur_pages: List[int] = []
        cur_start_page: Optional[int] = None
        cur_end_page: Optional[int] = None
        cur_ctx_snapshot: Dict[str, Dict[str, str]] = {}

        # dedup global
        seen_article_ids: set[str] = set()

        def new_section(
            heading_raw: str, heading_canon: str, start_page: int, num: str
        ) -> Dict[str, Any]:
            nonlocal section_seq
            section_seq += 1
            return {
                "section_id": f"{stem}::S{section_seq:03d}",
                "heading_raw": heading_raw,
                "heading_canonical": heading_canon,
                "num": num,
                "start_page": start_page,
                "end_page": start_page,
            }

        def reset_lower_context(kind: str) -> None:
            # reseta contextos abaixo do nível atual
            if kind == "LIVRO":
                ctx["TITULO"] = {}
                ctx["SUBTITULO"] = {}
                ctx["CAPITULO"] = {}
                ctx["SECAO"] = {}
                ctx["SUBSECAO"] = {}
            elif kind == "TITULO":
                ctx["SUBTITULO"] = {}
                ctx["CAPITULO"] = {}
                ctx["SECAO"] = {}
                ctx["SUBSECAO"] = {}
            elif kind == "SUBTITULO":
                ctx["CAPITULO"] = {}
                ctx["SECAO"] = {}
                ctx["SUBSECAO"] = {}
            elif kind == "CAPITULO":
                ctx["SECAO"] = {}
                ctx["SUBSECAO"] = {}
            elif kind == "SECAO":
                ctx["SUBSECAO"] = {}

        def flush_article() -> None:
            nonlocal \
                chunk_seq, \
                cur_art_no, \
                cur_lines, \
                cur_pages, \
                cur_start_page, \
                cur_end_page, \
                cur_ctx_snapshot

            if cur_art_no is None:
                return

            txt = "\n".join([x for x in cur_lines if x is not None]).strip()
            if not txt:
                cur_art_no = None
                cur_lines = []
                cur_pages = []
                cur_start_page = None
                cur_end_page = None
                cur_ctx_snapshot = {}
                return

            anchors: List[str] = []
            for p in cur_pages:
                a = f"[[Pág. {p}]]"
                if a not in anchors:
                    anchors.append(a)

            if anchors and not self._ANCHOR_RE.search(txt):
                txt = (anchors[0] + "\n" + txt).strip()

            chunk_seq += 1
            chunks.append(
                {
                    "chunk_id": f"{stem}::C{chunk_seq:04d}",
                    "section_id": None,
                    "heading_canonical": "ARTIGO",
                    "article_no": cur_art_no,
                    "hierarchy": cur_ctx_snapshot,
                    "text": txt,
                    "page_ref": {
                        "start": cur_start_page or 1,
                        "end": cur_end_page or (cur_start_page or 1),
                    },
                    "anchors": anchors or [f"[[Pág. {cur_start_page or 1}]]"],
                }
            )

            cur_art_no = None
            cur_lines = []
            cur_pages = []
            cur_start_page = None
            cur_end_page = None
            cur_ctx_snapshot = {}

        def begin_article(art_no: str, line_full: str, page_no: int) -> None:
            nonlocal \
                cur_art_no, \
                cur_lines, \
                cur_pages, \
                cur_start_page, \
                cur_end_page, \
                cur_ctx_snapshot

            flush_article()

            cur_art_no = art_no
            cur_lines = []

            cur_ctx_snapshot = {k: dict(v or {}) for k, v in (ctx or {}).items()}

            header = [f"ARTIGO {art_no}"]
            ctx_lines = self._ctx_lines(cur_ctx_snapshot)
            if ctx_lines:
                header.append("")
                header.extend(ctx_lines)
            header.append("")
            cur_lines.extend(header)

            cur_lines.append(f"[[Pág. {page_no}]]")
            cur_pages = [page_no]
            cur_start_page = page_no
            cur_end_page = page_no

            cur_lines.append(line_full.strip())

        def touch_page(page_no: int) -> None:
            nonlocal cur_end_page, cur_pages, cur_lines
            if cur_art_no is None:
                return
            if cur_pages and cur_pages[-1] == page_no:
                return
            cur_pages.append(page_no)
            cur_end_page = page_no
            marker = f"[[Pág. {page_no}]]"
            if not cur_lines or cur_lines[-1].strip() != marker:
                cur_lines.append(marker)

        stop_after_index = False

        for page_no in sorted(doc.pages.keys()):
            if stop_after_index:
                break

            page_text = doc.pages.get(page_no) or ""
            lines = page_text.split("\n")

            touch_page(page_no)

            for ln in lines:
                s = (ln or "").strip()

                # Para no índice (após ter iniciado artigos) e evita arrastar o último artigo
                if self._is_index_start(s) and (
                    cur_art_no is not None or bool(seen_article_ids)
                ):
                    flush_article()
                    stop_after_index = True
                    break

                if not s:
                    if cur_art_no is not None:
                        cur_lines.append("")
                    continue

                # headings markdown (gerado pelo pdf_convert)
                mh = self._MD_HEADING_RE.match(s)
                if mh:
                    htxt = self._clean_heading_text(mh.group(2))
                    key = self._norm(htxt)

                    h_type: Optional[str] = None
                    h_num: str = ""

                    if key.startswith("LIVRO "):
                        h_type = "LIVRO"
                        h_num = htxt.split(" ", 1)[1].strip()
                        ctx["LIVRO"] = {"num": h_num, "name": ""}
                        reset_lower_context("LIVRO")

                    elif key == "TITULO UNICO" or key.startswith("TITULO UNICO"):
                        h_type = "TITULO"
                        h_num = "ÚNICO"
                        ctx["TITULO"] = {"num": h_num, "name": ""}
                        reset_lower_context("TITULO")

                    elif key.startswith("TITULO "):
                        h_type = "TITULO"
                        h_num = htxt.split(" ", 1)[1].strip()
                        ctx["TITULO"] = {"num": h_num, "name": ""}
                        reset_lower_context("TITULO")

                    elif key == "SUBTITULO UNICO" or key.startswith("SUBTITULO UNICO"):
                        h_type = "SUBTITULO"
                        h_num = "ÚNICO"
                        ctx["SUBTITULO"] = {"num": h_num, "name": ""}
                        reset_lower_context("SUBTITULO")

                    elif key.startswith("SUBTITULO "):
                        h_type = "SUBTITULO"
                        h_num = htxt.split(" ", 1)[1].strip()
                        ctx["SUBTITULO"] = {"num": h_num, "name": ""}
                        reset_lower_context("SUBTITULO")

                    elif key == "CAPITULO UNICO" or key.startswith("CAPITULO UNICO"):
                        h_type = "CAPITULO"
                        h_num = "ÚNICO"
                        ctx["CAPITULO"] = {"num": h_num, "name": ""}
                        reset_lower_context("CAPITULO")

                    elif key.startswith("CAPITULO "):
                        h_type = "CAPITULO"
                        h_num = htxt.split(" ", 1)[1].strip()  # aceita VII-A
                        ctx["CAPITULO"] = {"num": h_num, "name": ""}
                        reset_lower_context("CAPITULO")

                    elif key.startswith("SECAO "):
                        h_type = "SECAO"
                        h_num = htxt.split(" ", 1)[1].strip()
                        ctx["SECAO"] = {"num": h_num, "name": ""}
                        reset_lower_context("SECAO")

                    elif key.startswith("SUBSECAO "):
                        h_type = "SUBSECAO"
                        h_num = htxt.split(" ", 1)[1].strip()
                        ctx["SUBSECAO"] = {"num": h_num, "name": ""}

                    if h_type:
                        section = new_section(htxt, h_type, page_no, h_num)
                        sections.append(section)
                        last_section_idx = len(sections) - 1
                        awaiting_name_for = h_type
                    else:
                        awaiting_name_for = None

                    continue

                # nome (linha seguinte em negrito) do heading
                if (
                    awaiting_name_for
                    and last_section_idx is not None
                    and self._is_candidate_name_line(s)
                ):
                    name = self._unbold(s)
                    if awaiting_name_for in ctx:
                        ctx[awaiting_name_for]["name"] = name
                    sections[last_section_idx]["end_page"] = page_no
                    sections[last_section_idx]["name"] = name
                    awaiting_name_for = None
                    continue

                # faixa "Art. X. a Y."
                mr = self._ART_RANGE_RE.match(s)
                if mr:
                    a0 = self._to_int_base(mr.group(1))
                    a1 = self._to_int_base(mr.group(2))
                    tail = (mr.group(3) or "").strip()
                    if a0 <= a1 and (a1 - a0) <= 500:
                        for n in range(a0, a1 + 1):
                            art_base = self._fmt_dot(n)
                            art_no = art_base
                            art_no, art_base, _ = self._canon_article_no(str(n))
                            if art_no in seen_article_ids:
                                continue
                            seen_article_ids.add(art_no)
                            line_full = f"Art. {art_base}. {tail}".strip()
                            begin_article(art_no, line_full, page_no)
                            flush_article()
                        continue

                # Artigo normal
                ma = self._ART_RE.match(s)
                if ma:
                    base_txt = ma.group(1).strip()
                    suf = (ma.group(2) or "").strip().upper().replace(" ", "")
                    base_raw = ma.group(1).strip()
                    suf_raw = ma.group(2) or ""
                    rest = (ma.group(3) or "").strip()

                    art_no = base_txt
                    if suf:
                        art_no = f"{base_txt}-{suf}"
                    art_no, base_txt, suf = self._canon_article_no(base_raw, suf_raw)

                    # repetição do mesmo artigo no fluxo (ex: topo de página)
                    if cur_art_no is not None and art_no == cur_art_no:
                        continue

                    # dedup global (evita duplicado do índice)
                    if art_no in seen_article_ids:
                        if cur_art_no is not None:
                            cur_lines.append(s)
                        continue

                    seen_article_ids.add(art_no)

                    # normaliza linha do artigo: "Art. N." (+ resto)
                    prefix = f"Art. {base_txt}{('-' + suf) if suf else ''}."
                    line_full = (prefix + (" " + rest if rest else "")).strip()

                    begin_article(art_no, line_full, page_no)
                    awaiting_name_for = None
                    continue

                # conteúdo do artigo
                if cur_art_no is not None:
                    cur_lines.append(s)

            # fim for ln

        # flush final caso não tenha parado no índice
        if not stop_after_index:
            flush_article()

        rag = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "stem": stem,
            "generated_at": now_utc_iso_z(),
            "sources": {"md": str(md_path)},
            "meta": dict(doc.front or {}),
            "normalizations": {
                "rules_version": self.RAG_RULES_VERSION,
                "rag_source": "markdown",
            },
            "sections": sections,
            "chunks": chunks,
        }

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        if not chunks:
            errors.append(
                {
                    "code": "NO_CHUNKS",
                    "msg": "Nenhum chunk (artigo) foi gerado.",
                    "details": {},
                }
            )

        for ch in chunks:
            txt = (ch.get("text") or "").strip()
            if not self._ANCHOR_RE.search(txt):
                errors.append(
                    {
                        "code": "MISSING_ANCHOR",
                        "msg": "Chunk sem âncora [[Pág. N]].",
                        "details": {"chunk_id": ch.get("chunk_id")},
                    }
                )

        status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
        qa = {
            "doc_id": doc_id,
            "profile_id": profile_id,
            "stem": stem,
            "generated_at": now_utc_iso_z(),
            "status": status,
            "ingest_to_qdrant_allowed": status in ("PASS", "PASS_WITH_WARNINGS"),
            "checks": {
                "required_sections_expected": ["ARTIGO"],
                "required_sections_found": (["ARTIGO"] if chunks else []),
            },
            "errors": errors,
            "warnings": warnings,
        }

        rep = [
            f"# MD→RAG Report — {stem}",
            "",
            f"- profile: {profile_id}",
            f"- md: {md_path}",
            f"- pages: {len(doc.pages)}",
            f"- sections: {len(sections)}",
            f"- chunks: {len(chunks)}",
            f"- qa.status: {status}",
            "",
        ]
        if errors:
            rep.append("## Errors")
            for e in errors:
                rep.append(f"- {e.get('code')}: {e.get('msg')}")
        if warnings:
            rep.append("## Warnings")
            for w in warnings:
                rep.append(f"- {w.get('code')}: {w.get('msg')}")
        rep_md = "\n".join(rep).strip() + "\n"

        raw_dir = out_json_dir / "raw"
        rag_dir = out_json_dir / "rag"
        qa_dir = out_rep_dir / "qa"
        logs_dir = out_rep_dir / "logs"

        raw_dir.mkdir(parents=True, exist_ok=True)
        rag_dir.mkdir(parents=True, exist_ok=True)
        qa_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        (raw_dir / f"{stem}.raw.json").write_text(
            json.dumps(raw_md, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (rag_dir / f"{stem}.rag.json").write_text(
            json.dumps(rag, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (qa_dir / f"{stem}.qa.json").write_text(
            json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (logs_dir / f"{stem}.md_rag.report.md").write_text(rep_md, encoding="utf-8")


# -----------------------------
# Runner
# -----------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--profiles",
        nargs="+",
        required=True,
        help="Lista de profiles (ex.: bj_juris_stj bj_doutrina bj_leis)",
    )
    ap.add_argument(
        "--limit", type=int, default=0, help="Limita quantidade de MDs (0=sem limite)"
    )
    ap.add_argument(
        "--only-new",
        action="store_true",
        help="Processa apenas MDs novos/alterados (pula se outputs existirem e forem mais novos que o MD).",
    )
    args = ap.parse_args()

    project_root = find_project_root(Path(__file__).resolve())
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    for profile in args.profiles:
        profile_yaml = resolve_profile_yaml(project_root, profile)
        data = load_yaml(profile_yaml)
        profile_id = data.get("profile_id") or data.get("id") or profile

        dirs = resolve_dirs(project_root, data)
        if "md" not in dirs:
            raise SystemExit(f"Profile inválido em {profile_yaml}: precisa dirs.md")

        md_dir = dirs["md"]
        if not md_dir.exists():
            raise SystemExit(f"Diretório MD não encontrado: {md_dir}")

        json_dir = dirs.get("json")
        rep_dir = dirs.get("rep")
        if json_dir is None or rep_dir is None:
            d_json, d_rep = derive_json_rep_from_md(md_dir)
            json_dir = json_dir or d_json
            rep_dir = rep_dir or d_rep

        md_files = sorted(md_dir.rglob("*.md"))
        if args.limit and args.limit > 0:
            md_files = md_files[: args.limit]

        print(f"Profile: {profile_id}")
        print(f"MD (entrada): {md_dir} ({len(md_files)})")
        print(f"JSON (saída): {json_dir}")
        print(f"REPORT (saída): {rep_dir}")

        if profile_id == "bj_juris_stj":
            rules = STJRagRules()
        elif profile_id == "bj_leis":
            rules = LeisRagRules()
        else:
            print(f"[skip] {profile_id}: sem regras MD→RAG definidas ainda.")
            continue

        for md_path in md_files:
            stem = safe_stem(md_path, md_dir)
            if args.only_new:
                if _is_fresh(md_path, stem, json_dir, rep_dir):
                    # opcional: log curto
                    print(f"[skip] {md_path.relative_to(md_dir)} (já atualizado)")
                    continue

            doc = parse_md(md_path, stem=stem)
            rules.build(
                doc, profile_id=profile_id, out_json_dir=json_dir, out_rep_dir=rep_dir
            )
            print(f"[ok] {md_path.relative_to(md_dir)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
