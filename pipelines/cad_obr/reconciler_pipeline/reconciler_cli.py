# pipelines/cad_obr/reconciler/reconciler_cli.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def _ensure_repo_root_on_syspath() -> None:
    """
    Permite executar como:
      python3 pipelines/cad_obr/reconciler/reconciler_cli.py ...

    Adiciona o root do repositório ao sys.path para resolver imports
    do namespace 'pipelines.*' mesmo sem __init__.py.
    """
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[3]  # reconciler -> cad_obr -> pipelines -> repo_root
    sys.path.insert(0, str(repo_root))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="reconciler_cli.py",
        description="CAD-OBR Reconciler (incremental por camadas) - gera dataset JSONL em 04_reconciler/",
    )

    p.add_argument(
        "--input-normalize",
        required=True,
        help="Diretório raiz do normalize (ex.: outputs/cad-obr/02_normalize)",
    )
    p.add_argument(
        "--input-monetary",
        required=True,
        help="Diretório raiz do monetary (ex.: outputs/cad-obr/03_monetary)",
    )
    p.add_argument(
        "--output",
        required=True,
        help="Diretório raiz de saída do reconciler (ex.: outputs/cad-obr/04_reconciler)",
    )
    p.add_argument(
        "--dataset",
        default="dataset_v1",
        help="Nome da subpasta do dataset dentro de --output (default: dataset_v1)",
    )
    p.add_argument(
        "--pattern",
        default="*.json",
        help="Pattern glob para arquivos JSON de entrada (default: *.json)",
    )
    p.add_argument(
        "--stop-after",
        default="ALL",
        choices=["A", "B", "C", "D", "E", "ALL"],
        help="Executa até a camada indicada (default: ALL). A=índices base, B=ônus, C=eventos, D=links/pendências, E=novações.",
    )

    return p.parse_args()


def _validate_dirs(input_normalize: Path, input_monetary: Path) -> Optional[str]:
    if not input_normalize.exists() or not input_normalize.is_dir():
        return f"Diretório inválido em --input-normalize: {input_normalize}"
    if not input_monetary.exists() or not input_monetary.is_dir():
        return f"Diretório inválido em --input-monetary: {input_monetary}"
    return None


def main() -> int:
    args = _parse_args()
    input_normalize = Path(args.input_normalize).resolve()
    input_monetary = Path(args.input_monetary).resolve()
    output_root = Path(args.output).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    err = _validate_dirs(input_normalize, input_monetary)
    if err:
        print(f"ERRO: {err}", file=sys.stderr)
        return 2

    # Imports após sys.path ajustado
    from reconciler_core import (
        CadObrReconciler,
        ReconcilerInputs,
        ReconcilerOutputs,
    )

    inputs = ReconcilerInputs(
        normalize_root=input_normalize,
        monetary_root=input_monetary,
        pattern=args.pattern,
    )
    outputs = ReconcilerOutputs(
        output_root=output_root,
        dataset_dirname=args.dataset,
    )

    recon = CadObrReconciler(inputs, outputs)

    # Execução por camadas (incremental)
    recon.layer_a_load_and_index()
    if args.stop_after == "A":
        out_dir = recon.write_dataset()
        print(f"OK: Camada A concluída. Dataset parcial em: {out_dir}")
        return 0

    recon.layer_b_build_onus_obrigacoes()
    if args.stop_after == "B":
        out_dir = recon.write_dataset()
        print(f"OK: Camadas A+B concluídas. Dataset parcial em: {out_dir}")
        return 0

    recon.layer_c_build_property_events()
    if args.stop_after == "C":
        out_dir = recon.write_dataset()
        print(f"OK: Camadas A+B+C concluídas. Dataset parcial em: {out_dir}")
        return 0

    recon.layer_d_build_links_and_pendencias()
    if args.stop_after == "D":
        out_dir = recon.write_dataset()
        print(f"OK: Camadas A+B+C+D concluídas. Dataset parcial em: {out_dir}")
        return 0

    recon.layer_e_build_novacoes()
    out_dir = recon.write_dataset()
    print(f"OK: Camadas A+B+C+D+E concluídas. Dataset em: {out_dir}")

    # Resumo rápido (arquivos esperados)
    expected = [
        "documentos.jsonl",
        "partes.jsonl",
        "imoveis.jsonl",
        "contratos_operacoes.jsonl",
        "onus_obrigacoes.jsonl",
        "property_events.jsonl",
        "links.jsonl",
        "pendencias.jsonl",
        "novacoes_detectadas.jsonl",
    ]
    missing = [f for f in expected if not (out_dir / f).exists()]
    if missing:
        print("ATENÇÃO: arquivos ausentes:", ", ".join(missing), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
