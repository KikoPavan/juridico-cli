import sys
import os
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def test_loader():
    loader_path = os.path.join(os.getcwd(), 'platform', 'skill-runtime', 'bundle_loader.py')
    bundle_loader_mod = load_module_from_path('bundle_loader', loader_path)
    BundleLoader = bundle_loader_mod.BundleLoader
    
    loader = BundleLoader()
    payload = loader.load_bundle_payload("extr-dummy")
    
    print("=== DUMMY BUNDLE VALIDATION ===")
    print("Bundle Name:", payload["bundle_name"])
    print("Frontmatter Length:", len(payload.get("frontmatter", {})))
    print("System Prompt snippet (transversal logic injected):")
    prompt = payload.get("system_prompt", "")
    print(prompt[:150], "...\n")
    print("Schema Type:", type(payload.get("schema")))
    print("Has 'nome' in schema?", "nome" in payload.get("schema", {}).get("properties", {}))
    print("===============================\n")

if __name__ == "__main__":
    test_loader()
