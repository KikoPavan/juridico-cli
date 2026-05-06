#!/usr/bin/env python3
"""
pdf-to-md · validate_output.py
===============================
Valida um arquivo .md gerado por convert_pdf_to_md.py
contra o contrato operacional de saída da skill.

Uso:
    python validate_output.py --input DOC.md [--strict]

Exit codes:
    0  Passou (sem erros)
    1  Falha (erros ou warnings em modo --strict)
    2  Arquivo não encontrado
"""

import argparse
import re
import sys
from pathlib import Path

CHECKS: list[tuple[str, callable]] = []


def check(label: str):
    def decorator(fn):
        CHECKS.append((label, fn))
        return fn
    return decorator


@check("Arquivo não está vazio")
def _not_empty(content, lines):
    return (False, "Arquivo está vazio.") if not content.strip() else (True, "")


@check("Sem YAML frontmatter")
def _no_yaml(content, lines):
    if content.lstrip().startswith("---"):
        return False, "Começa com '---': YAML frontmatter não é permitido."
    return True, ""


@check("Presença de anchors de página")
def _has_markers(content, lines):
    found = re.findall(r"\[\[Pág\.\s+\d+\]\]", content)
    if not found:
        return False, "Nenhum anchor [[Pág. N]] encontrado."
    return True, f"{len(found)} anchor(s) encontrado(s)."


@check("Anchors de página bem formados")
def _marker_format(content, lines):
    raw = re.findall(r"\[\[Pág\.[^\]]*\]\]", content)
    valid = re.compile(r"\[\[Pág\.\s+\d+\]\]")
    bad = [m for m in raw if not valid.match(m.strip())]
    if bad:
        return False, f"Malformados: {bad[:3]}"
    return True, ""


@check("Encoding UTF-8 legível")
def _encoding(content, lines):
    return True, ""


@check("Linhas sem comprimento excessivo")
def _line_lengths(content, lines):
    long_lines = [i + 1 for i, l in enumerate(lines) if len(l) > 2000]
    if long_lines:
        return True, f"WARNING: {len(long_lines)} linha(s) >2000 chars: {long_lines[:5]}"
    return True, ""


def run_validation(md_path: Path, strict: bool) -> int:
    try:
        content = md_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print(f"[ERRO] Não encontrado: {md_path}", file=sys.stderr)
        return 2

    lines = content.split("\n")
    errors, has_warnings = [], False

    print(f"\n[validate_output] {md_path}")
    print(f"  {len(content):,} chars | {len(lines):,} linhas\n")

    for label, fn in CHECKS:
        ok, msg = fn(content, lines)
        is_warn = msg.startswith("WARNING")

        if not ok:
            errors.append(label)
            print(f"  ✗  {label}")
            if msg:
                print(f"       {msg}")
        elif is_warn:
            has_warnings = True
            print(f"  ⚠  {label}")
            print(f"       {msg}")
        else:
            print(f"  ✓  {label}" + (f" ({msg})" if msg else ""))

    print()
    if errors:
        print(f"[RESULTADO] ✗ {len(errors)} erro(s).")
        return 1
    if has_warnings and strict:
        print("[RESULTADO] ✗ Warnings em modo --strict.")
        return 1
    print("[RESULTADO] ✓ Validação passou.")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input",  required=True, metavar="MD")
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    sys.exit(run_validation(Path(args.input).expanduser().resolve(), args.strict))


if __name__ == "__main__":
    main()
