"""
pipelines/cad_obr/normalize/normalize_valores.py

Normalização determinística de valores monetários (pt-BR) em documentos CAD-OBR.

Regras (contrato do pipeline):
- Strings monetárias SEM símbolo: "67.250,51"
- Campos numéricos em centavos (int):
  - hipotecas_onus[*].valor_divida_num
  - transacoes_venda[*].valor_num

Fontes e prioridade:
- hipotecas_onus[*]:
  1) valor_divida_original (se existir)
  2) valor_divida (se original ausente)
  - conversão CR$ -> R$: dividir por 2750 quando a fonte contiver "CR$"
- transacoes_venda[*]:
  - normaliza somente o campo "valor" (string) e cria "valor_num" (centavos)
  - se contiver "CR$": divide por 2750

Idempotente:
- Rodar novamente não deve degradar valores.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CR_TO_R_FACTOR = Decimal("2750")  # 1 R$ = 2.750 CR$


@dataclass
class NormalizeStats:
    files_total: int = 0
    files_written: int = 0

    onus_total: int = 0
    onus_normalized: int = 0
    onus_skipped_no_value: int = 0
    onus_skipped_parse_fail: int = 0

    vendas_total: int = 0
    vendas_normalized: int = 0
    vendas_skipped_no_value: int = 0
    vendas_skipped_parse_fail: int = 0


def detect_currency(text: str) -> Optional[str]:
    """
    Retorna "CR$" se houver CR$, "BRL" se houver R$/REAIS/REAL, ou None.
    """
    if not text:
        return None
    up = text.upper()
    if "CR$" in up:
        return "CR$"
    if "R$" in up or "REAIS" in up or "REAL" in up:
        return "BRL"
    return None


def parse_monetary_value(value: Any) -> Optional[Decimal]:
    """
    Extrai o PRIMEIRO valor monetário encontrado no texto e converte para Decimal.

    Suporta:
    - pt-BR: "93.354,27", "93354,27"
    - decimal por ponto: "93354.27", "93,354.27"
    - ignora texto por extenso e demais ruídos: "R$93.354,27-(noventa e três mil, ...)"
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    s = str(value).strip()
    if not s:
        return None

    # 1) pt-BR com vírgula decimal (com ou sem milhar)
    m = re.search(r"(\d{1,3}(?:\.\d{3})+,\d{2}|\d+,\d{2})", s)
    if m:
        num_str = m.group(1)
        num_str = num_str.replace(".", "").replace(",", ".")
        try:
            return Decimal(num_str)
        except Exception:
            return None

    # 2) decimal por ponto (com ou sem milhar estilo US)
    m = re.search(r"(\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2})", s)
    if m:
        num_str = m.group(1).replace(",", "")
        try:
            return Decimal(num_str)
        except Exception:
            return None

    # 3) inteiro simples (fallback)
    m = re.search(r"(\d+)", s)
    if m:
        try:
            return Decimal(m.group(1))
        except Exception:
            return None

    return None


def quantize_2(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_to_centavos(amount_reais: Decimal) -> int:
    """
    Converte Decimal em reais para int em centavos com arredondamento HALF_UP.
    """
    q = quantize_2(amount_reais)
    cent = (q * 100).to_integral_value(rounding=ROUND_HALF_UP)
    return int(cent)


def format_brl_no_symbol(amount_reais: Decimal) -> str:
    """
    Formata Decimal em reais para string pt-BR sem símbolo:
    67250.51 -> "67.250,51"
    """
    q = quantize_2(amount_reais)
    sign = "-" if q < 0 else ""
    q = abs(q)

    s = format(q, "f")
    if "." not in s:
        s += ".00"
    integer, frac = s.split(".", 1)
    frac = (frac + "00")[:2]

    chunks: List[str] = []
    while integer:
        chunks.append(integer[-3:])
        integer = integer[:-3]
    integer_fmt = ".".join(reversed(chunks)) if chunks else "0"

    return f"{sign}{integer_fmt},{frac}"


def normalize_onus_item(item: Dict[str, Any], stats: NormalizeStats) -> bool:
    """
    Normaliza um item de hipotecas_onus:
    - valor_divida (string BR sem símbolo)
    - valor_divida_num (int centavos)
    Fonte: valor_divida_original (prioridade) -> valor_divida
    """
    val_orig = (item.get("valor_divida_original") or "").strip()
    val_atual = (item.get("valor_divida") or "").strip()

    source = val_orig if val_orig else val_atual
    if not source:
        stats.onus_skipped_no_value += 1
        return False

    currency = detect_currency(source) or detect_currency(val_orig) or detect_currency(val_atual)

    dec = parse_monetary_value(source)
    if dec is None:
        stats.onus_skipped_parse_fail += 1
        return False

    reais = (dec / CR_TO_R_FACTOR) if currency == "CR$" else dec
    reais_q = quantize_2(reais)

    item["valor_divida"] = format_brl_no_symbol(reais_q)
    item["valor_divida_num"] = decimal_to_centavos(reais_q)

    stats.onus_normalized += 1
    return True


def normalize_venda_item(item: Dict[str, Any], stats: NormalizeStats) -> bool:
    """
    Normaliza transacoes_venda[*].valor:
    - valor: string BR sem símbolo
    - valor_num: int centavos
    """
    val = (item.get("valor") or "").strip()
    if not val:
        stats.vendas_skipped_no_value += 1
        return False

    currency = detect_currency(val)
    dec = parse_monetary_value(val)
    if dec is None:
        stats.vendas_skipped_parse_fail += 1
        return False

    reais = (dec / CR_TO_R_FACTOR) if currency == "CR$" else dec
    reais_q = quantize_2(reais)

    item["valor"] = format_brl_no_symbol(reais_q)
    item["valor_num"] = decimal_to_centavos(reais_q)

    stats.vendas_normalized += 1
    return True


def normalize_document(doc: Dict[str, Any], stats: NormalizeStats) -> bool:
    """
    Normaliza:
    - doc["hipotecas_onus"] (lista)
    - doc["transacoes_venda"] (lista)
    """
    changed_any = False

    onus = doc.get("hipotecas_onus")
    if isinstance(onus, list):
        for it in onus:
            if isinstance(it, dict):
                stats.onus_total += 1
                changed_any = normalize_onus_item(it, stats) or changed_any

    vendas = doc.get("transacoes_venda")
    if isinstance(vendas, list):
        for it in vendas:
            if isinstance(it, dict):
                stats.vendas_total += 1
                changed_any = normalize_venda_item(it, stats) or changed_any

    return changed_any


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def process_directory(input_dir: Path, output_dir: Path, glob_pattern: str = "*.json") -> NormalizeStats:
    stats = NormalizeStats()

    if input_dir.resolve() == output_dir.resolve():
        raise ValueError("input_dir e output_dir não podem ser o mesmo caminho (evita sobrescrita acidental).")

    files = sorted(input_dir.glob(glob_pattern))
    stats.files_total = len(files)

    for in_path in files:
        try:
            doc = load_json(in_path)
        except Exception as e:
            print(f"[WARN] Falha ao ler JSON: {in_path.name} ({e})")
            continue

        _ = normalize_document(doc, stats)

        out_path = output_dir / in_path.name
        save_json(out_path, doc)
        stats.files_written += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize valores monetários (ônus + transações de venda) para pt-BR sem símbolo e centavos.")
    parser.add_argument("--input", required=True, help="Diretório de entrada com JSONs do Collector (ex.: outputs/cad-obr/01_collector/escritura_imovel)")
    parser.add_argument("--output", required=True, help="Diretório de saída (ex.: outputs/cad-obr/02_normalize/escritura_imovel)")
    parser.add_argument("--pattern", default="*.json", help="Glob de arquivos (default: *.json)")

    args = parser.parse_args()
    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Diretório de entrada não encontrado: {input_dir}")

    stats = process_directory(input_dir, output_dir, glob_pattern=args.pattern)

    print("=== NORMALIZE_VALORES: RESUMO ===")
    print(f"Arquivos encontrados:      {stats.files_total}")
    print(f"Arquivos escritos:        {stats.files_written}")

    print(f"Ônus avaliados:           {stats.onus_total}")
    print(f"Ônus normalizados:        {stats.onus_normalized}")
    print(f"Ônus sem valor (skip):    {stats.onus_skipped_no_value}")
    print(f"Ônus parse falhou (skip): {stats.onus_skipped_parse_fail}")

    print(f"Vendas avaliadas:         {stats.vendas_total}")
    print(f"Vendas normalizadas:      {stats.vendas_normalized}")
    print(f"Vendas sem valor (skip):  {stats.vendas_skipped_no_value}")
    print(f"Vendas parse falhou:      {stats.vendas_skipped_parse_fail}")


if __name__ == "__main__":
    main()
