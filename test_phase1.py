import sys
import os
import yaml
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def test_phase_1():
    # 1. Test LLM Agnóstico
    print("=== TESTE: CLIENTE LLM AGNÓSTICO ===")
    
    # Path manual para contornar o hífen em "shared-llm" ou uso sem framework
    loader_path = os.path.join(os.getcwd(), 'packages', 'shared-llm', 'client.py')
    client_mod = load_module_from_path('client_mod', loader_path)
    DummyLLMClient = client_mod.DummyLLMClient
    
    client = DummyLLMClient()
    dummy_schema = {"type": "object", "properties": {"extracted_value": {"type": "string"}}}
    
    text_res = client.generate_text([{"role": "user", "content": "Extract"}])
    struct_res = client.generate_structured([{"role": "user", "content": "Extract structured"}], dummy_schema)
    
    print("Output Genérico Textual:", text_res)
    print("Output Estruturado (Dict/JSON aderente):", struct_res)
    assert "mock_extracted_value" == struct_res["extracted_value"]
    print("✓ Interface Abstrata de LLM opera limpa.")
    
    # 2. Test Registrar (YAML)
    print("\n=== TESTE: REGISTRO DE LLM E SKILLS ===")
    with open("platform/skill-runtime/llm_registry.yaml", "r") as f:
        llms = yaml.safe_load(f)

    with open("platform/skill-runtime/skill_registry.yaml", "r") as f:
        skills = yaml.safe_load(f)
        
    print("LLM Fallback Model:", llms.get("fallback_model"))
    print("Contrato Social Prefered Model:", skills["skills"]["extr-contrato-social"]["preferred_model"])
    schema_ref = skills["skills"]["extr-contrato-social"]["schema_ref"]
    print("Reference to Schema:", schema_ref)
    
    # 3. Validando existẽncia da Schema centralizada (Sem quebrar a Legada que deve continuar lá)
    print("\n=== TESTE: COMPATIBILIDADE DE SCHEMAS CENTRALIZADAS E ROOT LEGADO ===")
    assert os.path.exists(schema_ref), f"A Schema {schema_ref} gerida pelo Registry não existe no Package!"
    assert os.path.exists("schemas/contrato_social.schema.json"), "A schema legado na RAIZ SUMIU! Deveria estar mantido pra compatibilidade do ambiente de root!"
    
    print("✓ Todas as copias foram instanciadas. Suporte passivo preservado.")

if __name__ == "__main__":
    test_phase_1()
