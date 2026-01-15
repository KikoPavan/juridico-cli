import sys
from pathlib import Path
from typing import Any, Dict

from state import ReconcilerState

# --- MCP Tool Integration (Fallback Strategy: Direct Import) ---
# Adiciona o diretório do repo ao path para permitir imports do mcp-server-cad-obr
# Caminho: agents/reconciler-cli/nodes.py -> ROOT = ../../../
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    # Tentativa de achar o root dinamicamente se a estrutura mudar
    # Estrutura esperada: <root>/agents/reconciler-cli/nodes.py
    sys.path.append(str(ROOT_DIR))

# Adiciona o diretório do server especificamente para import direto dos módulos
SERVER_DIR = ROOT_DIR / "mcp-server-cad-obr"
if str(SERVER_DIR) not in sys.path:
    # Prioridade para o diretório do servidor
    sys.path.insert(0, str(SERVER_DIR))

from deterministic import get_property, list_onus, timeline
from rag_tools import semantic_search

# --- Nodes ---


def clarify_goal_node(state: ReconcilerState) -> Dict[str, Any]:
    """
    Normaliza o objetivo. V1: Apenas loga e prepara estruturas.
    """
    print(f"[Node: Clarify] Starting analysis for {state['target_property']}")
    return {"evidence": {"facts": [], "snippets": [], "gaps": []}}


def scan_deterministic_node(state: ReconcilerState) -> Dict[str, Any]:
    """
    Busca dados estruturados (imóvel, onus, linha do tempo).
    """
    prop_id = state["target_property"]
    print(f"[Node: Scan] Querying deterministic tools for {prop_id}")

    # Busca Propriedade
    prop_data = get_property(prop_id)
    if not prop_data:
        return {"evidence": {"gaps": [f"Property {prop_id} not found in dataset"]}}

    # Busca Onus
    onus_list = list_onus(prop_id)

    # Busca Timeline
    timeline_events = timeline(prop_id)

    # Compila Fatos
    facts = []
    if prop_data:
        facts.append({"type": "property_info", "data": prop_data})
    for o in onus_list:
        facts.append({"type": "onus", "data": o})
    for t in timeline_events:
        facts.append({"type": "event", "data": t})

    return {
        "evidence": {
            "facts": facts,
            "snippets": state["evidence"].get("snippets", []),
            "gaps": state["evidence"].get("gaps", []),
        }
    }


def rag_proof_node(state: ReconcilerState) -> Dict[str, Any]:
    """
    Busca evidências literais para corroborar (ou expandir) a hipótese.
    """
    hypothesis = state.get("hypothesis", "")
    prop_id = state["target_property"]

    if not hypothesis:
        return {}  # Sem hipótese, sem busca extra

    print(f"[Node: RAG] Searching evidence for hypothesis: '{hypothesis}'")
    results = semantic_search(hypothesis, property_id=prop_id)

    snippets = []
    for r in results:
        snippets.append(
            {
                "content": r.get("content"),
                "source": r.get("metadata", {}).get("source_id"),
                "score": r.get("score"),
            }
        )

    return {
        "evidence": {
            "facts": state["evidence"]["facts"],
            "snippets": snippets,
            "gaps": state["evidence"]["gaps"],
        }
    }


def assemble_evidence_node(state: ReconcilerState) -> Dict[str, Any]:
    """
    Compila o relatório final (JSON/MD).
    """
    evidence = state["evidence"]
    facts_count = len(evidence.get("facts", []))
    snippets_count = len(evidence.get("snippets", []))

    print(
        f"[Node: Assemble] Finished. Facts: {facts_count}, Snippets: {snippets_count}"
    )

    # Aqui poderia salvar o arquivo em disco, por enquanto retorna no estado
    return {"final_report_path": "memory_only_v1"}
