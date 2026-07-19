#!/usr/bin/env python3
"""
curar.py — Engine principal do Curador de Relevância
Projeto: juridico-cli / skill: curador-relevancia

Entrada: Envelope de Processo {metadata, pecas[]} do segmentador-juridico
Saída:   Envelope Curado {metadata, pecas[]} — mesmas peças enriquecidas com campos curatoriais
"""

import json
import argparse
import sys
import os
import copy
import re
from datetime import datetime, timezone

from regras import aplicar_regras


TIPOS_IMPACTO_PROTEGIDO = {
    "peticao_inicial", "contestacao", "decisao", "decisao_interlocutoria",
    "sentenca", "recurso",
}
_JUDICIAL_LOCATOR_RE = re.compile(r"\[\[judicial_locator:\s*(.*?)\]\]")
_JUDICIAL_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def _first_non_null(*values):
    return next((value for value in values if value is not None and value != ""), None)


def _locator_attrs(text: str) -> dict:
    match = _JUDICIAL_LOCATOR_RE.search(text or "")
    return dict(_JUDICIAL_ATTR_RE.findall(match.group(1))) if match else {}


def canonicalizar_rastreabilidade(peca: dict, metadata: dict | None = None) -> dict:
    """Preserva os campos judiciais e canonicaliza paginação/anchors."""
    metadata = metadata or {}
    peca["pages_start"] = _first_non_null(
        peca.get("pages_start"), peca.get("page_number_start"),
        peca.get("start_page"), peca.get("pagina_inicio"),
    )
    peca["pages_end"] = _first_non_null(
        peca.get("pages_end"), peca.get("page_number_end"),
        peca.get("end_page"), peca.get("pagina_fim"),
    )
    locator = _locator_attrs(peca.get("text", ""))
    process_number = _first_non_null(
        peca.get("process_number"), peca.get("processo_id"),
        metadata.get("process_number"), metadata.get("processo_id"),
        locator.get("process_number"),
    )
    event = _first_non_null(
        peca.get("event"), peca.get("event_id"),
        metadata.get("event"), metadata.get("event_id"), locator.get("event"),
    )
    document_code = _first_non_null(
        peca.get("document_code"), metadata.get("document_code"),
        locator.get("document_code"),
    )
    if process_number is not None:
        peca["process_number"] = process_number
    if event is not None:
        peca["event"] = event
    if document_code is not None:
        peca["document_code"] = document_code

    anchors = peca.get("anchors") or [{
        "label": peca.get("document_type", "desconhecido"),
        "page": peca.get("pages_start") or 1,
    }]
    for anchor in anchors:
        if anchor.get("page") is None:
            anchor["page"] = peca.get("pages_start") or 1
        if process_number is not None:
            anchor.setdefault("process_number", process_number)
        if event is not None:
            anchor.setdefault("event", event)
        if document_code is not None:
            anchor.setdefault("document_code", document_code)
    peca["anchors"] = anchors
    return peca


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def calcular_impacto(peca: dict) -> str:
    """Determina impacto_processual a partir da peça, com fallback por relevancia_estimada."""
    impacto = peca.get("impacto_processual")
    if impacto in ("nuclear", "relevante", "acessorio"):
        return impacto
    if peca.get("document_type") in TIPOS_IMPACTO_PROTEGIDO:
        return "relevante"
    if impacto == "irrelevante":
        return impacto
    rel = peca.get("relevancia_estimada", 0.0)
    if rel >= 0.85:
        return "nuclear"
    elif rel >= 0.55:
        return "relevante"
    elif rel >= 0.30:
        return "acessorio"
    return "irrelevante"


def calcular_prioridade(acao: str, impacto: str, confirmado: bool) -> int:
    """Mapeia ação + impacto para prioridade 1–5."""
    if confirmado or impacto == "nuclear":
        return 1
    mapa = {
        ("manter", "relevante"): 2,
        ("manter", "acessorio"): 3,
        ("resumir", "relevante"): 2,
        ("resumir", "acessorio"): 3,
        ("revisar", "relevante"): 3,
        ("revisar", "acessorio"): 3,
        ("revisar", "irrelevante"): 4,
        ("remover", "acessorio"): 4,
        ("remover", "irrelevante"): 5,
    }
    return mapa.get((acao, impacto), 4)


def mapear_encaminhamento(document_type: str | None, acao: str) -> str | None:
    """Sugere skill extr-* destino com base no tipo documental."""
    if acao in ("remover",):
        return None
    mapa = {
        "peticao_inicial":        "extr-peticao-processo",
        "contestacao":            "extr-contestacao-processo",
        "sentenca":               "extr-decisao-processo",
        "decisao_interlocutoria": "extr-decisao-processo",
        "despacho":               "extr-decisao-processo",
        "laudo_pericial":         "extr-laudo-pericial",
        "procuracao":             "extr-procuracao",
        "mandato":                "extr-mandato-processo",
        "recurso":                "extr-recurso-processo",
        "contrato":               "extr-contrato-social",
    }
    return mapa.get(document_type or "", None)


def _build_audit_entry_curator(acao: str, regra: str, gatilhos: list,
                                peca: dict, override: bool, override_motivo: str | None) -> dict:
    """Constrói uma AuditEntry do curador."""
    return {
        "stage": "curador-relevancia",
        "timestamp": _timestamp(),
        "action": "decisao_curatorial_aplicada",
        "notes": (
            f"acao={acao}; regra={regra}; "
            f"relevancia={peca.get('relevancia_estimada')}; "
            f"confianca={peca.get('confianca_classificacao')}"
            + (f"; override={override_motivo}" if override else "")
        ),
    }


class CuradorRelevancia:
    def __init__(self, modo: str = "padrao"):
        if modo not in ("padrao", "sintetico"):
            raise ValueError(f"Modo inválido: '{modo}'. Use 'padrao' ou 'sintetico'.")
        self.modo = modo

    def _enrich_peca(self, peca: dict, metadata: dict | None = None) -> dict:
        """Aplica curadoria a uma peça e retorna a peça enriquecida."""
        peca = canonicalizar_rastreabilidade(copy.deepcopy(peca), metadata)
        ts = _timestamp()
        piece_id = peca.get("piece_id", "desconhecido")

        try:
            resultado = aplicar_regras(peca, self.modo)
        except Exception as exc:
            # Fallback de segurança: qualquer erro → revisar
            peca_enriched = copy.deepcopy(peca)
            peca_enriched["acao_curatorial"] = "revisar"
            peca_enriched["justificativa_curta"] = f"Erro de processamento: {str(exc)[:80]}"
            peca_enriched["impacto_processual"] = "acessorio"
            peca_enriched["impacto_sentenca_confirmado"] = peca.get("impacto_sentenca_confirmado", False)
            peca_enriched["prioridade"] = 3
            peca_enriched["compressao_sugerida"] = None
            peca_enriched["encaminhamento"] = None
            peca_enriched["modo_aplicado"] = self.modo
            peca_enriched["audit_trail"] = [
                _build_audit_entry_curator(
                    "revisar", "R_ERRO_PROCESSAMENTO", ["excecao_interna"],
                    peca, True, f"Erro interno: {str(exc)[:60]}"
                )
            ]
            return peca_enriched

        acao = resultado["acao_curatorial"]
        override = resultado.get("override_aplicado", False)
        impacto = calcular_impacto(peca)
        confirmado = peca.get("impacto_sentenca_confirmado", False)

        # Override de segurança: impacto_sentenca_confirmado → sempre manter
        override_motivo = None
        if confirmado and acao in ("remover", "resumir"):
            override = True
            override_motivo = "impacto_sentenca_confirmado=true: preservação obrigatória"
            acao = "manter"
            resultado["compressao_sugerida"] = None

        prioridade = calcular_prioridade(acao, impacto, confirmado)
        encaminhamento = mapear_encaminhamento(peca.get("document_type"), acao)

        # Copiar peça original e adicionar campos curatoriais
        peca_enriched = copy.deepcopy(peca)
        peca_enriched["acao_curatorial"] = acao
        peca_enriched["justificativa_curta"] = resultado["justificativa_curta"]
        peca_enriched["impacto_processual"] = impacto
        peca_enriched["impacto_sentenca_confirmado"] = confirmado
        peca_enriched["prioridade"] = prioridade
        peca_enriched["compressao_sugerida"] = resultado.get("compressao_sugerida")
        peca_enriched["encaminhamento"] = encaminhamento
        peca_enriched["modo_aplicado"] = self.modo

        # Construir audit_trail como array
        audit_entrada = peca.get("audit_trail", [])
        if not isinstance(audit_entrada, list):
            audit_entrada = []

        audit_curador = _build_audit_entry_curator(
            acao, resultado["regra_aplicada"], resultado["gatilhos"],
            peca, override, override_motivo
        )
        peca_enriched["audit_trail"] = audit_entrada + [audit_curador]

        return peca_enriched

    def processar(self, entrada: dict) -> dict:
        """Processa Envelope de Processo e retorna Envelope Curado."""
        inicio = datetime.now(timezone.utc)
        meta_entrada = entrada.get("metadata", {})
        pecas = entrada.get("pecas", [])

        pecas_curadas = [self._enrich_peca(p, meta_entrada) for p in pecas]

        duracao = int((datetime.now(timezone.utc) - inicio).total_seconds() * 1000)

        # Preservar metadata original e enriquecer com campos do curador
        metadata_saida = copy.deepcopy(meta_entrada)
        metadata_saida["modo_curadoria"] = meta_entrada.get("modo_curadoria", self.modo)
        metadata_saida["modo_aplicado"] = self.modo
        metadata_saida["duracao_ms"] = duracao
        metadata_saida["versao_schema"] = "1.1.0"
        metadata_saida["gerado_por_curador"] = "curador-relevancia"

        return {
            "metadata": metadata_saida,
            "pecas": pecas_curadas,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Curador de Relevância — juridico-cli"
    )
    parser.add_argument(
        "--entrada", "-e", required=True,
        help="Caminho para o Envelope de Processo (output do segmentador-juridico)"
    )
    parser.add_argument(
        "--saida", "-s", default=None,
        help="Caminho para o Envelope Curado de saída"
    )
    parser.add_argument(
        "--modo", "-m", default=None,
        choices=["padrao", "sintetico"],
        help="Modo de curadoria"
    )
    parser.add_argument(
        "--indent", type=int, default=2,
        help="Indentação do JSON de saída (padrão: 2)"
    )
    args = parser.parse_args()

    try:
        with open(args.entrada, "r", encoding="utf-8") as f:
            entrada = json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {args.entrada}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERRO: JSON inválido em {args.entrada}: {e}", file=sys.stderr)
        sys.exit(1)

    modo = (
        args.modo
        or entrada.get("metadata", {}).get("modo_curadoria")
        or os.environ.get("CURADOR_MODO")
        or "padrao"
    )

    curador = CuradorRelevancia(modo=modo)
    resultado = curador.processar(entrada)
    saida_json = json.dumps(resultado, ensure_ascii=False, indent=args.indent)

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(saida_json)
        pecas = resultado.get("pecas", [])
        manter = sum(1 for p in pecas if p.get("acao_curatorial") == "manter")
        resumir = sum(1 for p in pecas if p.get("acao_curatorial") == "resumir")
        remover = sum(1 for p in pecas if p.get("acao_curatorial") == "remover")
        revisar = sum(1 for p in pecas if p.get("acao_curatorial") == "revisar")
        print(f"✓ Curadoria concluída → {args.saida}", file=sys.stderr)
        print(f"  {len(pecas)} peças: manter={manter} resumir={resumir} remover={remover} revisar={revisar}",
              file=sys.stderr)
    else:
        print(saida_json)


if __name__ == "__main__":
    main()
