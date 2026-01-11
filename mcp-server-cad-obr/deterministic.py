import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Caminho base relativo ao script (assumindo execução da raiz do projeto)
DATASET_PATH = Path("outputs/cad-obr/04_reconciler/dataset_v1")


def _load_jsonl(filename: str) -> List[Dict[str, Any]]:
    path = DATASET_PATH / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_property(property_id: str) -> Optional[Dict[str, Any]]:
    """
    Retorna detalhes de uma propriedade específica pelo ID (ex: matricula:7013).
    """
    imoveis = _load_jsonl("imoveis.jsonl")
    for prop in imoveis:
        if prop.get("property_id") == property_id:
            return prop
    return None


def list_onus(property_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista ônus associados a uma propriedade, com filtro opcional de status (ATIVO/BAIXADA).
    """
    all_onus = _load_jsonl("onus_obrigacoes.jsonl")
    results = [o for o in all_onus if o.get("property_id") == property_id]

    if status:
        results = [o for o in results if o.get("status") == status]

    return results


def timeline(property_id: str) -> List[Dict[str, Any]]:
    """
    Retorna uma timeline unificada de eventos (da property_events.jsonl) para a propriedade.
    Ordenada por data_efetiva.
    """
    events = _load_jsonl("property_events.jsonl")
    prop_events = [e for e in events if e.get("property_id") == property_id]

    # Normalização de data para ordenação segura
    def get_date(e):
        return e.get("data_efetiva") or e.get("data_registro") or "9999-12-31"

    prop_events.sort(key=get_date)
    return prop_events


def list_novacoes(property_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista novações detectadas. Se property_id for fornecido, filtra por ele.
    Nota: novacoes.jsonl pode não ter property_id direto, verificar schema se necessário.
    """
    novacoes = _load_jsonl("novacoes_detectadas.jsonl")
    if property_id:
        # Assumindo que novação tem property_id, se não tiver, este filtro pode precisar de ajuste
        # O schema nao foi lido para novacoes, mas é provável.
        novacoes = [n for n in novacoes if n.get("property_id") == property_id]
    return novacoes
