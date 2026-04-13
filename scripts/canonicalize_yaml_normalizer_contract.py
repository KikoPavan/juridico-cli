#!/usr/bin/env python3
import argparse
import re
from datetime import datetime
from pathlib import Path


def backup_file(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak.{ts}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return backup


def apply_regex_replacements(
    text: str, replacements: list[tuple[str, str]]
) -> tuple[str, int]:
    total = 0
    for pattern, repl in replacements:
        text, n = re.subn(pattern, repl, text, flags=re.MULTILINE)
        total += n
    return text, total


def update_file(path: Path, replacements: list[tuple[str, str]]) -> None:
    if not path.exists():
        print(f"[SKIP] Arquivo não encontrado: {path}")
        return

    original = path.read_text(encoding="utf-8")
    updated, count = apply_regex_replacements(original, replacements)

    if updated == original:
        print(f"[OK] Sem mudanças necessárias: {path}")
        return

    backup = backup_file(path)
    path.write_text(updated, encoding="utf-8", newline="\n")
    print(f"[WR] {path} | substituições: {count} | backup: {backup.name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Alinha o yaml-normalizador-juridico à nomenclatura canônica em português."
    )
    parser.add_argument(
        "--root", default=".", help="Raiz do repositório. Padrão: diretório atual."
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    base = root / "platform/skills/yaml-normalizador-juridico"

    file_replacements: dict[Path, list[tuple[str, str]]] = {
        base / "scripts/apply_yaml_normalization.py": [
            (r'"curation_action"(?=\s*:)', '"acao_curatorial"'),
            (r'"impacto_sentenca"(?=\s*:)', '"impacto_sentenca_confirmado"'),
            (r'ctx\["curation_action"\]', 'ctx["acao_curatorial"]'),
            (r'ctx\["impacto_sentenca"\]', 'ctx["impacto_sentenca_confirmado"]'),
        ],
        base / "scripts/validate_yaml_normalizador_juridico.py": [
            (r'"curation_action"(?=\s*:|\s*,)', '"acao_curatorial"'),
            (r'"impacto_sentenca"(?=\s*:|\s*,)', '"impacto_sentenca_confirmado"'),
            (r'fm\.get\("curation_action"\)', 'fm.get("acao_curatorial")'),
            (r'fm\.get\("impacto_sentenca"\)', 'fm.get("impacto_sentenca_confirmado")'),
            (r"\bcuration_action inválido\b", "acao_curatorial inválida"),
            (r"# 5\. curation_action válido", "# 5. acao_curatorial válida"),
            (
                r"# 11\. impacto_sentenca deve ser boolean",
                "# 11. impacto_sentenca_confirmado deve ser boolean",
            ),
            (
                r"\bimpacto_sentenca deve ser boolean\b",
                "impacto_sentenca_confirmado deve ser boolean",
            ),
        ],
        base / "assets/io.schema.json": [
            (r'"curation_action"(?=\s*:|\s*,)', '"acao_curatorial"'),
            (r'"impacto_sentenca"(?=\s*:|\s*,)', '"impacto_sentenca_confirmado"'),
        ],
        base / "assets/output_contract.md": [
            (r"`curation_action`", "`acao_curatorial`"),
            (r"`impacto_sentenca`", "`impacto_sentenca_confirmado`"),
        ],
        base / "assets/frontmatter_template.jinja2": [
            (r"^curation_action:", "acao_curatorial:"),
            (r"^impacto_sentenca:", "impacto_sentenca_confirmado:"),
            (r"<manter\|comprimir\|revisar>", "<manter|resumir|remover|revisar>"),
        ],
        base / "references/field_dictionary.md": [
            (r"### `curation_action`", "### `acao_curatorial`"),
            (r"### `impacto_sentenca`", "### `impacto_sentenca_confirmado`"),
        ],
        base / "references/exemplo_fluxo.md": [
            (r"^curation_action:", "acao_curatorial:"),
            (r"^impacto_sentenca:", "impacto_sentenca_confirmado:"),
        ],
        base / "references/example_output.md": [
            (r"^piece_id:\s*peca-003-peticao-inicial$", "piece_id: peca_001"),
            (r"^origin_piece_index:\s*2$", "origin_piece_index: 0"),
            (r"^priority:\s*alta$", "priority: 1"),
            (r"^impacto_processual:\s*alto$", "impacto_processual: nuclear"),
            (
                r'^court:\s*"__ Vara Cível da Comarca de São Paulo"$',
                "court: Vara Cível da Comarca de São Paulo",
            ),
            (r"^curation_action:", "acao_curatorial:"),
            (r"^impacto_sentenca:", "impacto_sentenca_confirmado:"),
        ],
    }

    for path, replacements in file_replacements.items():
        update_file(path, replacements)

    print("\nConcluído.")
    print("Nenhum arquivo do pipeline em apps/data-processing/ foi alterado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
