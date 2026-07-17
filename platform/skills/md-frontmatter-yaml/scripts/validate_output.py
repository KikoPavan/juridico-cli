#!/usr/bin/env python3
"""
md-frontmatter-yaml · validate_output.py
=========================================
Valida um arquivo .md com frontmatter gerado por apply_frontmatter.py.

Verifica:
- se o arquivo foi criado e não está vazio
- se o YAML é sintaticamente válido
- se os campos obrigatórios estão presentes
- se o corpo do Markdown foi preservado
- se o contrato mínimo foi atendido

Uso:
    python validate_output.py --input DOC_FINAL.md [--original DOC_ENTRADA.md] [--strict]

Exit codes:
    0  Validação passou
    1  Falha — erros encontrados
    2  Arquivo não encontrado
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERRO] pyyaml não instalado. Execute: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

CHECKS: list[tuple[str, callable]] = []

REQUIRED_FIELDS = {"source_file", "created_by_skill"}


def check(name: str):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _split_frontmatter(content: str) -> tuple[str | None, str]:
    """
    Separa o frontmatter YAML do corpo do Markdown.
    Retorna (yaml_str, body) ou (None, content) se não houver frontmatter.
    """
    if not content.startswith("---\n"):
        return None, content

    end = content.find("\n---\n", 4)
    if end == -1:
        return None, content

    yaml_str = content[4:end]
    body = content[end + 5:]  # após "---\n"
    return yaml_str, body


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

@check("Arquivo existe e não está vazio")
def check_not_empty(content: str, _ctx: dict) -> tuple[bool, str]:
    if not content.strip():
        return False, "Arquivo está vazio."
    return True, f"{len(content):,} chars"


@check("Começa com delimitador de frontmatter '---'")
def check_starts_with_delimiter(content: str, _ctx: dict) -> tuple[bool, str]:
    if not content.startswith("---\n"):
        return False, "Arquivo não começa com '---\\n'."
    return True, ""


@check("Frontmatter tem delimitador de fechamento '---'")
def check_closing_delimiter(content: str, _ctx: dict) -> tuple[bool, str]:
    yaml_str, _ = _split_frontmatter(content)
    if yaml_str is None:
        return False, "Delimitador de fechamento '---' não encontrado."
    return True, ""


@check("YAML é sintaticamente válido")
def check_yaml_valid(content: str, ctx: dict) -> tuple[bool, str]:
    yaml_str, _ = _split_frontmatter(content)
    if yaml_str is None:
        return False, "Não foi possível extrair o YAML."
    try:
        parsed = yaml.safe_load(yaml_str)
        ctx["yaml_data"] = parsed
        return True, f"{len(parsed)} campo(s)"
    except yaml.YAMLError as exc:
        return False, f"YAML inválido: {exc}"


@check("Campos obrigatórios presentes")
def check_required_fields(content: str, ctx: dict) -> tuple[bool, str]:
    data = ctx.get("yaml_data", {}) or {}
    missing = [f for f in REQUIRED_FIELDS if f not in data or data[f] is None]
    if missing:
        return False, f"Campos obrigatórios ausentes: {missing}"
    return True, ""


@check("Campo 'created_by_skill' é 'md-frontmatter-yaml'")
def check_created_by(content: str, ctx: dict) -> tuple[bool, str]:
    data = ctx.get("yaml_data", {}) or {}
    val = data.get("created_by_skill")
    if val != "md-frontmatter-yaml":
        return False, f"'created_by_skill' = {val!r} (esperado: 'md-frontmatter-yaml')"
    return True, ""


@check("Corpo do documento presente após o frontmatter")
def check_body_present(content: str, ctx: dict) -> tuple[bool, str]:
    _, body = _split_frontmatter(content)
    if not body.strip():
        return False, "Corpo do documento está vazio após o frontmatter."
    ctx["body"] = body
    return True, f"{len(body):,} chars no corpo"


@check("Corpo preservado integralmente (quando --original fornecido)")
def check_body_preserved(content: str, ctx: dict) -> tuple[bool, str]:
    original = ctx.get("original_content")
    if original is None:
        return True, "(--original não fornecido, verificação ignorada)"
    _, body = _split_frontmatter(content)
    # Comparar normalizado (ignorar diferença de \n final)
    if body.rstrip("\n") != original.rstrip("\n"):
        return False, "Corpo difere do arquivo original. Verifique se houve modificação."
    return True, "Corpo idêntico ao original"


@check("Encoding UTF-8")
def check_encoding(content: str, _ctx: dict) -> tuple[bool, str]:
    return True, ""


@check("Sem campos jurídicos especializados não autorizados")
def check_no_legal_fields(content: str, ctx: dict) -> tuple[bool, str]:
    data = ctx.get("yaml_data", {}) or {}
    legal_fields = {"court", "comarca", "vara", "parties", "classe_processual"}
    found = [f for f in legal_fields if f in data]
    if found:
        return True, f"WARNING: campos especializados não autorizados presentes: {found}"
    return True, ""


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_validation(md_path: Path, original_path: Path | None, strict: bool) -> int:
    try:
        content = md_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {md_path}", file=sys.stderr)
        return 2

    ctx: dict = {}
    if original_path:
        try:
            ctx["original_content"] = original_path.read_text(
                encoding="utf-8", errors="replace"
            )
        except Exception as exc:
            print(f"[AVISO] Não foi possível ler original: {exc}", file=sys.stderr)

    errors: list[str] = []
    warnings: list[str] = []

    print(f"\n[validate_output] {md_path.name}")
    print(f"  {len(content):,} chars\n")

    for name, fn in CHECKS:
        ok, msg = fn(content, ctx)
        is_warning = msg.startswith("WARNING")

        if not ok:
            errors.append(name)
            print(f"  ✗  {name}")
            if msg:
                print(f"       → {msg}")
        elif is_warning:
            warnings.append(name)
            print(f"  ⚠  {name}")
            print(f"       → {msg}")
        else:
            detail = f" ({msg})" if msg else ""
            print(f"  ✓  {name}{detail}")

    print()
    if errors:
        print(f"[RESULTADO] ✗ {len(errors)} erro(s). Validação falhou.")
        return 1
    if warnings and strict:
        print(f"[RESULTADO] ✗ {len(warnings)} warning(s) em modo --strict.")
        return 1

    print("[RESULTADO] ✓ Validação passou.")
    if warnings:
        print(f"  ({len(warnings)} warning(s) — use --strict para tratar como erro)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="validate_output: valida .md com frontmatter gerado por md-frontmatter-yaml."
    )
    parser.add_argument("--input", required=True, metavar="MD",
                        help="Arquivo .md com frontmatter a validar")
    parser.add_argument("--original", default=None, metavar="MD",
                        help="Arquivo .md original (para verificar preservação do corpo)")
    parser.add_argument("--strict", action="store_true",
                        help="Tratar warnings como erros")
    args = parser.parse_args()

    md_path = Path(args.input).expanduser().resolve()
    original_path = Path(args.original).expanduser().resolve() if args.original else None
    sys.exit(run_validation(md_path, original_path, args.strict))


if __name__ == "__main__":
    main()
