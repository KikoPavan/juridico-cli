import os
import json
import yaml

class BundleLoader:
    def __init__(self, base_path="platform/skills"):
        self.base_path = base_path
        self.shared_path = os.path.join(self.base_path, "_shared")

    def load_bundle(self, bundle_name: str, skill_config: dict = None) -> dict:
        """
        Carrega um skill bundle e injeta a regra transversal.
        O ponto de entrada canônico é SKILL.md — não há delegação para arquivos de agente separados.
        Retorna um dicionário contendo o prompt montado, schema, e metadados.
        """
        bundle_dir = os.path.join(self.base_path, bundle_name)

        # Ponto de entrada canônico: SKILL.md
        entrypoint_path = os.path.join(bundle_dir, "SKILL.md")
        if not os.path.exists(entrypoint_path):
            raise FileNotFoundError(f"Entrypoint SKILL.md não encontrado em {bundle_dir}")

        with open(entrypoint_path, "r", encoding="utf-8") as f:
            entrypoint_content = f.read()

        frontmatter = {}
        body = ""

        # Parse frontmatter e corpo do SKILL.md
        if entrypoint_content.startswith("---"):
            parts = entrypoint_content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_str = parts[1]
                try:
                    frontmatter = yaml.safe_load(frontmatter_str) or {}
                except yaml.YAMLError:
                    frontmatter = {}
                body = parts[2].strip()
        else:
            body = entrypoint_content.strip()

        # 1. Carregar Regra Transversal (extraction-base.md)
        extraction_base_path = os.path.join(self.shared_path, "extraction-base.md")
        extraction_base_content = ""
        if os.path.exists(extraction_base_path):
            with open(extraction_base_path, "r", encoding="utf-8") as bf:
                extraction_base_content = bf.read().strip()

        # 2. Carregar Schema JSON se existir localmente
        schema_content = None
        schema_path = os.path.join(bundle_dir, "schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as sf:
                try:
                    schema_content = json.load(sf)
                except json.JSONDecodeError:
                    schema_content = {"error": "Invalid JSON schema"}

        # 3. Montar o Payload Agregado
        full_system_prompt = f"{extraction_base_content}\n\n===\n\n{body}"

        # Mantendo compatibilidade de retorno posicional pros imports antigos
        self._last_loaded = {
            "bundle_name": bundle_name,
            "frontmatter": frontmatter,
            "system_prompt": full_system_prompt,
            "schema": schema_content
        }

        return full_system_prompt, frontmatter

    def load_bundle_payload(self, bundle_name: str, skill_config: dict = None) -> dict:
        """ Nova API que retorna o dict consolidado estruturado """
        self.load_bundle(bundle_name, skill_config)
        return self._last_loaded

if __name__ == "__main__":
    loader = BundleLoader()
    # Mock fallback, since we can't guarantee a valid bundle when running directly.
    pass
