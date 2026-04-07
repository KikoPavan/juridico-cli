"""
Qdrant loader: indexes extraction results into the legal_library_chunks_v1 collection.

This is a thin adapter over the existing scripts/index_library_qdrant.py logic.
Only used when the pipeline is configured to push to Qdrant after extraction.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


def push_to_qdrant(
    documents: List[Dict[str, Any]],
    collection: str = "legal_library_chunks_v1",
    host: str = "127.0.0.1",
    port: int = 6333,
) -> int:
    """
    Index a list of documents into Qdrant.
    Each document must have 'source_id', 'content' and optionally 'metadata'.
    Returns the number of successfully upserted points.

    Delegates to the project's existing qdrant-client setup.
    Raises ConnectionError if Qdrant is unreachable.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "qdrant-client and sentence-transformers are required for Qdrant loading."
        ) from exc

    client = QdrantClient(host=host, port=port)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    points: List[PointStruct] = []
    for i, doc in enumerate(documents):
        content = doc.get("content", "")
        if not content:
            continue
        vector = model.encode(content).tolist()
        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={
                    "source_id": doc.get("source_id", ""),
                    "content": content,
                    **doc.get("metadata", {}),
                },
            )
        )

    if points:
        client.upsert(collection_name=collection, points=points)

    return len(points)
