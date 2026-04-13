#!/usr/bin/env python3
"""
validar_saida.py — Validação do Envelope Curado (Curador de Relevância)
Projeto: juridico-cli / skill: curador-relevancia

Uso:
  python validar_saida.py --arquivo envelope_curado.json
  python validar_saida.py --arquivo envelope_curado.json --schema ../assets/schema_saida.json
  python validar_saida.py --arquivo envelope_curado.json --verbose
"""

import json
import argparse
import sys
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

CAMPOS_OBRIGATORIOS_PECA = [
    "piece_id", "document_type",
    "acao_curatorial", "justificativa_curta",
    "impacto_processual", "impacto_sentenca_confirmado",
    "prioridade", "compressao_sugerida", "encaminhamento",
    "audit_trail",
]

ACOES_VALIDAS = {"manter", "resumir", "remover", "revisar"}
MODOS_VALIDOS = {"padrao", "sintetico"}
IMPACTOS_VALIDOS = {"nuclear", "relevante", "acessorio", "irrelevante"}
COMPRESSOES_VALIDAS = {"resumo_1p", "cabecalho_apenas", "metadado_apenas", None}


def validar_envelope(dados: dict) -> list[str]:
    """Validação estrutural do Envelope Curado."""
    erros = []

    # Top-level
    if "metadata" not in dados:
        erros.append("Campo obrigatório ausente: 'metadata'")
    if "pecas" not in dados:
        erros.append("Campo obrigatório ausente: 'pecas'")
        return erros

    if not isinstance(dados["pecas"], list):
        erros.append("'pecas' deve ser uma lista")
        return erros

    # Metadata
    meta = dados.get("metadata", {})
    # Campos enriquecidos pelo curador (opcionais na entrada, obrigatórios na saída curada)
    for campo in ["modo_aplicado", "versao_schema", "gerado_por_curador"]:
        if campo not in meta:
            erros.append(f"metadata.{campo}: campo ausente (deve ser adicionado pelo curador)")

    if meta.get("gerado_por_curador") != "curador-relevancia":
        erros.append("metadata.gerado_por_curador: deve ser 'curador-relevancia'")

    # Peças
    for i, peca in enumerate(dados["pecas"]):
        prefixo = f"pecas[{i}] (piece_id={peca.get('piece_id', '?')})"

        for campo in CAMPOS_OBRIGATORIOS_PECA:
            if campo not in peca:
                erros.append(f"{prefixo}: campo obrigatório ausente '{campo}'")

        acao = peca.get("acao_curatorial")
        if acao not in ACOES_VALIDAS:
            erros.append(f"{prefixo}: acao_curatorial inválida '{acao}'. Válidas: {ACOES_VALIDAS}")

        modo = peca.get("modo_aplicado")
        if modo not in MODOS_VALIDOS:
            erros.append(f"{prefixo}: modo_aplicado inválido '{modo}'")

        impacto = peca.get("impacto_processual")
        if impacto not in IMPACTOS_VALIDOS:
            erros.append(f"{prefixo}: impacto_processual inválido '{impacto}'")

        compressao = peca.get("compressao_sugerida")
        if compressao not in COMPRESSOES_VALIDAS:
            erros.append(f"{prefixo}: compressao_sugerida inválida '{compressao}'")

        prioridade = peca.get("prioridade")
        if not isinstance(prioridade, int) or prioridade < 1 or prioridade > 5:
            erros.append(f"{prefixo}: prioridade deve ser integer 1–5, got: {prioridade}")

        just = peca.get("justificativa_curta", "")
        if not just or not isinstance(just, str) or not just.strip():
            erros.append(f"{prefixo}: justificativa_curta não pode ser vazia")
        elif len(just) > 120:
            erros.append(f"{prefixo}: justificativa_curta excede 120 chars ({len(just)})")

        # Regra: remover com justificativa obrigatória
        if acao == "remover" and not (just and just.strip()):
            erros.append(f"{prefixo}: acao=remover exige justificativa_curta")

        # Regra: resumir deve ter compressao_sugerida
        if acao == "resumir" and compressao is None:
            erros.append(f"{prefixo}: acao=resumir sem compressao_sugerida")

        # audit_trail como array
        trail = peca.get("audit_trail")
        if not isinstance(trail, list):
            erros.append(f"{prefixo}: audit_trail deve ser array, got: {type(trail).__name__}")
        elif len(trail) == 0:
            erros.append(f"{prefixo}: audit_trail deve ter ao menos 1 entrada")
        else:
            for j, entry in enumerate(trail):
                if not isinstance(entry, dict):
                    erros.append(f"{prefixo}.audit_trail[{j}]: deve ser objeto")
                    continue
                for field in ["stage", "timestamp", "action"]:
                    if field not in entry:
                        erros.append(f"{prefixo}.audit_trail[{j}].{field}: obrigatório")

    return erros


def validar_com_jsonschema(dados: dict, schema_path: Path) -> list[str]:
    """Validação com jsonschema."""
    erros = []
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(dados):
            erros.append(f"[jsonschema] {error.json_path}: {error.message}")
    except Exception as e:
        erros.append(f"Erro ao carregar/aplicar schema: {e}")
    return erros


def main():
    parser = argparse.ArgumentParser(
        description="Validador do Envelope Curado — Curador de Relevância"
    )
    parser.add_argument("--arquivo", "-a", required=True, help="JSON do envelope curado")
    parser.add_argument(
        "--schema", "-s", default=None,
        help="Caminho para schema_saida.json (opcional)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Exibir detalhes extras")
    args = parser.parse_args()

    # Carregar arquivo
    try:
        with open(args.arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"✗ Arquivo não encontrado: {args.arquivo}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"✗ JSON inválido: {e}")
        sys.exit(2)

    erros = []

    # Validação com jsonschema
    if args.schema:
        if not HAS_JSONSCHEMA:
            print("⚠ jsonschema não instalado. Usando validação estrutural interna...")
        else:
            if args.verbose:
                print(f"  Usando schema: {args.schema}")
            erros += validar_com_jsonschema(dados, Path(args.schema))

    # Sempre rodar validação estrutural
    erros += validar_envelope(dados)

    # Remover duplicatas mantendo ordem
    vistos = set()
    erros_unicos = []
    for e in erros:
        if e not in vistos:
            vistos.add(e)
            erros_unicos.append(e)

    if erros_unicos:
        print(f"\n✗ {len(erros_unicos)} erro(s) encontrado(s) em: {args.arquivo}\n")
        for e in erros_unicos:
            print(f"  • {e}")
        sys.exit(1)
    else:
        n = len(dados.get("pecas", []))
        meta = dados.get("metadata", {})
        print(f"✓ Envelope Curado válido — {n} peça(s) curada(s)")
        if args.verbose:
            print(f"  metadata.processo_id: {meta.get('processo_id', 'N/A')}")
            print(f"  metadata.gerado_por_curador: {meta.get('gerado_por_curador', 'N/A')}")
            print(f"  metadata.modo_aplicado: {meta.get('modo_aplicado', 'N/A')}")
            manter = sum(1 for p in dados["pecas"] if p.get("acao_curatorial") == "manter")
            revisar = sum(1 for p in dados["pecas"] if p.get("acao_curatorial") == "revisar")
            remover = sum(1 for p in dados["pecas"] if p.get("acao_curatorial") == "remover")
            resumir = sum(1 for p in dados["pecas"] if p.get("acao_curatorial") == "resumir")
            print(f"  manter={manter} resumir={resumir} remover={remover} revisar={revisar}")
        sys.exit(0)


if __name__ == "__main__":
    main()
