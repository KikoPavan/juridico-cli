# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LeisMdRules:
    """
    Regras SOMENTE para PDF→Markdown (leis).
    - Remove cabeçalho/rodapé do "print do site"
    - Corrige artefatos do ordinal (º)
    - Formata títulos (LIVRO/TÍTULO/CAPÍTULO/Seção) como headings em negrito
    """

    RULES_VERSION: str = "bj-leis-md-v3"

    _HYPHEN_RE = re.compile(r"(\w)-\n(\w)", re.UNICODE)
    _MANY_BLANKS_RE = re.compile(r"\n{3,}", re.UNICODE)

    # cabeçalho típico do "print" (data/hora + nome do documento)
    _HEADER_RE = re.compile(r"^\d{2}/\d{2}/\d{2},\s*\d{2}:\d{2}\s+L\d+.*$", re.UNICODE)

    # rodapé típico: URL (com ou sem "1/186")
    _FOOTER_URL_RE = re.compile(
        r"^https?://\S+(?:\s+\d+/\d+)?\s*$", re.IGNORECASE | re.UNICODE
    )

    # linha solta "o" (artefato comum do ordinal º)
    _LONE_O_RE = re.compile(r"^\s*o\s*$", re.IGNORECASE | re.UNICODE)

    # anchors do seu pipeline
    _ANCHOR_RE = re.compile(r"^\s*\[\[Pág\.\s*\d+\]\]\s*$", re.IGNORECASE | re.UNICODE)

    # match roman
    _ROMAN_RE = re.compile(r"^[IVXLCDM]+$", re.IGNORECASE)

    # --- Regex headings (LeisMdRules) ---
    # Observação: key já vem normalizado (sem acento, uppercase) via _norm_key()

    _H_LIVRO = re.compile(r"^LIVRO\s+([IVXLCDM]+)$", re.IGNORECASE)

    _H_TITULO_UNICO = re.compile(r"^TITULO\s+UNICO$", re.IGNORECASE)
    _H_TITULO = re.compile(r"^TITULO\s+([IVXLCDM]+)$", re.IGNORECASE)

    _H_SUBTITULO = re.compile(r"^SUBTITULO\s+([IVXLCDM]+)$", re.IGNORECASE)

    # CAPÍTULO VII-A (suporta sufixo)
    _H_CAP = re.compile(r"^CAPITULO\s+([IVXLCDM]+(?:-[A-Z])?)$", re.IGNORECASE)
    _H_CAP_UNICO = re.compile(r"^CAPITULO\s+UNICO$", re.IGNORECASE)

    # Seção / Subseção (inclui ÚNICA)
    _H_SECAO_UNICA = re.compile(r"^SECAO\s+UNICA$", re.IGNORECASE)
    _H_SECAO = re.compile(r"^SECAO\s+([IVXLCDM]+(?:-[A-Z])?)$", re.IGNORECASE)

    _H_SUBSECAO_UNICA = re.compile(r"^SUBSECAO\s+UNICA$", re.IGNORECASE)
    _H_SUBSECAO = re.compile(r"^SUBSECAO\s+([IVXLCDM]+(?:-[A-Z])?)$", re.IGNORECASE)

    @staticmethod
    def _strip_accents(s: str) -> str:
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s or "")
            if unicodedata.category(c) != "Mn"
        )

    @classmethod
    def _norm_key(cls, s: str) -> str:
        s2 = cls._strip_accents((s or "").strip())
        s2 = re.sub(r"\s+", " ", s2)
        return s2.upper().strip()

    @staticmethod
    def _already_bold(s: str) -> bool:
        s2 = (s or "").strip()
        return s2.startswith("**") and s2.endswith("**") and len(s2) >= 4

    @staticmethod
    def _wrap_bold(s: str) -> str:
        s2 = (s or "").strip()
        if not s2:
            return s2
        if LeisMdRules._already_bold(s2):
            return s2
        return f"**{s2}**"

    @staticmethod
    def _is_candidate_title_line(s: str) -> bool:
        """
        Linha "nome" de seção/capítulo etc. Ex.: "DAS PESSOAS", "Da Personalidade..."
        Mantém conservador para não boldar corpo de artigos.
        """
        t = (s or "").strip()
        if not t:
            return False
        if t.startswith("Art.") or t.startswith("§") or t.startswith("Parágrafo"):
            return False
        if "http://" in t.lower() or "https://" in t.lower():
            return False
        if any(ch.isdigit() for ch in t):
            return False
        if t.endswith(".") or t.endswith(";") or t.endswith(":"):
            return False
        if len(t) > 90:
            return False

        # ALL CAPS (com acentos) costuma ser título
        letters = [c for c in t if c.isalpha()]
        if letters:
            upp = sum(1 for c in letters if c.isupper())
            if upp / max(1, len(letters)) >= 0.85:
                return True

        # Title case típico (Da/Do/Dos/Das/De)
        starters = ("Da ", "Do ", "Dos ", "Das ", "De ", "Del ", "Dela ")
        if t.startswith(starters):
            return True

        return False

    @classmethod
    def _format_headings(cls, lines: list[str]) -> list[str]:
        out: list[str] = []
        bold_next_name = False

        for ln in lines:
            s = (ln or "").strip()
            if not s:
                out.append("")
                continue

            # --- Dentro do loop onde você processa "s" ---
            # ... (mantém seu trecho de âncora e key = cls._norm_key(s))
            # preserva âncora caso exista no conteúdo (normalmente não existe aqui)
            if cls._ANCHOR_RE.match(s):
                out.append(s)
                bold_next_name = False
                continue

            key = cls._norm_key(s)

            m = cls._H_LIVRO.match(key)
            if m:
                rn = m.group(1).upper()
                out.append(f"# **LIVRO {rn}**")
                bold_next_name = True
                continue

            m = cls._H_TITULO_UNICO.match(key)
            if m:
                out.append("## **TÍTULO ÚNICO**")
                bold_next_name = True
                continue

            m = cls._H_TITULO.match(key)
            if m:
                rn = m.group(1).upper()
                out.append(f"## **TÍTULO {rn}**")
                bold_next_name = True
                continue

            m = cls._H_SUBTITULO.match(key)
            if m:
                rn = m.group(1).upper()
                out.append(f"### **SUBTÍTULO {rn}**")
                bold_next_name = True
                continue

            m = cls._H_CAP_UNICO.match(key)
            if m:
                out.append("#### **CAPÍTULO ÚNICO**")
                bold_next_name = True
                continue

            m = cls._H_CAP.match(key)
            if m:
                rn = m.group(1).upper()  # aqui pode vir "VII-A"
                out.append(f"#### **CAPÍTULO {rn}**")
                bold_next_name = True
                continue

            m = cls._H_SECAO_UNICA.match(key)
            if m:
                out.append("##### **Seção Única**")
                bold_next_name = True
                continue

            m = cls._H_SECAO.match(key)
            if m:
                rn = m.group(1).upper()
                out.append(f"##### **Seção {rn}**")
                bold_next_name = True
                continue

            m = cls._H_SUBSECAO_UNICA.match(key)
            if m:
                out.append("###### **Subseção Única**")
                bold_next_name = True
                continue

            m = cls._H_SUBSECAO.match(key)
            if m:
                rn = m.group(1).upper()
                out.append(f"###### **Subseção {rn}**")
                bold_next_name = True
                continue

            # após um heading, bolda a próxima linha "nome" (se for candidata)
            if bold_next_name and cls._is_candidate_title_line(s):
                out.append(cls._wrap_bold(s))
                bold_next_name = False
                continue

            # fallback: bold conservador para linhas que claramente são títulos
            if cls._is_candidate_title_line(s):
                out.append(cls._wrap_bold(s))
            else:
                out.append(s)

            bold_next_name = False if s else bold_next_name

        return out

    def clean_page_text(
        self, text: str, *, page_no: int, pdf_path: Optional[Path] = None
    ) -> str:
        t = (text or "").replace("\x00", "")
        t = t.replace("\r\n", "\n").replace("\r", "\n")

        # junta palavras quebradas por hífen no fim da linha
        t = self._HYPHEN_RE.sub(r"\1\2", t)

        # filtra cabeçalho/rodapé e artefatos
        kept: list[str] = []
        for ln in t.split("\n"):
            s = (ln or "").strip()
            if not s:
                kept.append("")
                continue
            if self._HEADER_RE.match(s):
                continue
            if self._FOOTER_URL_RE.match(s):
                continue
            if self._LONE_O_RE.match(s):
                continue
            kept.append(ln.rstrip())

        # normaliza "Art. N " -> "Art. Nº " quando NÃO houver ponto após o número
        # Ex.: "Art. 1 Toda..." -> "Art. 1º Toda..."
        t2 = "\n".join(kept)
        t2 = re.sub(r"(?m)\bArt\.\s*(\d+)(?!\.)\s+", r"Art. \1º ", t2)

        # colapsa espaços repetidos e excesso de linhas em branco
        t2 = "\n".join([ln.rstrip() for ln in t2.split("\n")])
        t2 = re.sub(r"[ \t]{2,}", " ", t2)
        t2 = self._MANY_BLANKS_RE.sub("\n\n", t2)

        # aplica formatação de headings/títulos
        lines = t2.split("\n")
        lines = self._format_headings(lines)

        return "\n".join(lines).strip()

    def front_matter(
        self, *, profile_id: str, pdf_path: Path, pages_total: int
    ) -> Dict[str, Any]:
        return {
            "profile_id": profile_id,
            "source_pdf": pdf_path.name,
            "pages_total": pages_total,
            "rules_version": self.RULES_VERSION,
            "document_type": "lei",
        }


RULES = LeisMdRules()
