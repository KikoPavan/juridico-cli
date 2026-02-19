#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, Optional

FRONT_RE = re.compile(r"(?s)\A---\n(.*?)\n---\n", re.IGNORECASE)

# -----------------------------
# Artigos
# -----------------------------

# Detecta linha de artigo no início da linha (aceita Art / Art.)
ART_LINE_RE = re.compile(
    r"""
    ^(?P<indent>\s*)
    Art\.?\s*
    (?P<num>\d{1,3}(?:\.\d{3})*|\d+)
    \s*(?P<suffix>-\s*[A-Za-z]{1,2})?
    (?P<tail>.*)$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Ordinal logo após o número/sufixo (com ou sem espaço), antes do resto.
ORDINAL_PREFIX_RE = re.compile(r"""^\s*(?:º|°|ª|o|O)\s*\.?\s*""", re.VERBOSE)

# Expansão de faixa:
# Ex: "Art. 1.620. a 1.629. (Revogados...) Vigência"
# Aceita conectores: a | à | - | – | —
ART_RANGE_RE = re.compile(
    r"""
    ^(?P<indent>\s*)
    Art\.?\s*
    (?P<start>\d{1,3}(?:\.\d{3})*|\d+)
    (?:\s*(?:º|°|ª|o|O))?
    \s*\.?\s*
    (?:a|à|-|–|—)\s*
    (?P<end>\d{1,3}(?:\.\d{3})*|\d+)
    \s*\.?\s*
    (?P<rest>.*)$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# -----------------------------
# Headings (estrutura) + nomes
# -----------------------------

_MD_HEADING_BOLD_RE = re.compile(r"^(#{1,8})\s*\*\*(.+?)\*\*\s*$")
_BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*$")
_PAGE_ANCHOR_RE = re.compile(r"^\[\[Pág\.\s*\d+\]\]\s*$", re.IGNORECASE)
_ART_PREFIX_RE = re.compile(r"^Art\.?\s*\d", re.IGNORECASE)
_PAR_PREFIX_RE = re.compile(r"^(§|Parágrafo)", re.IGNORECASE)


def iter_md_files(inp: Path) -> Iterable[Path]:
    inp = inp.resolve()
    if inp.is_file():
        if inp.suffix.lower() != ".md":
            raise SystemExit(f"Entrada não é .md: {inp}")
        return [inp]
    if inp.is_dir():
        return sorted(inp.rglob("*.md"))
    raise SystemExit(f"Caminho inválido: {inp}")


def _art_to_int(s: str) -> int:
    # "1.620" -> 1620 ; "10" -> 10
    return int((s or "").replace(".", "").strip())


def _format_art(n: int) -> str:
    # 1620 -> "1.620" ; 2046 -> "2.046" ; 999 -> "999"
    return f"{n:,}".replace(",", ".") if n >= 1000 else str(n)


def _norm_suffix(suffix_raw: str) -> str:
    if not suffix_raw:
        return ""
    s = suffix_raw.strip()
    if not s:
        return ""
    # "- a" -> "-A"
    s = s.replace(" ", "")
    if not s.startswith("-"):
        s = "-" + s
    return s.upper()


def expand_article_range_line(line: str) -> Optional[list[str]]:
    m = ART_RANGE_RE.match(line)
    if not m:
        return None

    indent = m.group("indent") or ""
    start_s = (m.group("start") or "").strip()
    end_s = (m.group("end") or "").strip()
    rest = (m.group("rest") or "").rstrip()

    try:
        a = _art_to_int(start_s)
        b = _art_to_int(end_s)
    except Exception:
        return None

    if a <= 0 or b <= 0 or b < a:
        return None

    # Evita explosão acidental em ranges absurdos
    if (b - a) > 5000:
        return None

    # Limpa "rest" se começar com ponto
    rest2 = rest.lstrip()
    if rest2.startswith("."):
        rest2 = rest2[1:].lstrip()

    out: list[str] = []
    for n in range(a, b + 1):
        art_txt = _format_art(n)
        if rest2:
            out.append(f"{indent}Art. {art_txt}. {rest2}".rstrip())
        else:
            out.append(f"{indent}Art. {art_txt}.".rstrip())
    return out


def normalize_article_line(line: str) -> str:
    m = ART_LINE_RE.match(line)
    if not m:
        return line

    indent = m.group("indent") or ""
    num_raw = (m.group("num") or "").strip()
    suffix_raw = (m.group("suffix") or "") or ""
    tail = m.group("tail") or ""

    # Canonicaliza número (1597 -> 1.597)
    try:
        num_i = _art_to_int(num_raw)
        num = _format_art(num_i)
    except Exception:
        # se por algum motivo não converter, mantém bruto
        num = num_raw

    suffix = _norm_suffix(suffix_raw)

    # Remove ordinal (º/°/o) do começo do tail (se existir)
    tail2 = ORDINAL_PREFIX_RE.sub("", tail, count=1)

    # Remove ponto isolado no começo do tail
    t = tail2.lstrip()
    if t.startswith("."):
        t = t[1:].lstrip()

    if t:
        return f"{indent}Art. {num}{suffix}. {t}".rstrip()
    return f"{indent}Art. {num}{suffix}.".rstrip()


def _is_structure_heading_line(line: str) -> bool:
    m = _MD_HEADING_BOLD_RE.match((line or "").strip())
    if not m:
        return False
    core = (m.group(2) or "").strip()
    up = core.upper()
    return (
        up.startswith("LIVRO")
        or up.startswith("TÍTULO")
        or up.startswith("TITULO")
        or up.startswith("SUBTÍTULO")
        or up.startswith("SUBTITULO")
        or up.startswith("CAPÍTULO")
        or up.startswith("CAPITULO")
        or up.startswith("SEÇÃO")
        or up.startswith("SECAO")
        or up.startswith("SUBSEÇÃO")
        or up.startswith("SUBSECAO")
    )


def _is_bold_only_line(s: str) -> bool:
    return bool(_BOLD_ONLY_RE.match((s or "").strip()))


def _is_name_candidate_line(s: str) -> bool:
    t = (s or "").strip()
    if not t:
        return False
    if t.startswith("#"):
        return False
    if _PAGE_ANCHOR_RE.match(t):
        return False
    if _ART_PREFIX_RE.match(t) or _PAR_PREFIX_RE.match(t):
        return False
    # nomes de heading não devem ter dígitos (evita capturar texto de artigo)
    if any(ch.isdigit() for ch in t):
        return False
    if len(t) > 140:
        return False
    return True


def enforce_heading_names_bold(body: str) -> str:
    """
    Garante que, após headings estruturais (LIVRO/TÍTULO/SUBTÍTULO/CAPÍTULO/Seção/Subseção),
    a(s) linha(s) de nome venham em negrito.

    - Agora aceita nome mesmo se houver linhas em branco entre heading e nome (ex.: "Disposições Gerais").
    - Não inventa nome se não existir.
    """
    lines = (body or "").splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        ln = lines[i]
        out.append(ln)

        if not _is_structure_heading_line(ln):
            i += 1
            continue

        j = i + 1
        if j >= len(lines):
            i += 1
            continue

        # ✅ NOVO: preserva e pula linhas em branco logo após o heading
        while j < len(lines) and (lines[j] or "").strip() == "":
            out.append(lines[j])
            j += 1

        if j >= len(lines):
            i += 1
            continue

        # Se a próxima linha já é o nome em negrito, ok
        if _is_bold_only_line(lines[j]):
            i += 1
            continue

        # Coleta 1+ linhas candidatas de nome (até primeira quebra/linha não-candidata)
        name_parts: list[str] = []
        k = j
        while k < len(lines):
            t = (lines[k] or "").strip()
            if not t:
                break
            if not _is_name_candidate_line(t):
                break
            if t.startswith("#"):
                break
            name_parts.append(t)
            k += 1

        if name_parts:
            out.append("**" + " ".join(name_parts).strip() + "**")
            i = k
            continue

        i += 1

    return "\n".join(out).rstrip() + "\n"


def normalize_body(body: str) -> str:
    out_lines: list[str] = []
    for line in body.splitlines():
        # 1) Expande faixa se existir
        expanded = expand_article_range_line(line)
        if expanded is not None:
            out_lines.extend(expanded)
            continue

        # 2) Normaliza ordinal/pontuação + canonicaliza número do artigo
        out_lines.append(normalize_article_line(line))

    norm = "\n".join(out_lines).rstrip() + "\n"

    # 3) Garante nomes de headings em negrito (Seção/Subseção etc.)
    norm = enforce_heading_names_bold(norm)
    return norm


def normalize_md_text(text: str) -> str:
    m = FRONT_RE.search(text)
    if not m:
        return normalize_body(text)
    front = text[: m.end()]
    body = text[m.end() :]
    return front + normalize_body(body)


def write_output(
    src: Path, content: str, *, inplace: bool, out: Optional[Path], base_in: Path
) -> None:
    if inplace:
        src.write_text(content, encoding="utf-8")
        return

    if out is None:
        raise SystemExit(
            "Use --inplace para salvar no mesmo local (ou --out <dir|arquivo>)."
        )

    out = out.resolve()
    if out.is_dir() or str(out).endswith(("/", "\\")):
        out.mkdir(parents=True, exist_ok=True)
        rel = (
            src.resolve().relative_to(base_in.resolve())
            if base_in.is_dir()
            else Path(src.name)
        )
        dst = (out / rel).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
        return

    dst = out
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in", dest="inp", required=True, help="Arquivo .md ou diretório contendo .md"
    )
    ap.add_argument(
        "--inplace", action="store_true", help="Sobrescreve os arquivos no mesmo local"
    )
    ap.add_argument(
        "--out", default=None, help="Diretório/arquivo de saída (se não usar --inplace)"
    )
    args = ap.parse_args()

    inp = Path(args.inp).resolve()
    out = Path(args.out).resolve() if args.out else None

    files = list(iter_md_files(inp))
    if not files:
        raise SystemExit("Nenhum .md encontrado.")

    base_in = inp if inp.is_dir() else inp.parent

    for md in files:
        txt = md.read_text(encoding="utf-8", errors="replace")
        norm = normalize_md_text(txt)
        write_output(md, norm, inplace=args.inplace, out=out, base_in=base_in)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
