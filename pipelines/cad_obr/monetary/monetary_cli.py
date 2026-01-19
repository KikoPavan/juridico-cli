"""
Script: monetary_cli.py

Fase 1 – CLI para aplicar o motor `monetary_core` ao fluxo cad_obr.

Fluxo padrão:
- Entrada:  outputs/cad_obr/02_normalize/escritura_imovel/collector_out-cad_obr_*.json
- Saída:    outputs/cad_obr/03_monetary/escritura_imovel/monetary_out-cad_obr_*.json

Uso típico:
    python3 scripts/monetary_cli.py

Para processar apenas um arquivo específico:
    python3 scripts/monetary_cli.py --file collector_out_cad_obr_escritura_matricula_7.546.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Tuple

from monetary_core import processar_documento_cad_obr


def _listar_arquivos_entrada(input_dir: str, file_filter: str | None) -> List[str]:
    """
    Retorna a lista de arquivos JSON de entrada a processar.

    - Se `file_filter` for fornecido:
        - Se for caminho absoluto, usa diretamente.
        - Se for apenas nome, junta com `input_dir`.
    - Caso contrário:
        - Procura por `collector_out_cad_obr_*.json` em `input_dir`.
        - Se não encontrar nada, cai para todos os `*.json` do diretório.
    """
    if file_filter:
        if os.path.isabs(file_filter):
            return [file_filter]
        else:
            return [os.path.join(input_dir, file_filter)]

    pattern_pref = os.path.join(input_dir, "collector_out_cad_obr_*.json")
    files = sorted(glob.glob(pattern_pref))

    if not files:
        # fallback: qualquer .json do diretório
        pattern_all = os.path.join(input_dir, "*.json")
        files = sorted(glob.glob(pattern_all))

    return files


def _nome_saida(output_dir: str, input_path: str) -> str:
    """
    Gera o caminho do arquivo de saída a partir do nome de entrada.

    Regra:
    - Se o nome começar com "collector_out_", troca por "monetary_out_".
    - Caso contrário, prefixa com "monetary_".
    """
    base = os.path.basename(input_path)
    if base.startswith("collector_out_"):
        saida = "monetary_" + base[len("collector_out_") :]
    else:
        saida = "monetary_" + base

    return os.path.join(output_dir, saida)


def _contar_onus(doc: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    Conta quantos itens de hipotecas_onus existem e quantos
    foram calculados / não calculados.

    Retorna:
        (total_onus, calculados_true, calculados_false)
    """
    hipotecas = doc.get("hipotecas_onus")
    if not isinstance(hipotecas, list):
        return 0, 0, 0

    total = 0
    calc_true = 0
    calc_false = 0

    for onus in hipotecas:
        if not isinstance(onus, dict):
            continue
        total += 1
        meta = onus.get("_monetary_meta", {})
        if not isinstance(meta, dict):
            continue
        flag = meta.get("calculado")
        if flag is True:
            calc_true += 1
        elif flag is False:
            calc_false += 1

    return total, calc_true, calc_false


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aplica o motor monetary (cad_obr) aos arquivos JSON do collector."
    )
    parser.add_argument(
        "--input-dir",
        default="outputs/cad_obr/02_normalize/escritura_imovel/",
        help="Diretório de entrada com arquivos collector_out_cad_obr_*.json",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/cad_obr/03_monetary/escritura_imovel/",
        help="Diretório de saída para arquivos monetary_out_cad_obr_*.json",
    )
    parser.add_argument(
        "--file",
        help=(
            "Nome de um único arquivo JSON a processar. "
            "Se for caminho absoluto, é usado diretamente; "
            "se for apenas nome, é buscado dentro de --input-dir."
        ),
    )

    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.isdir(input_dir):
        print(f"[ERRO] Diretório de entrada não existe: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)

    arquivos = _listar_arquivos_entrada(input_dir, args.file)
    if not arquivos:
        print(f"[AVISO] Nenhum arquivo .json encontrado em: {input_dir}")
        return

    print("=== monetary-cli (cad_obr) Iniciado ===")
    print(f"Entrada : {input_dir}")
    print(f"Saída   : {output_dir}")
    if args.file:
        print(f"Filtro  : {args.file}")
    print("")

    total_docs = 0
    total_onus_global = 0
    total_calc_true_global = 0
    total_calc_false_global = 0

    for path in arquivos:
        if not os.path.isfile(path):
            print(f"[AVISO] Ignorando (não é arquivo): {path}")
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            print(f"[ERRO] Falha ao ler JSON: {path} -> {e}")
            continue

        total_docs += 1
        print(f"-> Processando documento: {os.path.basename(path)}")

        doc_out = processar_documento_cad_obr(doc)

        out_path = _nome_saida(output_dir, path)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(doc_out, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   [ERRO] Falha ao gravar saída: {out_path} -> {e}")
            continue

        # Estatísticas por documento
        total_onus, calc_true, calc_false = _contar_onus(doc_out)
        total_onus_global += total_onus
        total_calc_true_global += calc_true
        total_calc_false_global += calc_false

        print(
            f"   [OK] Saída: {os.path.basename(out_path)} "
            f"(ônus: {total_onus}, calculados: {calc_true}, não calculados: {calc_false})"
        )

    print("")
    print("=== monetary-cli (cad_obr) Finalizado ===")
    print(f"Documentos processados      : {total_docs}")
    print(f"Total de ônus encontrados   : {total_onus_global}")
    print(f"Ônus com cálculo aplicado   : {total_calc_true_global}")
    print(f"Ônus sem cálculo (política/dados) : {total_calc_false_global}")


if __name__ == "__main__":
    main()
