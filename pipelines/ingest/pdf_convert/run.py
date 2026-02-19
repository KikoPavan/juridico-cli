#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def find_project_root(start: Path) -> Path:
    start = start.resolve()
    for p in [start] + list(start.parents):
        if (p / "pyproject.toml").exists():
            return p
    return start


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Arquivo de profile não encontrado: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Profile inválido (YAML não é um objeto): {path}")
    return data


def resolve_profile_yaml(project_root: Path, profile_arg: str) -> Path:
    """
    Aceita:
      - nome do profile (ex.: bj_juris_stj) -> profiles/<name>/profile.yaml
      - caminho relativo dentro do projeto -> <project_root>/<path>
      - caminho absoluto -> <abs>
    """
    p = Path(profile_arg)
    if p.is_absolute():
        return p

    if profile_arg.endswith(".yaml") or "/" in profile_arg or "\\" in profile_arg:
        return (project_root / profile_arg).resolve()

    return (
        project_root
        / "pipelines"
        / "ingest"
        / "pdf_convert"
        / "profiles"
        / profile_arg
        / "profile.yaml"
    ).resolve()


def import_module_from_path(module_name: str, file_path: Path):
    file_path = file_path.resolve()
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Falha ao carregar módulo: {file_path}")
    mod = importlib.util.module_from_spec(spec)
    # IMPORTANTE: registra antes do exec (evita erro do dataclasses/sys.modules None)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def pick_profile_script(profile_dir: Path, data: Dict[str, Any]) -> Path:
    script = (
        data.get("script")
        or data.get("entrypoint")
        or (data.get("convert") or {}).get("script")
        or ""
    )
    if script:
        p = (profile_dir / script).resolve()
        if p.exists():
            return p
        raise SystemExit(f"Script do profile não encontrado: {p}")

    # fallback: tenta achar convert_*.py no diretório
    candidates = sorted(profile_dir.glob("convert_*.py"))
    if len(candidates) == 1:
        return candidates[0].resolve()
    if len(candidates) > 1:
        raise SystemExit(
            f"Profile sem 'script:' e múltiplos convert_*.py encontrados em {profile_dir}"
        )
    raise SystemExit(
        f"Profile sem 'script:' e nenhum convert_*.py encontrado em {profile_dir}"
    )


def resolve_dirs(project_root: Path, data: Dict[str, Any]) -> Dict[str, Path]:
    """
    PDF→MD: só aceita dirs.pdf e dirs.md.
    Ignora quaisquer outras chaves no YAML (ex.: json/rep).
    """
    dirs = data.get("dirs") or {}
    if not isinstance(dirs, dict):
        raise SystemExit("Profile inválido: 'dirs' deve ser um objeto.")

    def _get(k: str) -> Optional[Path]:
        v = dirs.get(k)
        if not v:
            return None
        return (project_root / str(v)).resolve()

    out: Dict[str, Path] = {}
    for key in ("pdf", "md"):
        p = _get(key)
        if p is not None:
            out[key] = p
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile", required=True, help="Nome do profile ou caminho do profile.yaml"
    )
    # Mantém compatibilidade com chamadas antigas, mas o único modo suportado é md_only.
    parser.add_argument(
        "--mode",
        default="md_only",
        choices=("md_only",),
        help="Apenas md_only (PDF→Markdown).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limita quantidade de PDFs (0 = sem limite)",
    )
    args = parser.parse_args()

    project_root = find_project_root(Path(__file__).resolve())
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    profile_yaml = resolve_profile_yaml(project_root, args.profile)
    data = load_yaml(profile_yaml)

    profile_dir = profile_yaml.parent
    profile_id = data.get("profile_id") or data.get("id") or profile_dir.name

    dirs = resolve_dirs(project_root, data)

    # PDF→MD exige somente pdf e md
    if "pdf" not in dirs or "md" not in dirs:
        raise SystemExit(
            f"Config inválida em {profile_yaml}: precisa dirs.pdf e dirs.md"
        )

    dir_pdf = dirs["pdf"]
    dir_md = dirs["md"]

    if not dir_pdf.exists():
        raise SystemExit(f"Diretório de PDFs não encontrado: {dir_pdf}")
    dir_md.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(dir_pdf.glob("*.pdf"))
    if args.limit and args.limit > 0:
        pdf_files = pdf_files[: args.limit]

    print(f"Projeto: {project_root}")
    print(f"Profile: {profile_yaml}")
    print("Mode: md_only (PDF→Markdown)")
    print(f"PDFs (entrada): {dir_pdf} ({len(pdf_files)})")
    print(f"Saída MD: {dir_md}")

    # RULES (somente limpeza/normalização de MD, se aplicável ao profile)
    rules_path = (profile_dir / "rules.py").resolve()
    if not rules_path.exists():
        raise SystemExit(f"rules.py não encontrado em: {rules_path}")
    rules_mod = import_module_from_path(f"{profile_id}__rules", rules_path)
    if not hasattr(rules_mod, "RULES"):
        raise SystemExit(f"{rules_path} não exporta RULES = <instância>")

    # convert script
    script_path = pick_profile_script(profile_dir, data)
    mod = import_module_from_path(f"{profile_id}__convert", script_path)

    # injeta contexto mínimo (PDF→MD)
    setattr(mod, "PROFILE_ID", profile_id)
    setattr(mod, "MODE", "md_only")
    setattr(mod, "LIMIT", args.limit if args.limit > 0 else None)
    setattr(mod, "DIR_PDF", str(dir_pdf))
    setattr(mod, "DIR_MD", str(dir_md))
    setattr(mod, "pdf_files", pdf_files)
    setattr(mod, "RULES", rules_mod.RULES)

    if not hasattr(mod, "main_processing_loop"):
        raise SystemExit(f"{script_path} não define main_processing_loop()")

    mod.main_processing_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
