import sys
from pathlib import Path

# Add current directory to path so we can import modules
sys.path.append(str(Path("mcp-server-cad_obr").absolute()))

from deterministic import get_property, list_onus, timeline


def test_tools():
    print("--- Testing get_property('matricula:7013') ---")
    prop = get_property("matricula:7013")
    print(f"Found: {prop is not None}")
    if prop:
        print(f"Docs Origem: {len(prop.get('docs_origem', []))}")

    print("\n--- Testing list_onus('matricula:7013') ---")
    onus_list = list_onus("matricula:7013")
    print(f"Count: {len(onus_list)}")
    if onus_list:
        print(f"First Onus ID: {onus_list[0].get('onus_id')}")

    print("\n--- Testing timeline('matricula:7013') ---")
    tl = timeline("matricula:7013")
    print(f"Events: {len(tl)}")
    if tl:
        print(
            f"First Event Date: {tl[0].get('data_efetiva') or tl[0].get('data_registro')}"
        )


if __name__ == "__main__":
    test_tools()
