import sys

from deterministic import DATASET_PATH, get_property, list_novacoes, list_onus, timeline
from mcp.server.fastmcp import FastMCP

# Validate data path exists
if not DATASET_PATH.exists():
    print(
        f"WARNING: Dataset path not found at {DATASET_PATH.absolute()}", file=sys.stderr
    )

# Inicializa o servidor MCP
mcp = FastMCP("cad-obr")


@mcp.tool()
def list_datasets() -> list[str]:
    """
    List available datasets in the cad-obr output directory.
    """
    if not DATASET_PATH.exists():
        return ["Error: Dataset path not found"]
    return [p.name for p in DATASET_PATH.glob("*.jsonl")]


# Register deterministic tools
mcp.add_tool(get_property)
mcp.add_tool(list_onus)
mcp.add_tool(timeline)
mcp.add_tool(list_novacoes)

# Register RAG tools
from rag_tools import search_jurisprudence, search_laws, semantic_search

mcp.add_tool(semantic_search)
mcp.add_tool(search_laws)
mcp.add_tool(search_jurisprudence)

if __name__ == "__main__":
    mcp.run()
