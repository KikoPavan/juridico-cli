#!/usr/bin/env python3
"""
regras.py — Motor de regras de negócio do Curador de Relevância
Projeto: juridico-cli / skill: curador-relevancia

Catálogo de regras:
  R00 — Capa processual administrativa → remover
  R00B — Tipo sem extrator reconhecido → revisar
  R01 — Nuclear com sentença confirmada → manter
  R02 — Tipo documental protegido → manter
  R03 — Fallback: baixa confiança → revisar
  R04 — Prova documental (flag) → manter
  R05 — Representação processual → manter
  R06 — Alta relevância (padrao) → manter
  R07 — Modo sintético: alta relevância → manter
  R08 — Despacho de expediente → remover (padrao) / remover (sintetico)
  R09 — Certidão de prazo irrelevante → remover
  R10 — Duplicata suspeita → revisar
  R11 — Peça acessória longa (padrao) → resumir
  R12 — Modo sintético: acessório → resumir cabecalho_apenas
  R13 — Fallback geral padrao → manter
  R14 — Fallback geral sintetico → resumir
"""

from typing import Any

# ── Limiares de configuração ─────────────────────────────────────────────────
LIMIARES = {
    "padrao": {
        "relevancia_manter": 0.40,
        "relevancia_remover": 0.30,
        "confianca_minima": 0.60,
        "paginas_resumir": 3,
    },
    "sintetico": {
        "relevancia_manter": 0.60,
        "relevancia_remover": 0.40,
        "confianca_minima": 0.60,
        "paginas_resumir": 1,
    },
}

# Tipos documentais cujos documentos NUNCA devem ser removidos
TIPOS_PROTEGIDOS = {
    "peticao_inicial",
    "contestacao",
    "sentenca",
    "acordao",
    "laudo_pericial",
    "procuracao",
    "recurso",
    "ata_audiencia",
    "decisao_interlocutoria",
}

# Tipos que podem ser removidos se irrelevantes
TIPOS_REMOVIVEIS = {
    "despacho",
    "certidao",
    "intimacao",
}

TIPOS_COM_EXTRATOR = {
    "peticao_inicial", "contestacao", "sentenca", "decisao", "decisao_interlocutoria",
    "despacho", "laudo_pericial", "procuracao", "mandato", "recurso", "contrato",
}


def _relevancia(p: dict) -> float:
    return float(p.get("relevancia_estimada", 0.0))


def _confianca(p: dict) -> float:
    return float(p.get("confianca_classificacao", 1.0))


def _flags(p: dict) -> dict:
    return p.get("flags", {})


def _sinais(p: dict) -> list:
    return p.get("sinais_relevancia", [])


def _paginas(p: dict) -> int:
    """Calcula total de páginas da peça a partir de pages_start/pages_end/pages_total."""
    pt = p.get("pages_total")
    if pt is not None and isinstance(pt, int):
        return pt
    ps = p.get("pages_start")
    pe = p.get("pages_end")
    if ps is not None and pe is not None:
        return pe - ps + 1
    # Fallback: tenta ler do formato antigo paginas
    pg = p.get("paginas", {})
    return int(pg.get("total", 1))


def _tipo(p: dict) -> str | None:
    return p.get("document_type")


def _impacto(p: dict) -> str | None:
    return p.get("impacto_processual")


def _confirmado(p: dict) -> bool:
    return bool(p.get("impacto_sentenca_confirmado", False))


def _resultado(acao, regra, gatilhos, justificativa,
               compressao=None, override=False, override_motivo=None) -> dict:
    return {
        "acao_curatorial": acao,
        "regra_aplicada": regra,
        "gatilhos": gatilhos,
        "justificativa_curta": justificativa[:120],
        "compressao_sugerida": compressao,
        "override_aplicado": override,
        "override_motivo": override_motivo,
    }


# ── Regras universais (aplicadas antes de qualquer modo) ─────────────────────

def r01_nuclear_confirmado(p: dict) -> dict | None:
    if _confirmado(p):
        return _resultado(
            "manter", "R01_nuclear_sentenca_confirmado",
            ["impacto_sentenca_confirmado=true"],
            f"Impacto na sentença confirmado; tipo={_tipo(p)} preservado obrigatoriamente.",
        )
    return None


def r00_capa_processo_administrativa(p: dict) -> dict | None:
    if _tipo(p) == "capa_processo":
        return _resultado(
            "remover", "R00_capa_processo_administrativa",
            ["document_type=capa_processo", "peca_administrativa"],
            "Capa processual administrativa sem conteúdo útil à sentença; remoção rastreada.",
        )
    return None


def r00b_tipo_sem_extrator(p: dict) -> dict | None:
    tipo = _tipo(p)
    if tipo not in TIPOS_COM_EXTRATOR:
        return _resultado(
            "revisar", "R00B_tipo_sem_extrator",
            [f"document_type={tipo}", "encaminhamento_extrator=null"],
            f"Tipo {tipo or 'nulo'} sem extrator reconhecido; encaminhado à revisão segura.",
            override=True,
            override_motivo="Ausência de rota extr-* reconhecida",
        )
    return None


def r02_tipo_protegido(p: dict) -> dict | None:
    tipo = _tipo(p)
    if tipo in TIPOS_PROTEGIDOS:
        return _resultado(
            "manter", "R02_tipo_documental_protegido",
            [f"document_type={tipo}", "tipo_em_lista_protegida"],
            f"{tipo} é tipo protegido; remoção vedada por regra de segurança jurídica.",
        )
    return None


def r03_fallback_baixa_confianca(p: dict) -> dict | None:
    conf = _confianca(p)
    tipo = _tipo(p)
    limiar = LIMIARES["padrao"]["confianca_minima"]  # universal
    if conf < limiar or tipo is None:
        motivo = "document_type=null" if tipo is None else f"confianca={conf:.2f}<{limiar}"
        return _resultado(
            "revisar", "R03_fallback_baixa_confianca",
            [motivo],
            f"Classificação incerta (confiança={conf:.2f}); escalado para revisão humana.",
            override=True,
            override_motivo="Confiança abaixo do limiar de segurança — revisão humana obrigatória",
        )
    return None


def r04_prova_documental(p: dict) -> dict | None:
    if _flags(p).get("prova_documental"):
        return _resultado(
            "manter", "R04_prova_documental_protegida",
            ["flag.prova_documental=true"],
            "Prova documental: remoção vedada pelo princípio do contraditório.",
        )
    return None


def r05_representacao_processual(p: dict) -> dict | None:
    if _flags(p).get("representacao_processual"):
        return _resultado(
            "manter", "R05_representacao_processual_protegida",
            ["flag.representacao_processual=true"],
            "Representação processual protegida; documento essencial ao processo.",
        )
    return None


def r10_duplicata(p: dict) -> dict | None:
    if _flags(p).get("duplicata_suspeita"):
        return _resultado(
            "revisar", "R10_duplicata_suspeita",
            ["flag.duplicata_suspeita=true"],
            "Possível duplicata detectada; requer confirmação humana antes de remover.",
        )
    return None


# ── Regras modo `padrao` ──────────────────────────────────────────────────────

def r06_padrao_alta_relevancia(p: dict) -> dict | None:
    limiar = LIMIARES["padrao"]["relevancia_manter"]
    rel = _relevancia(p)
    if rel >= limiar:
        return _resultado(
            "manter", "R06_padrao_alta_relevancia",
            [f"relevancia={rel:.2f}>={limiar}", "modo=padrao"],
            f"Relevância {rel:.2f} acima do limiar {limiar}; mantido no modo padrão.",
        )
    return None


def r08_padrao_despacho_expediente(p: dict) -> dict | None:
    tipo = _tipo(p)
    rel = _relevancia(p)
    limiar = LIMIARES["padrao"]["relevancia_remover"]
    if tipo == "despacho" and rel < limiar and _flags(p).get("prazo_expirado", False):
        return _resultado(
            "remover", "R08_despacho_expediente_prazo_expirado",
            ["document_type=despacho", f"relevancia<{limiar}", "flag.prazo_expirado=true"],
            f"Despacho de expediente com prazo expirado; relevância {rel:.2f} — descarte justificado.",
        )
    return None


def r09_padrao_certidao_irrelevante(p: dict) -> dict | None:
    tipo = _tipo(p)
    rel = _relevancia(p)
    limiar = LIMIARES["padrao"]["relevancia_remover"]
    if tipo == "certidao" and rel < limiar and _flags(p).get("prazo_expirado", False):
        return _resultado(
            "remover", "R09_certidao_prazo_irrelevante",
            ["document_type=certidao", f"relevancia<{limiar}", "flag.prazo_expirado=true"],
            f"Certidão de prazo expirado; relevância {rel:.2f} abaixo do limiar — descarte justificado.",
        )
    return None


def r11_padrao_acessorio_longo(p: dict) -> dict | None:
    impacto = _impacto(p)
    paginas = _paginas(p)
    limiar_pg = LIMIARES["padrao"]["paginas_resumir"]
    if impacto in ("acessorio",) and paginas > limiar_pg:
        return _resultado(
            "resumir", "R11_padrao_acessorio_longo",
            [f"impacto_processual=acessorio", f"paginas={paginas}>{limiar_pg}"],
            f"Peça acessória com {paginas} páginas; compressão para resumo de 1 página sugerida.",
            compressao="resumo_1p",
        )
    return None


def r13_padrao_fallback(p: dict) -> dict:
    rel = _relevancia(p)
    return _resultado(
        "manter", "R13_padrao_fallback_geral",
        [f"relevancia={rel:.2f}", "modo=padrao", "sem_regra_especifica"],
        f"Nenhuma regra específica aplicável; mantido por conservadorismo do modo padrão.",
    )


# ── Regras modo `sintetico` ───────────────────────────────────────────────────

def r07_sintetico_alta_relevancia(p: dict) -> dict | None:
    limiar = LIMIARES["sintetico"]["relevancia_manter"]
    rel = _relevancia(p)
    if rel >= limiar:
        return _resultado(
            "manter", "R07_sintetico_alta_relevancia",
            [f"relevancia={rel:.2f}>={limiar}", "modo=sintetico"],
            f"Relevância {rel:.2f} acima do limiar sintético {limiar}; mantido.",
        )
    return None


def r08s_sintetico_despacho(p: dict) -> dict | None:
    tipo = _tipo(p)
    rel = _relevancia(p)
    limiar = LIMIARES["sintetico"]["relevancia_remover"]
    if tipo in ("despacho", "intimacao") and rel < limiar:
        return _resultado(
            "remover", "R08S_sintetico_despacho_intimacao",
            [f"document_type={tipo}", f"relevancia<{limiar}", "modo=sintetico"],
            f"{tipo} com relevância {rel:.2f} abaixo do limiar sintético — descartado.",
        )
    return None


def r09s_sintetico_certidao(p: dict) -> dict | None:
    tipo = _tipo(p)
    rel = _relevancia(p)
    limiar = LIMIARES["sintetico"]["relevancia_remover"]
    if tipo == "certidao" and rel < limiar:
        return _resultado(
            "remover", "R09S_sintetico_certidao",
            ["document_type=certidao", f"relevancia<{limiar}", "modo=sintetico"],
            f"Certidão com relevância {rel:.2f} — descartada no modo sintético.",
        )
    return None


def r12_sintetico_acessorio(p: dict) -> dict | None:
    impacto = _impacto(p)
    rel = _relevancia(p)
    limiar_rem = LIMIARES["sintetico"]["relevancia_remover"]
    limiar_man = LIMIARES["sintetico"]["relevancia_manter"]
    if impacto in ("acessorio", "irrelevante") or (rel < limiar_man and rel >= limiar_rem):
        return _resultado(
            "resumir", "R12_sintetico_acessorio_comprimido",
            [f"impacto_processual={impacto}", f"relevancia={rel:.2f}", "modo=sintetico"],
            f"Peça acessória no modo sintético; comprimida para cabeçalho apenas.",
            compressao="cabecalho_apenas",
        )
    return None


def r14_sintetico_fallback(p: dict) -> dict:
    rel = _relevancia(p)
    return _resultado(
        "resumir", "R14_sintetico_fallback_geral",
        [f"relevancia={rel:.2f}", "modo=sintetico", "sem_regra_especifica"],
        f"Fallback sintético: peça não classificada comprimida para revisão de cabeçalho.",
        compressao="cabecalho_apenas",
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────

REGRAS_UNIVERSAIS = [
    r01_nuclear_confirmado,
    r00_capa_processo_administrativa,
    r00b_tipo_sem_extrator,
    r04_prova_documental,
    r05_representacao_processual,
    r02_tipo_protegido,
    r10_duplicata,
    r03_fallback_baixa_confianca,
]

REGRAS_PADRAO = [
    r08_padrao_despacho_expediente,
    r09_padrao_certidao_irrelevante,
    r11_padrao_acessorio_longo,
    r06_padrao_alta_relevancia,
]

REGRAS_SINTETICO = [
    r08s_sintetico_despacho,
    r09s_sintetico_certidao,
    r07_sintetico_alta_relevancia,
    r12_sintetico_acessorio,
]


def aplicar_regras(peca: dict, modo: str) -> dict:
    """
    Aplica a cadeia de regras na ordem correta para o modo especificado.
    Retorna o resultado da primeira regra que disparar.
    """
    # 1. Regras universais (proteções de segurança jurídica)
    for regra in REGRAS_UNIVERSAIS:
        resultado = regra(peca)
        if resultado is not None:
            return resultado

    # 2. Regras específicas do modo
    regras_modo = REGRAS_PADRAO if modo == "padrao" else REGRAS_SINTETICO
    for regra in regras_modo:
        resultado = regra(peca)
        if resultado is not None:
            return resultado

    # 3. Fallback do modo
    if modo == "padrao":
        return r13_padrao_fallback(peca)
    else:
        return r14_sintetico_fallback(peca)
