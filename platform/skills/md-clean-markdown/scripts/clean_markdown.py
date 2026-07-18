#!/usr/bin/env python3
"""
md-clean-markdown · clean_markdown.py
======================================
Limpa e normaliza um arquivo Markdown bruto.

Agnóstico de domínio: funciona para relatórios, manuais, artigos,
formulários e qualquer documento Markdown textual.

Não interpreta, classifica nem reescreve o conteúdo.

Uso:
    python clean_markdown.py --input DOC.md --output DOC_LIMPO.md [opções]

Opções:
    --input PATH        Arquivo .md de entrada (obrigatório)
    --output PATH       Arquivo .md limpo de saída (obrigatório)
    --max-blank N       Máximo de linhas em branco consecutivas (padrão: 2)
    --no-markers        Não preservar marcadores [[Pág. N]] e <!-- page N -->
    --verbose           Exibir log de operações no stderr
    --report            Gerar cleaning_report.md junto ao output
"""

import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Reuse the canonical judicial locator parser/serializer used by pdf-to-md.
_project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_project_root / "packages" / "shared-llm"))

import judicial_locator

# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_INPUT_ERROR = 1
EXIT_PROCESS_ERROR = 2
EXIT_WRITE_ERROR = 3

OUTPUT_ENCODING = "utf-8"

TYPOGRAPHIC_LIGATURES = str.maketrans(
    {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
)

# Regex para marcadores de página (gerados por pdf-to-md)
# Formato primário: [[Pág. N]] — output real de pdf-to-md
# Formato legado:   <!-- page N --> e variantes — compatibilidade retroativa
PAGE_MARKER_RE = re.compile(
    r"\[\[judicial_locator:[^\]]*\]\]"
    r"|\[\[Pág\.\s*\d+\]\]"
    r"|<!--\s*page\s+\d+(\s*:\s*(empty|extraction_failed|scanned_no_ocr))?\s*-->"
)


# ---------------------------------------------------------------------------
# Estatísticas de limpeza
# ---------------------------------------------------------------------------
@dataclass
class CleanStats:
    lines_in: int = 0
    lines_out: int = 0
    trailing_ws_fixed: int = 0
    blank_collapsed: int = 0
    bullets_normalized: int = 0
    separators_normalized: int = 0
    headings_fixed: int = 0
    decorative_removed: int = 0
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Isolamento de blocos de código
# ---------------------------------------------------------------------------
def _extract_code_blocks(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    """
    Substitui blocos de código por placeholders únicos.
    Retorna (linhas modificadas, mapa placeholder→conteúdo original).
    """
    result: list[str] = []
    blocks: dict[str, str] = {}
    inside = False
    fence_char = ""
    buffer: list[str] = []
    block_idx = 0

    for line in lines:
        stripped = line.rstrip()
        if not inside:
            # Detectar abertura de bloco
            m = re.match(r"^(```|~~~)", stripped)
            if m:
                inside = True
                fence_char = m.group(1)
                buffer = [line]
            else:
                result.append(line)
        else:
            buffer.append(line)
            # Detectar fechamento com o mesmo fence
            if stripped.startswith(fence_char) and stripped == fence_char:
                placeholder = f"__CODE_BLOCK_{block_idx}__"
                blocks[placeholder] = "".join(buffer)
                result.append(placeholder + "\n")
                block_idx += 1
                buffer = []
                inside = False

    # Bloco não fechado (malformado): tratar como texto normal
    if buffer:
        result.extend(buffer)

    return result, blocks


def _restore_code_blocks(lines: list[str], blocks: dict[str, str]) -> list[str]:
    """Restaura os placeholders com o conteúdo original dos blocos."""
    result: list[str] = []
    for line in lines:
        key = line.strip()
        if key in blocks:
            # Restaurar as linhas originais do bloco
            result.extend(blocks[key].splitlines(keepends=True))
        else:
            result.append(line)
    return result


def _normalize_typographic_ligatures(text: str) -> str:
    """Expand known ligatures before line-oriented structural cleaning."""
    return text.translate(TYPOGRAPHIC_LIGATURES)


def _recompose_hyphenated_words(lines: list[str]) -> list[str]:
    """Join words split by a line-ending hyphen and lowercase continuation."""
    result: list[str] = []
    index = 0

    while index < len(lines):
        current = lines[index]
        index += 1
        while index < len(lines):
            following = lines[index]
            current_body = current.rstrip("\r\n")
            following_body = following.rstrip("\r\n")
            if (
                re.search(r"[^\W\d_]-$", current_body, flags=re.UNICODE)
                and re.match(r"^[^\W\d_]", following_body, flags=re.UNICODE)
                and following_body[0].islower()
            ):
                newline = "\n" if following.endswith(("\n", "\r")) else ""
                current = current_body[:-1] + following_body + newline
                index += 1
                continue
            break

        result.append(current)

    return result


_STRUCTURAL_LINE_RE = re.compile(
    r"^(?:"
    r"\s*$"
    r"|\s{4,}\S"
    r"|\s{0,3}(?:#{1,6}\s*|[-+*]\s+|\d+[.)]\s+|>\s*|```|~~~)"
    r"|\s{0,3}(?:---+|___+|\*\*\*+)\s*$"
    r"|\s*\|"
    r"|__CODE_BLOCK_\d+__\s*$"
    r")"
)


def _is_structural_line(line: str) -> bool:
    return bool(_STRUCTURAL_LINE_RE.match(line)) or _is_page_marker(line)


def _recompose_prose_lines(lines: list[str]) -> list[str]:
    """Join prose fragments without crossing Markdown structural boundaries."""
    result: list[str] = []
    index = 0

    while index < len(lines):
        current = lines[index]
        index += 1
        while index < len(lines):
            following = lines[index]
            current_body = current.rstrip("\r\n")
            following_body = following.rstrip("\r\n")
            if (
                not _is_structural_line(current_body)
                and not _is_structural_line(following_body)
                and not re.search(r"[.!?;:…—–-][\"')\]]*$", current_body.rstrip())
                and re.match(r"^[a-zà-öø-ÿ]", following_body)
            ):
                newline = "\n" if following.endswith(("\n", "\r")) else ""
                current = current_body.rstrip() + " " + following_body.lstrip() + newline
                index += 1
                continue
            break

        result.append(current)

    return result


# ---------------------------------------------------------------------------
# Regras de limpeza (aplicadas por linha)
# ---------------------------------------------------------------------------

def _fix_trailing_whitespace(line: str, stats: CleanStats) -> str:
    """Regra 2: remove trailing whitespace, exceto quebra forçada (exatamente 2 espaços finais)."""
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line
    # Exactly 2 trailing spaces = Markdown forced line break — preserve.
    # 3+ trailing spaces are accidental and must be stripped.
    if body.endswith("  ") and not body.endswith("   "):
        return line
    stripped = body.rstrip(" \t")
    result = stripped + newline
    if result != line:
        stats.trailing_ws_fixed += 1
    return result


def _fix_heading_space(line: str, stats: CleanStats) -> str:
    """Regra 4: garante exatamente 1 espaço após os # do heading."""
    m = re.match(r"^(#{1,6})([ \t]*)(\S)", line)
    if m:
        hashes, spaces, first_char = m.group(1), m.group(2), m.group(3)
        if spaces != " ":
            rest = line[len(hashes) + len(spaces):]
            newline = "\n" if line.endswith("\n") else ""
            fixed = hashes + " " + rest.rstrip("\n") + newline
            stats.headings_fixed += 1
            return fixed
    return line


def _fix_bullet(line: str, stats: CleanStats) -> str:
    """Regra 5: normaliza * e + como bullet para -."""
    m = re.match(r"^([ \t]*)([*+]) (.+)", line)
    if m:
        indent, _bullet, content = m.group(1), m.group(2), m.group(3)
        newline = "\n" if line.endswith("\n") else ""
        fixed = indent + "- " + content.rstrip("\n") + newline
        stats.bullets_normalized += 1
        return fixed
    return line


_HR_PATTERNS = [
    re.compile(r"^[ \t]*(\*[ \t]*){3,}[ \t]*$"),   # *** ou * * *
    re.compile(r"^[ \t]*(_[ \t]*){3,}[ \t]*$"),     # ___ ou _ _ _
    re.compile(r"^[ \t]*(=[ \t]*){3,}[ \t]*$"),     # === ou = = =
    re.compile(r"^[ \t]*(-[ \t]*){4,}[ \t]*$"),     # ---- (4+ traços com espaços)
]


def _fix_horizontal_rule(line: str, stats: CleanStats) -> str:
    """Regra 6: normaliza variantes de <hr> para ---."""
    stripped = line.rstrip("\n").rstrip()
    for pattern in _HR_PATTERNS:
        if pattern.match(stripped):
            newline = "\n" if line.endswith("\n") else ""
            stats.separators_normalized += 1
            return "---" + newline
    return line


_DECORATIVE_RE = re.compile(r"^([.,:;!?~`@#$%^&=|])\1{3,}$")


def _remove_decorative_line(line: str, stats: CleanStats) -> str | None:
    """Regra 8: remove linhas de pontuação decorativa pura."""
    stripped = line.strip()
    if _DECORATIVE_RE.match(stripped):
        stats.decorative_removed += 1
        return None  # sinaliza remoção
    return line


def _is_page_marker(line: str) -> bool:
    return bool(PAGE_MARKER_RE.search(line))


# ---------------------------------------------------------------------------
# Pipeline de limpeza
# ---------------------------------------------------------------------------
def clean_lines(
    lines: list[str],
    max_blank: int,
    preserve_markers: bool,
    stats: CleanStats,
    verbose: bool,
) -> list[str]:
    """
    Aplica todas as regras de limpeza à lista de linhas.
    Não toca em blocos de código (já isolados antes desta função).
    """
    result: list[str] = []
    blank_run = 0

    for raw_line in lines:
        line = raw_line

        # Placeholder de bloco de código — passar direto
        if re.match(r"^__CODE_BLOCK_\d+__\n?$", line):
            blank_run = 0
            result.append(line)
            continue

        # Marcadores de página — preservar intactos
        if preserve_markers and _is_page_marker(line):
            blank_run = 0
            result.append(line)
            continue

        # Linha em branco
        if not line.strip():
            blank_run += 1
            if blank_run <= max_blank:
                result.append("\n")
            else:
                stats.blank_collapsed += (1 if blank_run == max_blank + 1 else 0)
                if verbose and blank_run == max_blank + 1:
                    print(f"  [clean] colapso de linhas em branco", file=sys.stderr)
            continue
        # Aplicar regras em ordem (blank_run ainda NÃO resetado)
        # Separadores ANTES de bullets: "* * *" deve virar "---", não "- * *"
        line = _fix_trailing_whitespace(line, stats)
        line = _fix_horizontal_rule(line, stats)
        line = _fix_heading_space(line, stats)
        line = _fix_bullet(line, stats)

        removed = _remove_decorative_line(line, stats)
        if removed is None:
            # Linha removida: não resetar blank_run para que blanks
            # antes e depois da linha removida sejam contados juntos.
            if verbose:
                print(f"  [clean] linha decorativa removida: {line.strip()!r}",
                      file=sys.stderr)
            continue

        # Só reseta o contador quando efetivamente mantemos conteúdo
        blank_run = 0
        result.append(line)

    return result


# ---------------------------------------------------------------------------
# Linha final do arquivo
# ---------------------------------------------------------------------------
def _ensure_trailing_newline(lines: list[str]) -> list[str]:
    """Regra 9: garante exatamente uma \n ao final."""
    # Remover linhas em branco finais extras
    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        last = lines[-1].rstrip("\n")
        lines[-1] = last + "\n"
    return lines


# ---------------------------------------------------------------------------
# Relatório de limpeza
# ---------------------------------------------------------------------------
def build_report(
    input_path: Path,
    output_path: Path,
    stats: CleanStats,
    exit_code: int,
) -> str:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    status = "ok" if not stats.warnings else "warnings"

    lines = [
        "# Relatório de Limpeza — md-clean-markdown",
        "",
        f"- **Arquivo de entrada:** `{input_path.name}`",
        f"- **Arquivo de saída:** `{output_path.name}`",
        f"- **Linhas de entrada:** {stats.lines_in}",
        f"- **Linhas de saída:** {stats.lines_out}",
        f"- **Linhas removidas:** {stats.lines_in - stats.lines_out}",
        "",
        "**Operações aplicadas:**",
        f"- trailing whitespace removido: {stats.trailing_ws_fixed} linha(s)",
        f"- linhas em branco colapsadas: {stats.blank_collapsed} ocorrência(s)",
        f"- bullets normalizados: {stats.bullets_normalized} item(ns)",
        f"- separadores normalizados: {stats.separators_normalized} ocorrência(s)",
        f"- headings corrigidos: {stats.headings_fixed} ocorrência(s)",
        f"- linhas decorativas removidas: {stats.decorative_removed}",
        "",
        f"- **Status:** `{status}`",
        f"- **Data/hora:** {ts}",
        f"- **Exit code:** {exit_code}",
    ]

    if stats.warnings:
        lines += ["", "## Warnings"]
        lines += [f"- {w}" for w in stats.warnings]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="md-clean-markdown: limpa e normaliza Markdown bruto."
    )
    parser.add_argument("--input", required=True, metavar="MD",
                        help="Arquivo .md bruto de entrada")
    parser.add_argument("--output", required=True, metavar="MD",
                        help="Arquivo .md limpo de saída")
    parser.add_argument("--max-blank", type=int, default=2, metavar="N",
                        help="Máximo de linhas em branco consecutivas (padrão: 2)")
    parser.add_argument("--no-markers", action="store_true",
                        help="Não preservar marcadores [[Pág. N]] e <!-- page N -->")
    parser.add_argument("--verbose", action="store_true",
                        help="Log de operações no stderr")
    parser.add_argument("--report", action="store_true",
                        help="Gerar cleaning_report.md junto ao output")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    preserve_markers = not args.no_markers
    stats = CleanStats()

    # --- Validar entrada ---
    if not input_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(EXIT_INPUT_ERROR)

    # --- Ler ---
    try:
        raw_text = input_path.read_text(encoding=OUTPUT_ENCODING, errors="replace")
        import html
        raw_text = html.unescape(raw_text)
        raw_text = _normalize_typographic_ligatures(raw_text)
    except Exception as exc:
        print(f"[ERRO] Falha ao ler {input_path}: {exc}", file=sys.stderr)
        sys.exit(EXIT_INPUT_ERROR)

    lines = raw_text.splitlines(keepends=True)
    stats.lines_in = len(lines)

    if args.verbose:
        print(f"[clean] Entrada: {input_path} ({stats.lines_in} linhas)",
              file=sys.stderr)

    # --- Isolar blocos de código ---
    lines_no_code, code_blocks = _extract_code_blocks(lines)

    # --- Estruturar páginas de separação eproc fora de blocos de código ---
    structured_text = judicial_locator.structure_eproc_event_separator_markdown(
        "".join(lines_no_code)
    )
    lines_no_code = structured_text.splitlines(keepends=True)

    # --- Recompor quebras artificiais antes da limpeza estrutural ---
    lines_no_code = _recompose_hyphenated_words(lines_no_code)
    lines_no_code = _recompose_prose_lines(lines_no_code)

    # --- Aplicar regras de limpeza ---
    try:
        cleaned = clean_lines(
            lines_no_code,
            max_blank=args.max_blank,
            preserve_markers=preserve_markers,
            stats=stats,
            verbose=args.verbose,
        )
    except Exception as exc:
        print(f"[ERRO] Falha no processamento: {exc}", file=sys.stderr)
        sys.exit(EXIT_PROCESS_ERROR)

    # --- Restaurar blocos de código ---
    cleaned = _restore_code_blocks(cleaned, code_blocks)

    # --- Linha final ---
    cleaned = _ensure_trailing_newline(cleaned)
    stats.lines_out = len(cleaned)

    # --- Escrever saída ---
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("".join(cleaned), encoding=OUTPUT_ENCODING)
    except Exception as exc:
        print(f"[ERRO] Falha ao escrever {output_path}: {exc}", file=sys.stderr)
        sys.exit(EXIT_WRITE_ERROR)

    if args.verbose:
        print(f"[clean] Saída: {output_path} ({stats.lines_out} linhas)",
              file=sys.stderr)
        print(f"[clean] Trailing WS: {stats.trailing_ws_fixed} | "
              f"Blank collapsed: {stats.blank_collapsed} | "
              f"Bullets: {stats.bullets_normalized} | "
              f"Separators: {stats.separators_normalized} | "
              f"Headings: {stats.headings_fixed}",
              file=sys.stderr)

    exit_code = EXIT_OK

    # --- Relatório ---
    if args.report:
        report_path = output_path.parent / "cleaning_report.md"
        try:
            report_path.write_text(
                build_report(input_path, output_path, stats, exit_code),
                encoding=OUTPUT_ENCODING,
            )
            if args.verbose:
                print(f"[clean] Relatório: {report_path}", file=sys.stderr)
        except Exception as exc:
            print(f"[AVISO] Não foi possível escrever relatório: {exc}",
                  file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
