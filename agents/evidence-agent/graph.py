from langgraph.graph import END, StateGraph
from nodes import (
    assemble_evidence_node,
    clarify_goal_node,
    rag_proof_node,
    scan_deterministic_node,
)
from state import ReconcilerState


def create_reconciler_graph():
    # Inicializa o Grafo
    workflow = StateGraph(ReconcilerState)

    # Adiciona os Nós
    workflow.add_node("clarify", clarify_goal_node)
    workflow.add_node("scan", scan_deterministic_node)
    workflow.add_node("rag", rag_proof_node)
    workflow.add_node("assemble", assemble_evidence_node)

    # Define as Arestas (Fluxo Sequencial)
    workflow.set_entry_point("clarify")
    workflow.add_edge("clarify", "scan")
    workflow.add_edge("scan", "rag")
    workflow.add_edge("rag", "assemble")
    workflow.add_edge("assemble", END)

    # Compila
    app = workflow.compile()
    return app
