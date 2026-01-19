import sys
from pathlib import Path

# Adiciona o diretório raiz ao sys.path para importar scripts
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from scripts.rag_service import RAGService

# Instância única do serviço (Mock por enquanto)
_rag_service = RAGService()


def semantic_search(query: str, property_id: str = None) -> list[dict]:
    """
    Realiza busca semântica por evidências.
    Args:
        query: Texto da busca.
        property_id: (Opcional) Filtra por matrícula.
    """
    filters = {}
    if property_id:
        filters["property_id"] = property_id

    return _rag_service.search_evidencias_caso(query, filters)


def search_laws(query: str) -> list[dict]:
    """
    Busca na base normativa (leis/artigos).
    """
    return _rag_service.search_base_normativa(query)


def search_jurisprudence(query: str) -> list[dict]:
    """
    Busca na base de jurisprudência.
    """
    return _rag_service.search_jurisprudencia(query)
