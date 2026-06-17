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
            "input_clean": os.path.join(self.var_dir, "output", "processed"),
            "input_md_frontmatter": os.path.join(self.var_dir, "output", "md-frontmatter-yaml"),
            "input_processed_fm_legacy": os.path.join(self.var_dir, "output", "processed_fm"),
            "output": os.path.join(self.var_dir, "output"),
            "extracted": os.path.join(self.var_dir, "output", "extracted"),
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
        
        # Tenta ler preferencialmente da pasta md-frontmatter-yaml, com fallbacks
        input_path_fm = os.path.join(self.dirs["input_md_frontmatter"], input_filename)
        input_path_clean = os.path.join(self.dirs["input_clean"], input_filename)
        input_path_fm_legacy = os.path.join(self.dirs["input_processed_fm_legacy"], input_filename)
        
        if os.path.exists(input_path_fm):
            input_path = input_path_fm
            self.log(f"Entrada enriquecida localizada em md-frontmatter-yaml: {input_path}", run_id)
        elif os.path.exists(input_path_clean):
            input_path = input_path_clean
            self.log(f"Entrada com frontmatter não localizada. Usando fallback limpo: {input_path}", run_id)
        elif os.path.exists(input_path_fm_legacy):
            input_path = input_path_fm_legacy
            self.log(f"[FALLBACK LEGADO] Entrada localizada em processed_fm (remover em migração futura): {input_path}", run_id)
        else:
            self.log(f"[ERRO] Arquivo não encontrado em md-frontmatter-yaml, processed nem processed_fm: {input_filename}", run_id)
            sys.exit(1)
            
        with open(input_path, "r", encoding="utf-8") as f:
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
                    
        self.log(f"Lido de: {input_path} | Metadados: {frontmatter}", run_id)

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
        
        # 4. Processamento LLM Agnóstico — usa provider e model do llm_profile
        llm_profile = dispatch_result.get("llm_profile", {})
        execution_class_key = llm_profile.get("execution_class", "")
        provider = None
        if execution_class_key:
            llm_reg_path = os.path.join(self.platform_path, "skill-runtime", "llm_registry.yaml")
            try:
                with open(llm_reg_path, "r") as f:
                    import yaml as _yaml
                    llm_reg = _yaml.safe_load(f)
                exec_class = llm_reg.get("execution_classes", {}).get(execution_class_key, {})
                provider = exec_class.get("provider")
            except Exception:
                pass
        model = llm_profile.get("model")
        client = LLMClientFactory.create_client(provider_override=provider, model_override=model)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ]
        
        effective_model = model or getattr(client, 'model_name', 'unknown')
        self.log(f"Usando provider: {provider or 'gemini'} | model: {effective_model}", run_id)
        self.log(f"Enviando dados para processamento...", run_id)
        response = client.generate_structured(messages, schema=schema_json)
        
        failed_blocks = response.pop("_failed_blocks", []) if isinstance(response, dict) else []
        
        # 5. Output Final — salva em var/output/extracted/
        out_filename = f"result_{bundle_id}_{input_filename.split('.')[0]}.json"
        out_path = os.path.join(self.dirs["extracted"], out_filename)
        
        with open(out_path, "w", encoding="utf-8") as outf:
            json.dump(response, outf, indent=2, ensure_ascii=False)
            
        if failed_blocks:
            self.log(f"⚠️ Extração concluída com ressalvas! Blocos que falharam: {', '.join(failed_blocks)}. Resultado em: {out_path}", run_id)
        else:
            self.log(f"Extração concluída com sucesso! Resultado em: {out_path}", run_id)
        return out_path
