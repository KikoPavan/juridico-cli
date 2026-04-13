#!/usr/bin/env python3
"""
gerar_exemplo.py — Executa o curador com o exemplo de entrada e salva a saída
Projeto: juridico-cli / skill: curador-relevancia

Uso:
  python gerar_exemplo.py                     # ambos os modos
  python gerar_exemplo.py --modo padrao
  python gerar_exemplo.py --modo sintetico
"""

import json
import sys
import argparse
from pathlib import Path

# Adiciona o diretório do script ao path
sys.path.insert(0, str(Path(__file__).parent))

from curar import CuradorRelevancia

BASE = Path(__file__).parent.parent / "assets"


def rodar(modo: str):
    entrada_path = BASE / "exemplo_entrada.json"
    saida_path = BASE / f"exemplo_saida_{modo}.json"

    with open(entrada_path, "r", encoding="utf-8") as f:
        entrada = json.load(f)

    entrada["metadata"]["modo_curadoria"] = modo
    curador = CuradorRelevancia(modo=modo)
    resultado = curador.processar(entrada)

    with open(saida_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"✓ Exemplo [{modo}] → {saida_path}")
    s = resultado["sumario"]
    print(f"  manter={s['total_manter']} resumir={s['total_resumir']} "
          f"remover={s['total_remover']} revisar={s['total_revisar']} "
          f"retenção={s['taxa_retencao']:.1%}")


def main():
    parser = argparse.ArgumentParser(description="Gerador de exemplos do curador")
    parser.add_argument("--modo", choices=["padrao", "sintetico"], default=None)
    args = parser.parse_args()

    modos = [args.modo] if args.modo else ["padrao", "sintetico"]
    for m in modos:
        rodar(m)


if __name__ == "__main__":
    main()
