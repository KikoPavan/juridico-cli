#!/usr/bin/env python3
"""
md-clean-markdown · validate_output.py
========================================
Valida um arquivo .md limpo produzido por clean_markdown.py
contra o contrato mínimo de saída da skill.

Agnóstico de domínio: não verifica conteúdo, apenas estrutura e contrato.

Uso:
    python validate_output.py --input DOC_LIMPO.md [--strict]

Exit codes:
    0  Validação passou (sem erros)
    1  Falha — erros encontrados (ou warnings em modo --strict)
    2  Arquivo não encontrado
"""

import argparse
import re
import sys
from pathlib import Path

# Deve permanecer em sincronia com PAGE_MARKER_RE em clean_markdown.py
# Formato primário: [[Pág. N]] — output real de pdf-to-md
# Formato legado:   <!-- page N --> e variantes
PAGE_MARKER_RE = re.compile(
    r"\[\[judicial_locator:[^\]]*\]\]"
    r"|\[\[Pág\.\s*\d+\]\]"
    r"|<!--\s*page\s+\d+(\s*:\s*(empty|extraction_failed|scanned_no_ocr))?\s*-->"
)

CHECKS: list[tuple[str, callable]] = []


def check(name: str):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

@check("Arquivo existe e não está vazio")
def check_not_empty(content: str, lines: list[str]) -> tuple[bool, str]:
    if not content.strip():
        return False, "Arquivo está vazio."
    return True, f"{len(content):,} chars | {len(lines):,} linhas"


@check("Sem YAML frontmatter")
def check_no_yaml(content: str, lines: list[str]) -> tuple[bool, str]:
    if content.lstrip().startswith("---\n") or content.lstrip().startswith("---\r\n"):
        # Distinguir frontmatter YAML de separador horizontal ---
        # Frontmatter tem --- no início E outra --- fechando
        segment = content.lstrip()
        after_first = segment[3:].lstrip("\n\r")
        if re.search(r"\n---\s*\n", after_first[:2000]):
            return False, "Possível YAML frontmatter detectado no início."
    return True, ""


@check("Sem trailing whitespace nas linhas")
def check_no_trailing_ws(content: str, lines: list[str]) -> tuple[bool, str]:
    bad = []
    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip("\n\r")
        # Permitir 2 espaços finais (quebra forçada Markdown)
        if stripped.endswith(" ") and not stripped.endswith("  "):
            bad.append(i)
        elif stripped.endswith("\t"):
            bad.append(i)
    if bad:
        return False, f"Trailing whitespace em {len(bad)} linha(s): {bad[:5]}"
    return True, ""


@check("Sem sequências excessivas de linhas em branco (>2)")
def check_blank_lines(content: str, lines: list[str]) -> tuple[bool, str]:
    run = 0
    violations = []
    for i, line in enumerate(lines, start=1):
        if not line.strip():
            run += 1
            if run > 2:
                violations.append(i)
        else:
            run = 0
    if violations:
        return False, f"Sequências com >2 linhas em branco, ex.: linha(s) {violations[:5]}"
    return True, ""


@check("Headings com espaço correto após #")
def check_heading_space(content: str, lines: list[str]) -> tuple[bool, str]:
    bad = []
    for i, line in enumerate(lines, start=1):
        if re.match(r"^#{1,6}[^ #\n]", line):
            bad.append((i, line.rstrip()))
    if bad:
        return False, f"Headings malformados em {len(bad)} linha(s): {bad[:3]}"
    return True, ""


@check("Bullets normalizados (sem * ou + soltos como marcador)")
def check_bullets(content: str, lines: list[str]) -> tuple[bool, str]:
    bad = []
    for i, line in enumerate(lines, start=1):
        if re.match(r"^[ \t]*[*+] ", line):
            bad.append(i)
    if bad:
        return False, f"Bullets não normalizados em {len(bad)} linha(s): {bad[:5]}"
    return True, ""


@check("Arquivo termina com exatamente uma quebra de linha")
def check_trailing_newline(content: str, lines: list[str]) -> tuple[bool, str]:
    if not content.endswith("\n"):
        return False, "Arquivo não termina com \\n."
    if content.endswith("\n\n"):
        return True, "WARNING: arquivo termina com múltiplas quebras de linha."
    return True, ""


@check("Marcadores de página no output (formato reconhecido)")
def check_page_markers(content: str, lines: list[str]) -> tuple[bool, str]:
    count = sum(1 for _ in PAGE_MARKER_RE.finditer(content))
    if count:
        return True, f"{count} marcador(es) de página presente(s)"
    return True, ""  # Ausência não é erro — o MD de entrada pode não ter tido marcadores


@check("Encoding UTF-8 (leitura bem-sucedida)")
def check_encoding(content: str, lines: list[str]) -> tuple[bool, str]:
    return True, ""


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def _check_marker_integrity(source_content: str, output_content: str) -> tuple[bool, str]:
    """Verifica que cada marcador presente na fonte existe na saída."""
    source_markers = [m.group(0) for m in PAGE_MARKER_RE.finditer(source_content)]
    if not source_markers:
        return True, "nenhum marcador de página na fonte"

    missing = [m for m in source_markers if m not in output_content]
    if missing:
        sample = missing[:3]
        return False, f"{len(missing)} marcador(es) ausente(s) na saída: {sample}"
    return True, f"{len(source_markers)} marcador(es) verificado(s) ✓"


def run_validation(md_path: Path, strict: bool, source_path: Path | None = None) -> int:
    try:
        content = md_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {md_path}", file=sys.stderr)
        return 2

    lines = content.split("\n")
    errors: list[str] = []
    warnings_found: list[str] = []

    print(f"\n[validate_output] {md_path.name}")
    print(f"  {len(content):,} chars | {len(lines):,} linhas\n")

    for name, fn in CHECKS:
        ok, msg = fn(content, lines)
        is_warning = msg.startswith("WARNING")

        if not ok:
            errors.append(name)
            print(f"  ✗  {name}")
            if msg:
                print(f"       → {msg}")
        elif is_warning:
            warnings_found.append(name)
            print(f"  ⚠  {name}")
            print(f"       → {msg}")
        else:
            detail = f" ({msg})" if msg else ""
            print(f"  ✓  {name}{detail}")

    if source_path is not None:
        check_name = "Integridade de marcadores de página (fonte → saída)"
        try:
            source_content = source_path.read_text(encoding="utf-8", errors="replace")
            ok, msg = _check_marker_integrity(source_content, content)
            if not ok:
                errors.append(check_name)
                print(f"  ✗  {check_name}")
                print(f"       → {msg}")
            else:
                print(f"  ✓  {check_name} ({msg})")
        except FileNotFoundError:
            print(f"  ⚠  {check_name}")
            print(f"       → Arquivo fonte não encontrado: {source_path}", file=sys.stderr)

    print()
    if errors:
        print(f"[RESULTADO] ✗ {len(errors)} erro(s). Validação falhou.")
        return 1
    if warnings_found and strict:
        print(f"[RESULTADO] ✗ {len(warnings_found)} warning(s) em modo --strict.")
        return 1

    print("[RESULTADO] ✓ Validação passou.")
    if warnings_found:
        print(f"  ({len(warnings_found)} warning(s) — use --strict para tratar como erro)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="validate_output: valida .md gerado por md-clean-markdown."
    )
    parser.add_argument("--input", required=True, metavar="MD",
                        help="Arquivo .md limpo a validar (saída de clean_markdown.py)")
    parser.add_argument("--source", metavar="MD",
                        help="Arquivo .md bruto original (entrada de clean_markdown.py) — "
                             "habilita verificação de integridade de marcadores de página")
    parser.add_argument("--strict", action="store_true",
                        help="Tratar warnings como erros")
    args = parser.parse_args()

    md_path = Path(args.input).expanduser().resolve()
    source_path = Path(args.source).expanduser().resolve() if args.source else None
    sys.exit(run_validation(md_path, args.strict, source_path=source_path))


if __name__ == "__main__":
    main()
