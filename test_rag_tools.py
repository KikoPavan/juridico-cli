import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path("mcp-server-cad-obr").absolute()))

from rag_tools import search_laws, semantic_search


def test_rag():
    print("--- Testing semantic_search('fraude') ---")
    results = semantic_search("fraude", property_id="matricula:7013")
    print(f"Results: {len(results)}")
    if results:
        print(f"First result content: {results[0].get('content')}")
        print(f"Metadata: {results[0].get('metadata')}")

    print("\n--- Testing search_laws('codigo civil') ---")
    laws = search_laws("codigo civil")
    print(f"Laws found: {len(laws)}")


if __name__ == "__main__":
    test_rag()
