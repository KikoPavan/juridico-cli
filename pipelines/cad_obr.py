#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pipelines/cad_obr.py

Orquestrador do pipeline CAD-OBR (Normalize -> Monetary).

Ordem por tipo de documento:
1) normalize_valores.py       (01_collector -> 02_normalize)
2) normalize_titularidade.py  (in-place em 02_normalize)
3) normalize_partes.py        (in-place em 02_normalize)
4) monetary_cli.py            (02_normalize -> 03_monetary)

Uso:
  python3 pipelines/cad_obr.py
  python3 pipelines/cad_obr.py --dry-run
  python3 pipelines/cad_obr.py --types escritura_imovel
  python3 pipelines/cad_obr.py --skip-monetary
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


DEFAULT_TYPES = ["contrato_social", "escritura_imovel", "escritura_hipotecaria"]


@dataclass
class RunResult:
    ok: bool
    cmd: List[str]
    returncode: int


def _repo_root() -> Path:
    # Este arquivo está em <repo>/pipelines/cad_obr.py
    return Path(__file__).resolve().parents[1]


def _script_path(repo: Path, rel: str) -> Path:
    return (repo / rel).resolve()


def _run(cmd: List[str], dry_run: bool) -> RunResult:
    print("\n$ " + " ".join(cmd))
    if dry_run:
        return RunResult(ok=True, cmd=cmd, returncode=0)

    p = subprocess.run(cmd, text=True)
    return RunResult(ok=(p.returncode == 0), cmd=cmd, returncode=p.returncode)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    repo = _repo_root()

    ap = argparse.ArgumentParser(description="Orquestrador CAD-OBR (normalize + monetary).")
    ap.add_argument(
        "--base-out",
        default="outputs/cad-obr",
        help="Base de outputs (default: outputs/cad-obr)",
    )
    ap.add_argument(
        "--types",
        default=",".join(DEFAULT_TYPES),
        help="Tipos a processar separados por vírgula (default: contrato_social,escritura_imovel,escritura_hipotecaria)",
    )
    ap.add_argument(
        "--pattern",
        default="*collector_out*.json",
        help='Pattern de entrada do collector para o normalize_valores (default: "*collector_out*.json")',
    )
    ap.add_argument("--dry-run", action="store_true", help="Apenas imprime comandos, sem executar.")
    ap.add_argument("--continue-on-error", action="store_true", help="Continua mesmo se um passo falhar.")
    ap.add_argument("--skip-values", action="store_true", help="Pula normalize_valores.")
    ap.add_argument("--skip-titularidade", action="store_true", help="Pula normalize_titularidade.")
    ap.add_argument("--skip-partes", action="store_true", help="Pula normalize_partes.")
    ap.add_argument("--skip-monetary", action="store_true", help="Pula monetary_cli.")
    args = ap.parse_args()

    base_out = (repo / args.base_out).resolve()
    dir_01 = base_out / "01_collector"
    dir_02 = base_out / "02_normalize"
    dir_03 = base_out / "03_monetary"

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    if not types:
        print("ERRO: --types vazio.")
        return 2

    normalize_valores_py = _script_path(repo, "pipelines/cad_obr/normalize/normalize_valores.py")
    normalize_titularidade_py = _script_path(repo, "pipelines/cad_obr/normalize/normalize_titularidade.py")
    normalize_partes_py = _script_path(repo, "pipelines/cad_obr/normalize/normalize_partes.py")
    monetary_cli_py = _script_path(repo, "pipelines/cad_obr/monetary/monetary_cli.py")

    py = sys.executable  # garante o Python do seu venv/uv/ambiente atual

    failures: List[str] = []

    for t in types:
        in_01 = dir_01 / t
        out_02 = dir_02 / t
        out_03 = dir_03 / t

        print("\n" + "=" * 72)
        print(f"TIPO: {t}")
        print(f"01_collector: {in_01}")
        print(f"02_normalize: {out_02}")
        print(f"03_monetary:  {out_03}")
        print("=" * 72)

        if not in_01.exists():
            msg = f"[ERRO] Pasta de entrada não existe: {in_01}"
            print(msg)
            failures.append(msg)
            if not args.continue_on_error:
                return 1
            continue

        _ensure_dir(out_02)
        _ensure_dir(out_03)

        # 1) normalize_valores (01 -> 02)
        if not args.skip_values:
            cmd = [
                py,
                str(normalize_valores_py),
                "--input",
                str(in_01),
                "--output",
                str(out_02),
                "--pattern",
                args.pattern,
            ]
            r = _run(cmd, args.dry_run)
            if not r.ok:
                msg = f"[FAIL] normalize_valores ({t}) rc={r.returncode}"
                print(msg)
                failures.append(msg)
                if not args.continue_on_error:
                    return 1

        # 2) normalize_titularidade (in-place em 02)
        if not args.skip_titularidade:
            cmd = [
                py,
                str(normalize_titularidade_py),
                "--input",
                str(out_02),
                "--output",
                str(out_02),
                "--pattern",
                "*.json",
                "--inplace",
            ]
            r = _run(cmd, args.dry_run)
            if not r.ok:
                msg = f"[FAIL] normalize_titularidade ({t}) rc={r.returncode}"
                print(msg)
                failures.append(msg)
                if not args.continue_on_error:
                    return 1

        # 3) normalize_partes (in-place em 02)
        if not args.skip_partes:
            cmd = [
                py,
                str(normalize_partes_py),
                "--input",
                str(out_02),
                "--output",
                str(out_02),
                "--pattern",
                "*.json",
                "--inplace",
            ]
            r = _run(cmd, args.dry_run)
            if not r.ok:
                msg = f"[FAIL] normalize_partes ({t}) rc={r.returncode}"
                print(msg)
                failures.append(msg)
                if not args.continue_on_error:
                    return 1

        # 4) monetary_cli (02 -> 03)
        if not args.skip_monetary:
            cmd = [
                py,
                str(monetary_cli_py),
                "--input-dir",
                str(out_02),
                "--output-dir",
                str(out_03),
            ]
            r = _run(cmd, args.dry_run)
            if not r.ok:
                msg = f"[FAIL] monetary_cli ({t}) rc={r.returncode}"
                print(msg)
                failures.append(msg)
                if not args.continue_on_error:
                    return 1

    print("\n" + "=" * 72)
    if failures:
        print("PIPELINE FINALIZADO COM FALHAS:")
        for f in failures:
            print("- " + f)
        print("=" * 72)
        return 1

    print("PIPELINE FINALIZADO COM SUCESSO.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
