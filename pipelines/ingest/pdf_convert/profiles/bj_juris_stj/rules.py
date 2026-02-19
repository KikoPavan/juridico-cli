#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExtractionMeta:
    pages_total: int
    primary_tool: str = "pymupdf"
    method: str = "text"


@dataclass(frozen=True)
class Evidence:
    page: Optional[int]
    snippet: str


class STJRules:
    """
    Regras EXCLUSIVAS para conversão PDF -> MD (md_only).
    NÃO contém RAG/QA/RAW.
    - limpeza por página
    - metadados
    - front matter
    - correções de cabeçalho (quebras)
    """

    # -----------------------------
    # Rodapé / assinatura STJ
    # -----------------------------
    _FOOTER_START_RE = re.compile(
        r"^\s*Documento\s+eletrônico\s+VDA[0-9A-Z]+\b", re.IGNORECASE
    )
    _FOOTER_LINE_RE = re.compile(
        r"^\s*(?:"
        r"Documento\s+eletrônico\s+VDA[0-9A-Z]+\b.*|"
        r"Signatário\(a\)\s*:\s*.*|"
        r"Assinado\s+em\s*:\s*.*|"
        r"Código\s+de\s+Controle\s+do\s+Documento\s*:\s*.*"
        r")\s*$",
        re.IGNORECASE,
    )
    _FOOTER_SITE_CERT_RE = re.compile(
        r"Documento\s*:\s*\d+\s*-\s*Inteiro\s+Teor\s+do\s+Ac[oó]rd[aã]o\s*-\s*Site\s+certificado\s*-\s*DJe\s*:\s*\d{1,2}/\d{1,2}/\d{4}",
        re.IGNORECASE,
    )
    _FOOTER_PAGE_RE = re.compile(r"Página\s*\d+\s*de\s*\d+", re.IGNORECASE)

    # -----------------------------
    # Labels do cabeçalho
    # -----------------------------
    _LABELS = (
        "RELATOR",
        "RELATORA",
        "AGRAVANTE",
        "AGRAVADO",
        "ADVOGADO",
        "ADVOGADOS",
        "OUTRO NOME",
        "RECORRENTE",
        "RECORRIDO",
        "ASSUNTO",
        "PRESIDENTE DA SESSÃO",
        "SECRETÁRIO",
        "ORIGEM",
        "INTERESSADO",
        "INTERESSADA",
        "IMPETRANTE",
        "IMPETRADO",
        "PACIENTE",
        "EMBARGANTE",
        "EMBARGADO",
        "APELANTE",
        "APELADO",
        "REQUERENTE",
        "REQUERIDO",
        "REQUERIDA",
        "EXEQUENTE",
        "EXECUTADO",
        "EXECUTADA",
        "INTERES.",
    )

    _LABEL_JOIN_RE = re.compile(
        r"(?m)^\s*(" + "|".join(re.escape(x) for x in _LABELS) + r")\s*\n\s*:\s*",
        flags=re.IGNORECASE,
    )

    _INLINE_LABEL_SPLIT_RE = re.compile(
        r"\s+(" + "|".join(re.escape(x) for x in _LABELS) + r")\s*:\s*",
        flags=re.IGNORECASE,
    )

    _RELATOR_LINE_RE = re.compile(r"(?im)^\s*(RELATORA?)\s*:\s*(.+)$")

    _CUT_LABELS = _LABELS
    _RELATOR_CUT_RE = re.compile(
        r"\b(" + "|".join(re.escape(x) for x in _CUT_LABELS) + r")\s*:\s*",
        flags=re.IGNORECASE,
    )

    # -----------------------------
    # Headings (estritas: só se a linha for APENAS o título)
    # -----------------------------
    _HEADING_ONLY_RE = re.compile(
        r"^(?:\*\*)?\s*(?:"
        r"EMENTA|ACÓRDÃO|ACORDAO|RELATÓRIO|RELATORIO|VOTO|É\s+O\s+VOTO|E\s+O\s+VOTO|"
        r"TERMO|TERMO\s+DE\s+JULGAMENTO|AUTUAÇÃO|AUTUACAO|AGRAVO\s+INTERNO|"
        r"CERTIDÃO\s+DE\s+JULGAMENTO|CERTIDAO\s+DE\s+JULGAMENTO|CERTIDAO"
        r")\s*(?:\*\*)?$",
        re.IGNORECASE,
    )

    _SECTION_CANON = {
        "ACORDAO": "ACÓRDÃO",
        "RELATORIO": "RELATÓRIO",
        "AUTUACAO": "AUTUAÇÃO",
        "CERTIDAO": "CERTIDÃO",
        "CERTIDAO DE JULGAMENTO": "CERTIDÃO DE JULGAMENTO",
    }

    # meses PT (normalizados sem acento)
    MONTHS_PT = {
        "janeiro": "01",
        "fevereiro": "02",
        "marco": "03",
        "abril": "04",
        "maio": "05",
        "junho": "06",
        "julho": "07",
        "agosto": "08",
        "setembro": "09",
        "outubro": "10",
        "novembro": "11",
        "dezembro": "12",
    }

    _DJE_RE = re.compile(r"\bDJe\s*:\s*(\d{1,2}/\d{1,2}/\d{4})\b", re.IGNORECASE)

    _BRASILIA_TEXTUAL_DATE_RE = re.compile(
        r"\bBras[ií]lia"
        r"(?:\s*[-–]\s*DF|\s*\(\s*DF\s*\)|\s*,\s*DF)?"
        r"\s*[,–-]?\s*"
        r"(\d{1,2})\s+de\s+([A-Za-zÀ-ÿçÇ]+)\s+de\s+(\d{4})\b",
        re.IGNORECASE,
    )
    _BRASILIA_NUMERIC_DATE_RE = re.compile(
        r"\bBras[ií]lia"
        r"(?:\s*[-–]\s*DF|\s*\(\s*DF\s*\)|\s*,\s*DF)?"
        r"\s*[,–-]?\s*"
        r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        *,
        document_type: str = "base_juridica",
        doc_subtype: str = "jurisprudencia",
        language: str = "pt-BR",
    ) -> None:
        self.document_type = document_type
        self.doc_subtype = doc_subtype
        self.language = language

    # -----------------------------
    # util
    # -----------------------------
    @staticmethod
    def _yaml_quote(s: str) -> str:
        s = (s or "").replace("\\", "\\\\").replace('"', '\\"')
        return f'"{s}"'

    @staticmethod
    def _normalize_newlines(text: str) -> str:
        return (text or "").replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def _normalize_spaces(text: str) -> str:
        lines = [(ln or "").rstrip() for ln in (text or "").split("\n")]
        return "\n".join(lines)

    @staticmethod
    def _strip_accents(s: str) -> str:
        if not s:
            return ""
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )

    @staticmethod
    def _dmy_to_iso(dmy: str) -> str:
        try:
            dt = datetime.strptime(dmy, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return ""

    @staticmethod
    def _is_all_caps_like(s: str) -> bool:
        s2 = re.sub(r"[^A-Za-zÀ-ÿÇÁÉÍÓÚÂÊÔÃÕÜ]", "", s or "")
        return bool(s2) and (s2.upper() == s2) and len(s2) >= 4

    # -----------------------------
    # limpeza rodapé
    # -----------------------------
    def _strip_footer_lines(self, raw: str) -> str:
        text = self._normalize_newlines(raw)
        lines = text.split("\n")

        cut_idx: Optional[int] = None
        for i, ln in enumerate(lines):
            if self._FOOTER_START_RE.match(ln):
                cut_idx = i
                break
        if cut_idx is not None:
            lines = lines[:cut_idx]

        cleaned: List[str] = []
        for ln in lines:
            ln2 = self._FOOTER_SITE_CERT_RE.sub("", ln)
            ln2 = self._FOOTER_PAGE_RE.sub("", ln2)

            if self._FOOTER_LINE_RE.match(ln2):
                continue

            ln2 = ln2.strip()
            if not ln2:
                continue
            cleaned.append(ln2)

        return "\n".join(cleaned)

    # corrige "LABEL \n :" -> "LABEL : "
    def _fix_label_colon_breaks(self, text: str) -> str:
        return self._LABEL_JOIN_RE.sub(lambda m: f"{m.group(1).upper()} : ", text or "")

    # quebra cabeçalho que veio em uma linha só: "... RELATOR : X AGRAVANTE : Y ..."
    def _split_inline_labels(self, text: str) -> str:
        def _repl(m: re.Match) -> str:
            return "\n" + m.group(1).upper() + " : "

        return self._INLINE_LABEL_SPLIT_RE.sub(_repl, text or "")

    # -----------------------------
    # headings (somente linha isolada)
    # -----------------------------
    def _format_section_headings(self, text: str) -> str:
        lines = (text or "").splitlines()
        out: List[str] = []
        for ln in lines:
            s = (ln or "").strip()
            if not s:
                out.append("")
                continue

            # remove bold, se já vier
            m = re.match(r"^\*\*(.+?)\*\*$", s)
            core = (m.group(1) if m else s).strip()

            if self._HEADING_ONLY_RE.match(s):
                key = self._strip_accents(core).upper().strip()
                key = re.sub(r"\s+", " ", key)
                canon = self._SECTION_CANON.get(key, core)
                # garante separação por blocos
                if out and out[-1] != "":
                    out.append("")
                out.append(f"**{canon}**")
                out.append("")
            else:
                out.append(ln)

        # normaliza múltiplas linhas vazias
        norm: List[str] = []
        prev_blank = False
        for x in out:
            if x == "":
                if not prev_blank:
                    norm.append("")
                prev_blank = True
            else:
                norm.append(x)
                prev_blank = False

        return "\n".join(norm).strip()

    # -----------------------------
    # reflow por blocos (mantém cabeçalho com labels em linhas)
    # -----------------------------
    def _reflow_text(self, text: str) -> str:
        lines = (text or "").splitlines()
        out_blocks: List[str] = []
        buf: List[str] = []

        def flush() -> None:
            if not buf:
                return
            out_blocks.append(self._reflow_block(buf))
            buf.clear()

        for ln in lines:
            if (ln or "").strip() == "":
                flush()
                out_blocks.append("")
            else:
                buf.append(ln)
        flush()

        # normaliza múltiplos separadores
        out: List[str] = []
        prev_blank = False
        for b in out_blocks:
            if b == "":
                if not prev_blank:
                    out.append("")
                prev_blank = True
            else:
                out.append(b)
                prev_blank = False

        return "\n".join(out).strip()

    def _reflow_block(self, lines: List[str]) -> str:
        if not lines:
            return ""

        # se o bloco começa com heading isolado em bold, mantém como linha
        if len(lines) == 1:
            return lines[0].strip()

        if len(lines) == 1 and re.match(r"^\*\*.+\*\*$", (lines[0] or "").strip()):
            return (lines[0] or "").strip()

        # bloco com várias labels ":" -> mantém por linha
        colon_count = sum(1 for ln in lines if ":" in (ln or ""))
        if colon_count >= 2 or any(
            self._is_all_caps_like(ln or "") for ln in lines[:3]
        ):
            out2: List[str] = []
            for ln in lines:
                ln2 = (ln or "").strip()
                if not ln2:
                    continue
                out2.append(ln2)
            return "\n".join(out2)

        # caso geral: junta como parágrafo
        return " ".join((ln or "").strip() for ln in lines if (ln or "").strip())

    # -----------------------------
    # API pública do MD-only
    # -----------------------------
    def clean_page_text(self, raw_page_text: str) -> str:
        t = self._normalize_newlines(raw_page_text)
        t = self._strip_footer_lines(t)
        t = self._fix_label_colon_breaks(t)
        t = self._split_inline_labels(t)
        t = self._normalize_spaces(t)
        t = self._format_section_headings(t)
        t = self._reflow_text(t)
        return t

    def strip_repeated_header_block(self, page_text: str) -> str:
        """
        Remove cabeçalho repetido nas páginas 2+.
        """
        txt = self._normalize_newlines(page_text or "")
        lines = txt.split("\n")

        top = "\n".join(lines[:25])
        if not re.search(r"(?im)^\s*RELATORA?\s*:\s*", top):
            return page_text

        for i, ln in enumerate(lines):
            s = (ln or "").strip()
            if re.match(r"(?i)^\*\*(EMENTA|ACÓRDÃO|RELATÓRIO|VOTO|TERMO)\*\*$", s):
                return "\n".join(lines[i:]).lstrip() + "\n"
            if re.match(r"(?i)^(O\s+EXMO\.|Trata-se|Cuida-se|Vistos)", s):
                return "\n".join(lines[i:]).lstrip() + "\n"

        return page_text

    # -----------------------------
    # Metadados
    # -----------------------------
    @staticmethod
    def parse_publication_date_from_filename(stem: str) -> Optional[str]:
        m = re.search(r"(\d{4}-\d{2}-\d{2})$", stem or "")
        return m.group(1) if m else None

    @staticmethod
    def detect_court(text: str) -> str:
        if "Superior Tribunal de Justiça" in (text or "") or "STJ" in (text or ""):
            return "STJ"
        return "NÃO INFORMADO"

    def parse_relator_from_text(self, text: str) -> str:
        m = self._RELATOR_LINE_RE.search(text or "")
        if not m:
            return "NÃO INFORMADO"
        rel = (m.group(2) or "").strip()
        if not rel:
            return "NÃO INFORMADO"

        cut = self._RELATOR_CUT_RE.search(rel)
        if cut:
            rel = rel[: cut.start()].strip()

        rel = re.sub(r"\s{2,}", " ", rel).strip(" -–—\t")
        return rel if rel else "NÃO INFORMADO"

    @staticmethod
    def parse_class_from_text(text: str) -> str:
        lines = [line.strip() for line in (text or "").split("\n") if line.strip()]
        if not lines:
            return "NÃO INFORMADO"
        first = lines[0]
        cut = STJRules._RELATOR_CUT_RE.search(first)
        if cut:
            first = first[: cut.start()].strip()
        return first if first else "NÃO INFORMADO"

    def parse_judgment_date_from_text(self, text: str) -> str:
        txt = text or ""
        m = self._BRASILIA_TEXTUAL_DATE_RE.search(txt)
        if m:
            day = int(m.group(1))
            mon_raw = self._strip_accents((m.group(2) or "").lower())
            year = m.group(3)
            mon = self.MONTHS_PT.get(mon_raw)
            if mon:
                return f"{year}-{mon}-{day:02d}"

        m2 = self._BRASILIA_NUMERIC_DATE_RE.search(txt)
        if m2:
            day = int(m2.group(1))
            mon = int(m2.group(2))
            year = m2.group(3)
            if 1 <= day <= 31 and 1 <= mon <= 12:
                return f"{year}-{mon:02d}-{day:02d}"

        return ""

    def parse_publication_date_from_text(self, raw_text: str) -> str:
        lines = self._normalize_newlines(raw_text or "").split("\n")

        candidates: List[tuple[str, int]] = []
        for ln in lines:
            m = self._DJE_RE.search(ln)
            if not m:
                continue
            dmy = m.group(1)
            weight = 1
            lnl = (ln or "").lower()
            if "documento" in lnl:
                weight += 3
            if "site certificado" in lnl:
                weight += 3
            if "inteiro teor" in lnl:
                weight += 1
            candidates.append((dmy, weight))

        if not candidates:
            return ""

        score: Dict[str, int] = {}
        for dmy, w in candidates:
            score[dmy] = score.get(dmy, 0) + w

        best_dmy = max(score.items(), key=lambda kv: kv[1])[0]
        return self._dmy_to_iso(best_dmy)

    def extract_metadata(
        self,
        *,
        full_text: str,
        stem: str,
        raw_full_text: Optional[str] = None,
    ) -> Dict[str, str]:
        court = self.detect_court(full_text)
        class_ = self.parse_class_from_text(full_text)
        relator = self.parse_relator_from_text(full_text)

        judgment_date = self.parse_judgment_date_from_text(full_text)
        if not judgment_date and raw_full_text:
            judgment_date = self.parse_judgment_date_from_text(raw_full_text)

        publication_date = self.parse_publication_date_from_filename(stem) or ""
        if not publication_date:
            publication_date = self.parse_publication_date_from_text(
                raw_full_text or ""
            )

        return {
            "document_type": self.document_type,
            "doc_subtype": self.doc_subtype,
            "court": court,
            "class": class_,
            "relator": relator,
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "language": self.language,
        }

    def build_front_matter_str(
        self,
        *,
        meta: Dict[str, str],
        pages_total: int,
        source_pdf: str,
        extraction: Optional[ExtractionMeta] = None,
    ) -> str:
        return (
            "---\n"
            f"document_type: {meta.get('document_type', self.document_type)}\n"
            f"doc_subtype: {meta.get('doc_subtype', self.doc_subtype)}\n"
            f"source_pdf: {source_pdf}\n"
            f"court: {meta.get('court', 'NÃO INFORMADO')}\n"
            f"class: {self._yaml_quote(meta.get('class', 'NÃO INFORMADO'))}\n"
            f"relator: {self._yaml_quote(meta.get('relator', 'NÃO INFORMADO'))}\n"
            f"judgment_date: {self._yaml_quote(meta.get('judgment_date', ''))}\n"
            f"publication_date: {self._yaml_quote(meta.get('publication_date', ''))}\n"
            f"language: {meta.get('language', self.language)}\n"
            "extraction:\n"
            f"  method: {(extraction.method if extraction else 'text')}\n"
            f"  pages_total: {pages_total}\n"
            f"  primary_tool: {(extraction.primary_tool if extraction else 'pymupdf')}\n"
            "---\n"
        )


RULES = STJRules()
