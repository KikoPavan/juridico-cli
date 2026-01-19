# pipelines/cad_obr/normalize/normalize_pipeline_cli.py
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

DEFAULT_CATEGORIES = ["contrato_social", "escritura_imovel", "escritura_hipotecaria"]


def _script_paths() -> Tuple[Path, Path, Path]:
    """
    Resolve os scripts normalizadores como arquivos irmãos deste motor.
    """
    here = Path(__file__).resolve().parent
    s1 = here / "normalize_titularidade.py"
    s2 = here / "normalize_partes.py"
    s3 = here / "normalize_valores.py"
    return s1, s2, s3


def _run(cmd: List[str], dry_run: bool) -> None:
    if dry_run:
        print("[dry-run]", " ".join(cmd))
        return
    subprocess.run(cmd, check=True)


def _copy_back_outputs(tmp_cat_dir: Path, dest_cat_dir: Path) -> int:
    """
    Copia de volta apenas os arquivos gerados pelo normalizador (safe overwrite),
    sem apagar arquivos que não foram gerados no tmp.
    """
    count = 0
    for f in tmp_cat_dir.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(tmp_cat_dir)
        dst = dest_cat_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        count += 1
    return count


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="normalize_pipeline_cli.py",
        description="Motor CAD_OBR: roda normalize_titularidade -> normalize_partes -> normalize_valores (por categoria).",
    )

    p.add_argument(
        "--collector-root",
        default="outputs/cad_obr/01_collector",
        help="Raiz de entrada (default: outputs/cad_obr/01_collector)",
    )
    p.add_argument(
        "--normalize-root",
        default="outputs/cad_obr/02_normalize",
        help="Raiz de saída/base de normalização (default: outputs/cad_obr/02_normalize)",
    )
    p.add_argument(
        "--pattern",
        default="*collector_out*.json",
        help="Glob de arquivos a processar (default: *collector_out*.json)",
    )
    p.add_argument(
        "--categories",
        nargs="*",
        default=DEFAULT_CATEGORIES,
        help=f"Categorias/pastas a processar (default: {', '.join(DEFAULT_CATEGORIES)})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas imprime os comandos sem executar.",
    )
    p.add_argument(
        "--keep-tmp",
        action="store_true",
        help="Mantém diretório temporário do step de valores (debug).",
    )

    return p.parse_args()


def main() -> int:
    args = _parse_args()

    collector_root = Path(args.collector_root).resolve()
    normalize_root = Path(args.normalize_root).resolve()
    pattern = str(args.pattern)
    categories: List[str] = list(args.categories or [])
    dry_run: bool = bool(args.dry_run)
    keep_tmp: bool = bool(args.keep_tmp)

    s_tit, s_partes, s_val = _script_paths()

    # checks mínimos
    for s in (s_tit, s_partes, s_val):
        if not s.exists():
            print(f"ERRO: script não encontrado: {s}", file=sys.stderr)
            return 2

    if not collector_root.exists():
        print(f"ERRO: collector-root inválido: {collector_root}", file=sys.stderr)
        return 2

    normalize_root.mkdir(parents=True, exist_ok=True)

    # temp root para step 3 (valores)
    tmp_root: Optional[Path] = None
    if not dry_run:
        tmp_root = Path(tempfile.mkdtemp(prefix="cad_obr_norm_valores_"))

    try:
        for cat in categories:
            in_cat_01 = collector_root / cat
            out_cat_02 = normalize_root / cat

            if not in_cat_01.exists():
                print(f"ATENÇÃO: categoria não encontrada (pulando): {in_cat_01}")
                continue

            out_cat_02.mkdir(parents=True, exist_ok=True)

            # 1) titularidade: 01 -> 02
            cmd1 = [
                sys.executable,
                str(s_tit),
                "--input",
                str(in_cat_01),
                "--output",
                str(out_cat_02),
                "--pattern",
                pattern,
            ]
            _run(cmd1, dry_run)

            # 2) partes: inplace em 02 (script exige --output e aceita --inplace)
            cmd2 = [
                sys.executable,
                str(s_partes),
                "--input",
                str(out_cat_02),
                "--output",
                str(out_cat_02),
                "--pattern",
                pattern,
                "--inplace",
            ]
            _run(cmd2, dry_run)

            # 3) valores: NÃO tem --inplace -> roda para tmp e copia de volta
            if dry_run:
                tmp_cat = Path("/tmp") / f"cad_obr_norm_valores_preview/{cat}"
            else:
                assert tmp_root is not None
                tmp_cat = tmp_root / cat
                tmp_cat.mkdir(parents=True, exist_ok=True)

            cmd3 = [
                sys.executable,
                str(s_val),
                "--input",
                str(out_cat_02),
                "--output",
                str(tmp_cat),
                "--pattern",
                pattern,
            ]
            _run(cmd3, dry_run)

            if not dry_run:
                changed = _copy_back_outputs(tmp_cat, out_cat_02)
                print(
                    f"OK: {cat} -> valores aplicados (arquivos copiados de volta: {changed})"
                )

        return 0

    except subprocess.CalledProcessError as e:
        print(f"ERRO: comando falhou (exit={e.returncode})", file=sys.stderr)
        return e.returncode or 1

    finally:
        if tmp_root is not None and tmp_root.exists() and not keep_tmp:
            shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
