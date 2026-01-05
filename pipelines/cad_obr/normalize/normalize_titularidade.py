#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


# -----------------------------
# Config de normalização
# -----------------------------

MONTHS_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

# Chaves “explicitamente” de data (evita mexer em textos longos como detalhes_da_procuracao)
DATE_KEYS = {
    "data_assinatura",
    "data_registro",
    "data_efetiva",
    "data_baixa",
    "data_emissao",
    "data_posicao",
    "data_posicao_composicao",
    "data_celebracao",
    "data_valor",
    "vencimento",
    "vencimento_final",
    "primeiro_vencimento",
    "ultimo_vencimento",
    # usado em historico_aditivos[]
    "data",
}

# Chaves de identificadores
CPF_KEYS = {"cpf"}
CNPJ_KEYS = {"cnpj"}

# Números de contrato/documento/operação
NUM_KEYS = {"numero", "numero_contrato", "numero_documento"}


ISO_DATE_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")
DMY_SLASH_RE = re.compile(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\s*$")
LONG_PT_RE = re.compile(
    r"^\s*(\d{1,2})\s+de\s+([A-Za-zÀ-ÿçÇ]+)\s+de\s+([0-9\.\s]{2,6})\s*\.?\s*$",
    re.IGNORECASE,
)

# Para ano com 2 dígitos: pivot 30 -> <=30 vira 20xx; >30 vira 19xx
YY_PIVOT = 30


def _safe_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except Exception:
        return None


def normalize_digits_only(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def parse_date_to_iso(raw: str) -> Optional[str]:
    """
    Aceita:
      - YYYY-MM-DD
      - dd/mm/yyyy | dd-mm-yyyy
      - dd/mm/yy   | dd-mm-yy
      - "dd de mês de yyyy" (pt-BR), incluindo anos como "1.994" ou "2.003"
      - tolera ponto final no fim ("2001.")
    Retorna "YYYY-MM-DD" ou None se não parsear.
    """
    if not raw or not isinstance(raw, str):
        return None

    s = raw.strip()

    # 1) ISO
    m = ISO_DATE_RE.match(s)
    if m:
        yyyy, mm, dd = map(int, m.groups())
        try:
            return date(yyyy, mm, dd).isoformat()
        except Exception:
            return None

    # 2) dd/mm/yyyy ou dd/mm/yy
    m = DMY_SLASH_RE.match(s)
    if m:
        dd_s, mm_s, yy_s = m.groups()
        dd = _safe_int(dd_s)
        mm = _safe_int(mm_s)
        yy = _safe_int(yy_s)
        if dd is None or mm is None or yy is None:
            return None

        if yy < 100:
            yy = (2000 + yy) if yy <= YY_PIVOT else (1900 + yy)

        try:
            return date(yy, mm, dd).isoformat()
        except Exception:
            return None

    # 3) "dd de mês de yyyy" (com ano possivelmente "1.994")
    m = LONG_PT_RE.match(s)
    if m:
        dd_s, month_s, year_s = m.groups()
        dd = _safe_int(dd_s)
        if dd is None:
            return None

        month_key = month_s.strip().lower()
        # normaliza cedilha/variações mínimas
        month_key = month_key.replace("ç", "ç")  # noop, só para clareza
        if month_key not in MONTHS_PT:
            # tenta remover acentos básicos do "março"
            month_key_alt = month_key.replace("março", "marco")
            if month_key_alt in MONTHS_PT:
                month_key = month_key_alt
            else:
                return None
        mm = MONTHS_PT[month_key]

        # ano: remove tudo que não é dígito (pega "1.994" -> "1994", "2.003" -> "2003")
        year_digits = re.sub(r"\D+", "", year_s)
        if not year_digits:
            return None
        yy = _safe_int(year_digits)
        if yy is None:
            return None
        if yy < 100:
            yy = (2000 + yy) if yy <= YY_PIVOT else (1900 + yy)

        try:
            return date(yy, mm, dd).isoformat()
        except Exception:
            return None

    return None


def should_normalize_num(value: str) -> bool:
    """
    Normaliza para digits-only quando:
      - contém '.' (ex.: 176.700.530)
      - NÃO contém '/' (para não destruir 96/70042-4)
    """
    if not isinstance(value, str):
        return False
    s = value.strip()
    return ("." in s) and ("/" not in s)


@dataclass
class Stats:
    files_in: int = 0
    files_out: int = 0
    date_changed: int = 0
    cpf_changed: int = 0
    cnpj_changed: int = 0
    num_changed: int = 0


def normalize_object(obj: Any, stats: Stats) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            kl = k.lower()

            # datas (apenas por chave, não dentro de textos livres)
            if k in DATE_KEYS and isinstance(v, str):
                iso = parse_date_to_iso(v)
                if iso and iso != v:
                    out[k] = iso
                    stats.date_changed += 1
                    continue

            # cpf/cnpj
            if kl in CPF_KEYS and isinstance(v, str):
                nd = normalize_digits_only(v)
                if nd and nd != v:
                    out[k] = nd
                    stats.cpf_changed += 1
                    continue

            if kl in CNPJ_KEYS and isinstance(v, str):
                nd = normalize_digits_only(v)
                if nd and nd != v:
                    out[k] = nd
                    stats.cnpj_changed += 1
                    continue

            # números de documento/contrato (somente se for seguro)
            if k in NUM_KEYS and isinstance(v, str) and should_normalize_num(v):
                nd = normalize_digits_only(v)
                if nd and nd != v:
                    out[k] = nd
                    stats.num_changed += 1
                    continue

            out[k] = normalize_object(v, stats)
        return out

    if isinstance(obj, list):
        return [normalize_object(x, stats) for x in obj]

    return obj


def iter_input_files(input_path: Path, pattern: str) -> Iterable[Path]:
    if input_path.is_file():
        yield input_path
        return
    yield from input_path.rglob(pattern)


def ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Normaliza titularidade (datas + CPF/CNPJ + números pontuados) no pipeline CAD-OBR.")
    ap.add_argument("--input", required=True, help="Arquivo .json ou diretório de entrada")
    ap.add_argument("--output", required=True, help="Arquivo .json ou diretório de saída")
    ap.add_argument("--pattern", default="*.json", help="Glob de arquivos (quando --input é diretório). Default: *.json")
    ap.add_argument("--inplace", action="store_true", help="Permite sobrescrever no mesmo diretório/arquivo (usa temp + replace).")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise SystemExit(f"ERRO: input não existe: {in_path}")

    # Determina modo arquivo vs diretório
    in_is_file = in_path.is_file()
    out_is_file = out_path.suffix.lower() == ".json" or (in_is_file and not out_path.is_dir())

    # Segurança: impedir input==output sem --inplace
    if not args.inplace:
        try:
            if in_is_file and out_is_file and in_path.resolve() == out_path.resolve():
                raise SystemExit("ERRO: input e output são o mesmo arquivo. Use --inplace.")
            if (not in_is_file) and (not out_is_file):
                if in_path.resolve() == out_path.resolve():
                    raise SystemExit("ERRO: input e output são o mesmo diretório. Use --inplace.")
        except Exception:
            pass

    stats = Stats()

    # Processa
    files = list(iter_input_files(in_path, args.pattern))
    stats.files_in = len(files)

    for src in files:
        data = load_json(src)
        normalized = normalize_object(data, stats)

        if in_is_file and out_is_file:
            dst = out_path
        else:
            # preserva estrutura relativa se input for diretório
            rel = src.relative_to(in_path) if (not in_is_file) else Path(src.name)
            dst = out_path / rel

        if args.inplace:
            # escreve em temp e substitui
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            save_json(tmp, normalized)
            ensure_parent_dir(dst)
            shutil.move(str(tmp), str(dst))
        else:
            save_json(dst, normalized)

        stats.files_out += 1

    print("OK normalize_titularidade")
    print(f"- arquivos_in:  {stats.files_in}")
    print(f"- arquivos_out: {stats.files_out}")
    print(f"- datas_normalizadas: {stats.date_changed}")
    print(f"- cpf_normalizados:   {stats.cpf_changed}")
    print(f"- cnpj_normalizados:  {stats.cnpj_changed}")
    print(f"- numeros_normalizados: {stats.num_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
