"""
Módulo: monetary_core.py
Fase 1 – motor de cálculo para cad-obr (sem índices externos ainda).

Responsabilidades principais:
- processar_documento_cad_obr(doc): aplica o cálculo em todos os itens de `hipotecas_onus`.
- processar_onus_cad_obr(onus): aplica as regras R1–R2, R4–R8, R11, R13 em um único ônus.

Política atual:
- Arrendamento mercantil / leasing: NUNCA calcula valor_presente (R2).
- Só calcula quando há:
  - data_efetiva,
  - data_baixa,
  - valor_divida em R$,
  - taxa anual identificável em `taxas`.
- Ainda não usa CSV de índices (Fase 2).
"""

import csv
import os
import re
import math
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple, List
from datetime import date


# ------------------------------------------------------------
# Utilitários de parsing
# ------------------------------------------------------------

MESES_PTBR = {
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


def parse_data_ptbr(data_str: Optional[str]) -> Optional[date]:
    """
    Converte datas em português para objeto date.

    Suporta formatos como:
      - "24 de Fevereiro de 1999"
      - "24 de abril de 1.996"
      - "2001-03-29" (ISO)

    Retorna None se não conseguir interpretar.
    """
    if not data_str:
        return None

    s = data_str.strip()

    # Tenta primeiro formato ISO (YYYY-MM-DD)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            from datetime import date as _date

            year, month, day = map(int, s.split("-"))
            return _date(year, month, day)
    except Exception:
        pass

    # Formato "24 de Abril de 1.996"
    # Captura: dia, mês (texto), ano (com ou sem ponto de milhar)
    m = re.search(
        r"(\d{1,2})\s+de\s+([A-Za-zçÇáàâãéêíóôõúüÁÀÂÃÉÊÍÓÔÕÚÜ]+)\s+de\s+([\d\.]{2,6})",
        s,
    )
    if not m:
        return None

    dia_str, mes_str, ano_str = m.groups()
    try:
        dia = int(dia_str)
    except ValueError:
        return None

    mes_nome = mes_str.strip().lower()
    mes = MESES_PTBR.get(mes_nome)
    if not mes:
        return None

    # Remove pontos do ano (ex.: "1.996" -> "1996")
    ano_digits = re.sub(r"[^\d]", "", ano_str)
    if len(ano_digits) == 2:
        # Heurística simples: "94" -> 1994
        ano = 1900 + int(ano_digits)
    elif len(ano_digits) == 4:
        ano = int(ano_digits)
    else:
        return None

    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


def parse_valor_brl(valor_str: Optional[str]) -> Optional[float]:
    """
    Converte textos como:
      - "R$60.000,00"
      - "R$ 58.181,82"
      - "R$60.000,00-(sessenta mil reais)"
    em float (ex.: 60000.00).

    Retorna None se não encontrar padrão monetário.
    """
    if not valor_str:
        return None

    # Procura o primeiro padrão XX.XXX,YY
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", valor_str)
    if not m:
        return None

    num = m.group(1)
    # Remove separador de milhar e troca vírgula por ponto
    num = num.replace(".", "").replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def extrair_taxa_anual(taxas_str: Optional[str]) -> tuple[Optional[float], str]:
    """
    Tenta extrair uma taxa de juros a partir do texto de `taxas`.

    Suporta:
      - juros anuais: "juros de 12,680% efetivos ao ano"
      - juros mensais: "juros de 4,40% ao mês"

    Retorna:
      (taxa_decimal, tipo_taxa), onde:
        - taxa_decimal: ex.: 0.1268 para "12,68% a.a." ou 0.044 para "4,4% a.m."
        - tipo_taxa: "anual", "mensal", "desconhecida", "ausente"
    """
    if not taxas_str:
        return None, "ausente"

    texto = taxas_str.strip()
    texto_lower = texto.lower()

    # Flags de unidade
    eh_mensal = ("ao mês" in texto_lower) or ("ao mes" in texto_lower) or ("mensal" in texto_lower)
    eh_anual = (
        ("ao ano" in texto_lower)
        or ("anual" in texto_lower)
        or ("anuais" in texto_lower)
        or ("efetivos ao ano" in texto_lower)
    )

    # 1) Tenta número seguido de "%"
    m = re.search(r"(\d{1,3}(?:[.,]\d{1,3})?)\s*%", texto)
    if not m:
        # 2) Sem "%": tenta pegar número perto de "juros"
        m = re.search(r"juros[^0-9]{0,15}(\d{1,3}(?:[.,]\d{1,3})?)", texto_lower)

    if not m:
        # não encontrou número
        return (None, "desconhecida" if (eh_anual or eh_mensal) else "ausente")

    taxa_str = m.group(1).strip()

    # Normalização:
    # - "12,680" -> "12.680"
    # - "12.680" -> "12.680"
    if "," in taxa_str and "." not in taxa_str:
        taxa_norm = taxa_str.replace(".", "").replace(",", ".")
    elif "." in taxa_str and "," not in taxa_str:
        taxa_norm = taxa_str
    else:
        # casos estranhos: remove tudo que não for dígito e usa como inteiro
        taxa_norm = re.sub(r"[^\d]", "", taxa_str)

    try:
        taxa_percent = float(taxa_norm)
    except ValueError:
        return None, "desconhecida"

    # Proteção contra taxas absurdas (parser mal-sucedido)
    if taxa_percent <= 0 or taxa_percent > 200:
        return None, "desconhecida"

    taxa_decimal = taxa_percent / 100.0

    # Decide o tipo
    if eh_mensal and not eh_anual:
        return taxa_decimal, "mensal"
    if eh_anual and not eh_mensal:
        return taxa_decimal, "anual"

    # Se tiver ambos marcados ou nenhum, não vamos chutar
    return None, "desconhecida"


def formatar_valor_brl(valor: float) -> str:
    """
    Formata um float em string monetária brasileira SEM símbolo, ex.:

      60000.0  -> "60.000,00"
      84918.88 -> "84.918,88"
    """
    sign = "-" if valor < 0 else ""
    centavos = int(round(abs(valor) * 100))
    inteiro = centavos // 100
    frac = centavos % 100

    parte_inteira = f"{inteiro:,}".replace(",", ".")
    return f"{sign}{parte_inteira},{frac:02d}"


# ------------------------------------------------------------
# Núcleo de regras cad-obr
# ------------------------------------------------------------


def _inicializar_meta() -> Dict[str, Any]:
    """Cria estrutura básica de _monetary_meta."""
    return {
        "calculado": False,
        "motivo": None,
        "regra_aplicada": None,
        "tipo_taxa_detectado": None,
        "detalhes_calculo": {},
    }


@lru_cache(maxsize=1)
def carregar_tr_mensal(csv_path: str) -> Dict[Tuple[int, int], float]:
    """
    Carrega tabela TR mensal no formato Bacen (uma linha por ano, colunas 01..12)
    e devolve um dicionário {(ano, mes): tr_decimal}.

    Observação importante:
    - Muitos CSVs do Bacen trazem TR em "percentual" (ex.: 0,07 = 0,07%).
    - O motor precisa de fração (ex.: 0,0007).
    - Heurística: se |TR| > 0.02, assume que veio em % e divide por 100.
      (TR em fração normalmente fica bem abaixo disso.)
    """
    tabela: Dict[Tuple[int, int], float] = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return tabela

        col_ano = reader.fieldnames[0]

        mes_cols = [c for c in reader.fieldnames[1:] if c and c.strip().isdigit()]

        for row in reader:
            ano_txt = (row.get(col_ano) or "").strip()
            if not ano_txt.isdigit():
                continue

            ano = int(ano_txt)

            for mes_col in mes_cols:
                txt = (row.get(mes_col) or "").strip()
                if not txt:
                    continue

                # normaliza: vírgula → ponto
                txt = txt.replace(" ", "").replace(",", ".")

                try:
                    tr_val = float(txt)
                except ValueError:
                    continue

                # Heurística % -> fração (ex.: 0,07% => 0,0007)
                if abs(tr_val) > 0.02:
                    tr_val = tr_val / 100.0

                try:
                    mes = int(mes_col)
                except ValueError:
                    continue

                tabela[(ano, mes)] = tr_val

    return tabela


def iter_meses_periodo(inicio: date, fim: date) -> List[Tuple[int, int]]:
    """
    Devolve lista [(ano, mes)] para todos os meses do período,
    do mês de 'inicio' até o mês de 'fim' (inclusive).
    """
    meses: List[Tuple[int, int]] = []
    ano, mes = inicio.year, inicio.month

    while (ano, mes) <= (fim.year, fim.month):
        meses.append((ano, mes))
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

    return meses


def processar_onus_cad_obr(
    onus: Dict[str, Any],
    tr_table: Optional[Dict[Tuple[int, int], float]] = None,
) -> Dict[str, Any]:
    """
    Processa um único item de hipoteca/ônus de matrícula (cad-obr),
    aplicando:
      - regras já existentes de juros (taxa efetiva anual ou mensal),
      - e, se aplicável, correção pela TR mensal acumulada.
    """
    meta = _inicializar_meta()

    # 1) Filtra arrendamento mercantil / leasing (não calcula valor_presente)
    tipo = (onus.get("tipo_divida") or "").upper()
    if "ARRENDAMENTO MERCANTIL" in tipo or "LEASING" in tipo:
        meta["calculado"] = False
        meta["motivo"] = "tipo_divida_arrendamento_mercantil"
        meta["regra_aplicada"] = "R2"
        onus["valor_presente"] = None
        onus["valor_presente_num"] = None
        onus["_monetary_meta"] = meta
        return onus

    # 2) Datas básicas
    data_efetiva_str = onus.get("data_efetiva")
    data_baixa_str = onus.get("data_baixa")
    quitada = onus.get("quitada")
    cancelada = onus.get("cancelada")

    dt_efetiva = parse_data_ptbr(data_efetiva_str)
    dt_baixa = parse_data_ptbr(data_baixa_str)

    if dt_efetiva is None:
        meta["motivo"] = "dados_insuficientes_para_calculo: data_efetiva_ausente_ou_invalida"
        meta["regra_aplicada"] = "R13"
        onus.setdefault("valor_presente", None)
        onus["_monetary_meta"] = meta
        return onus

    # Baixa/quitada sem data_baixa → não calcula
    if (quitada is True or cancelada is True) and dt_baixa is None:
        meta["motivo"] = "sem_data_baixa_para_baixa_quitada"
        meta["regra_aplicada"] = "R5"
        onus.setdefault("valor_presente", None)
        onus["_monetary_meta"] = meta
        return onus

    # Não baixada e sem data_baixa → ainda em aberto, não calcula
    if dt_baixa is None and not (quitada is True or cancelada is True):
        meta["motivo"] = "divida_sem_baixa_no_cad-obr"
        meta["regra_aplicada"] = "R6"
        onus.setdefault("valor_presente", None)
        onus["_monetary_meta"] = meta
        return onus

    # Qualquer outro caso com dt_baixa ausente → impossível calcular
    if dt_baixa is None:
        meta["motivo"] = "dados_insuficientes_para_calculo: data_baixa_ausente"
        meta["regra_aplicada"] = "R13"
        onus.setdefault("valor_presente", None)
        onus["_monetary_meta"] = meta
        return onus

    # Sanidade: baixa antes da data efetiva
    if dt_baixa < dt_efetiva:
        meta["motivo"] = "datas_inconsistentes: data_baixa_antes_de_data_efetiva"
        meta["regra_aplicada"] = "R11"
        onus.setdefault("valor_presente", None)
        onus["_monetary_meta"] = meta
        return onus
    

    # 3) Valor base (capital) – prioridade: valor_divida_num (centavos)
    valor_base = None
    valor_base_centavos = None

    # 3.1) Canônico: centavos (gerado pelo normalize)
    if isinstance(onus.get("valor_divida_num"), int):
        valor_base_centavos = int(onus["valor_divida_num"])
        valor_base = valor_base_centavos / 100.0

    # 3.2) Compatibilidade (legado): valor_divida_numero em reais
    elif isinstance(onus.get("valor_divida_numero"), (int, float)):
        valor_base = float(onus["valor_divida_numero"])
        valor_base_centavos = int(round(valor_base * 100))

    # 3.3) Fallback: parse da string (valor_divida)
    else:
        valor_base = parse_valor_brl(onus.get("valor_divida"))
        if valor_base is not None:
            valor_base_centavos = int(round(valor_base * 100))

    if valor_base is None:
        meta["motivo"] = "dados_insuficientes_para_calculo: valor_divida_invalido_ou_ausente"
        meta["regra_aplicada"] = "R13"
        onus.setdefault("valor_presente", None)
        onus.setdefault("valor_presente_num", None)
        onus["_monetary_meta"] = meta
        return onus


    # 4) Taxa de juros (já na forma decimal) e tipo ("anual" ou "mensal")
    taxa_decimal, tipo_taxa = extrair_taxa_anual(onus.get("taxas"))
    meta["tipo_taxa_detectado"] = tipo_taxa

    if taxa_decimal is None or tipo_taxa not in ("anual", "mensal"):
        meta["motivo"] = "taxa_nao_suportada"
        meta["regra_aplicada"] = "R8"
        onus.setdefault("valor_presente", None)
        onus["_monetary_meta"] = meta
        return onus

    dias_decorridos = (dt_baixa - dt_efetiva).days

    # 4.1) Fator de juros (mantém lógica existente)
    if tipo_taxa == "anual":
        taxa_anual = taxa_decimal
        if taxa_anual <= -1.0:
            meta["motivo"] = "taxa_anual_invalida_para_juros_compostos"
            meta["regra_aplicada"] = "R8"
            onus.setdefault("valor_presente", None)
            onus["_monetary_meta"] = meta
            return onus

        n_anos = dias_decorridos / 365.0
        fator_juros = math.pow(1.0 + taxa_anual, n_anos)
        regime_juros = "composto_anual_simples_dias_365"

    else:  # "mensal"
        taxa_mensal = taxa_decimal
        if taxa_mensal <= -1.0:
            meta["motivo"] = "taxa_mensal_invalida_para_juros_compostos"
            meta["regra_aplicada"] = "R8"
            onus.setdefault("valor_presente", None)
            onus["_monetary_meta"] = meta
            return onus

        n_meses = dias_decorridos / 30.0
        fator_juros = math.pow(1.0 + taxa_mensal, n_meses)
        regime_juros = "composto_mensal_mes_comercial"

    # 5) TR mensal composta (se o texto de taxas mencionar TR / Taxa Referencial)
    taxas_str = (onus.get("taxas") or "").lower()
    usa_tr = (
        " tr" in taxas_str
        or "taxa referencial" in taxas_str
        or "correção pela tr" in taxas_str
        or "correcao pela tr" in taxas_str
    )
    meta["usa_tr"] = usa_tr

    fator_tr = 1.0
    tr_meses_sem_dado: List[str] = []
    periodo_tr = None

    if usa_tr:
        if tr_table is None:
            meta["tr_aplicada"] = False
            meta["tr_motivo"] = "tr_csv_nao_carregado"
        else:
            meses_periodo = iter_meses_periodo(dt_efetiva, dt_baixa)
            periodo_tr = {
                "inicio": f"{dt_efetiva.year}-{dt_efetiva.month:02d}",
                "fim": f"{dt_baixa.year}-{dt_baixa.month:02d}",
                "total_meses": len(meses_periodo),
            }

            for ano, mes in meses_periodo:
                key = (ano, mes)
                tr_val = tr_table.get(key)
                if tr_val is None:
                    tr_meses_sem_dado.append(f"{ano}-{mes:02d}")
                    continue
                fator_tr *= (1.0 + tr_val)

            if tr_meses_sem_dado:
                # Aplicamos TR onde havia índice; meses sem dado são assumidos com TR=0,
                # mas listados em meta para rastreabilidade.
                meta["tr_aplicada"] = True
                meta["tr_motivo"] = "tr_aplicada_com_meses_sem_indice"
            else:
                meta["tr_aplicada"] = True
                meta["tr_motivo"] = None

    # 6) Montante final = capital * juros * TR
    valor_presente_float = valor_base * fator_juros * fator_tr
    valor_presente_centavos = int(round(valor_presente_float * 100))

    onus["valor_presente"] = formatar_valor_brl(valor_presente_float)
    onus["valor_presente_num"] = valor_presente_centavos

    meta["calculado"] = True
    meta["motivo"] = None
    meta["regra_aplicada"] = "R7"

    detalhe: Dict[str, Any] = {
        "data_inicial_utilizada": dt_efetiva.isoformat(),
        "data_final_utilizada": dt_baixa.isoformat(),
        "dias_decorridos": dias_decorridos,
        "regime_juros": regime_juros,

        # numéricos canônicos (centavos)
        "valor_base_centavos": valor_base_centavos,
        "valor_presente_centavos": valor_presente_centavos,

        # leitura humana (float em reais)
        "valor_base_num": round(valor_base, 2) if valor_base is not None else None,
        "valor_presente_num": round(valor_presente_float, 2),
    }


    if tipo_taxa == "anual":
        detalhe["tipo_taxa"] = "anual"
        detalhe["taxa_percentual_anual"] = round(taxa_decimal * 100, 6)
    else:
        detalhe["tipo_taxa"] = "mensal"
        detalhe["taxa_percentual_mensal"] = round(taxa_decimal * 100, 6)

    if usa_tr:
        detalhe["regime_tr"] = "tr_mensal_composta"
        detalhe["tr_fator_total"] = round(fator_tr, 10)
        detalhe["tr_meses_sem_dado"] = tr_meses_sem_dado
        detalhe["tr_periodo"] = periodo_tr

    meta["detalhes_calculo"] = detalhe
    onus["_monetary_meta"] = meta
    return onus


def processar_documento_cad_obr(
    doc: Dict[str, Any],
    tr_csv_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Processa o documento completo (matrícula) aplicando as regras de cálculo
    a todos os itens em `hipotecas_onus`.

    - Se `tr_csv_path` for informado, usa esse caminho para a TR.
    - Caso contrário, tenta usar o caminho padrão:
        data/indices/Tabela_bacen_TR.csv

    Se o arquivo não existir ou der erro de leitura, os cálculos seguem
    apenas com juros (sem TR), e os metadados indicam o motivo.
    """
    # resolve caminho da TR
    tr_table: Optional[Dict[Tuple[int, int], float]] = None

    if tr_csv_path:
        candidato = tr_csv_path
    else:
        candidato = os.path.join("data", "indices", "Tabela_bacen_TR.csv")

    if os.path.isfile(candidato):
        try:
            tr_table = carregar_tr_mensal(os.path.abspath(candidato))
        except Exception:
            tr_table = None  # falha de leitura → segue sem TR

    onus_list = doc.get("hipotecas_onus")
    if not isinstance(onus_list, list):
        return doc

    novos_onus: List[Dict[str, Any]] = []
    for item in onus_list:
        if isinstance(item, dict):
            novos_onus.append(processar_onus_cad_obr(item, tr_table=tr_table))
        else:
            novos_onus.append(item)

    doc["hipotecas_onus"] = novos_onus
    return doc
