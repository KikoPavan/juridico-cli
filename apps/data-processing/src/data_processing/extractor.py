import os
import sys
import json
import argparse
from datetime import datetime

def load_module_from_path(module_name, file_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Instanciar provedores agnósticos sem acoplamento a pipelines/ ou legacy
client_mod = load_module_from_path('client_mod', os.path.join(os.getcwd(), 'packages', 'shared-llm', 'client.py'))
LLMClientFactory = client_mod.LLMClientFactory

class DataExtractorApp:
    """
    Novo orquestrador funcional V1.1 sob `apps/data-processing/`.
    Lida exclusivamente com a estrutura padronizada de `var/` para I/O.
    """
    def __init__(self, platform_path="platform", var_dir="var", staging_path=None):
        self.platform_path = platform_path
        self.var_dir = var_dir

        # Paths obrigatórios V1.1
        self.dirs = {
            "input_md": os.path.join(self.var_dir, "input", "md"),
            "staging": staging_path if staging_path else os.path.join(self.var_dir, "staging"),
            "output": os.path.join(self.var_dir, "output"),
            "logs": os.path.join(self.var_dir, "logs")
        }

        for d in self.dirs.values():
            os.makedirs(d, exist_ok=True)
            
        # Instanciar dispatcher canônico (caminho real de resolução de skills)
        dispatcher_path = os.path.join(self.platform_path, 'skill-runtime', 'skill_dispatcher.py')
        dispatcher_mod = load_module_from_path('skill_dispatcher', dispatcher_path)
        self.dispatcher = dispatcher_mod.SkillDispatcher(platform_path=self.platform_path)

    def log(self, message: str, run_id: str):
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}\n"
        log_file = os.path.join(self.dirs["logs"], f"extraction_{run_id}.log")
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(log_line)
        print(message)

    def run_extraction(self, bundle_id: str, input_filename: str):
        # Gerar ID da run
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log(f"=== INICIANDO EXTRAÇÃO V1.1: {run_id} ===", run_id)
        
        # Leitura diretamente de staging (1:1), já limpo
        staging_path = os.path.join(self.dirs["staging"], input_filename)
        if not os.path.exists(staging_path):
            self.log(f"[ERRO] Arquivo não encontrado em staging: {staging_path}", run_id)
            sys.exit(1)
            
        with open(staging_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Parse do Frontmatter
        frontmatter = {}
        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    raw_text = parts[2].strip()
                except Exception as e:
                    self.log(f"[AVISO] Falha ao fazer parser do frontmatter: {e}", run_id)
                    
        self.log(f"Lido de staging 1:1: {staging_path} | Metadados: {frontmatter}", run_id)

        # 2. Despachar via runtime canônico
        try:
            dispatch_result = self.dispatcher.dispatch(bundle_id)
        except ValueError as e:
            self.log(f"[ERRO] {e}", run_id)
            sys.exit(1)

        skill_config = dispatch_result["skill_config"]
        system_prompt = dispatch_result["system_prompt"]
        schema_path = skill_config["schema_ref"]

        with open(schema_path, "r", encoding="utf-8") as sf:
            schema_json = json.load(sf)

        self.log(f"Profile: {skill_config.get('profile')} | Schema: {schema_path}", run_id)
        self.log(f"Instrução carregada com sucesso (Tamanho: {len(system_prompt)} chars)", run_id)
        
        # 4. Processamento LLM Agnóstico
        client = LLMClientFactory.create_client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ]
        
        self.log(f"Enviando dados para processamento...", run_id)
        response = client.generate_structured(messages, schema=schema_json)
        
        # 5. Output Final
        out_filename = f"result_{bundle_id}_{input_filename.split('.')[0]}.json"
        out_path = os.path.join(self.dirs["output"], out_filename)
        
        with open(out_path, "w", encoding="utf-8") as outf:
            json.dump(response, outf, indent=2, ensure_ascii=False)
            
        self.log(f"Extração concluída com sucesso! Resultado em: {out_path}", run_id)
        return out_path
