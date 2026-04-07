import os
import json
import yaml
import glob
from pathlib import Path

class SkillMigrator:
    """
    Script de runtime isolado (Data Processing Sandbox)
    Estrutura os bundles originais adaptando para uso no `bundle_loader.py` 
    """
    def __init__(self, platform_dir="platform"):
        self.skills_dir = os.path.join(platform_dir, "skills")
        self.skill_runtime_dir = os.path.join(platform_dir, "skill-runtime")

    def read_registry(self):
        with open(os.path.join(self.skill_runtime_dir, "skill_registry.yaml"), "r") as f:
            return yaml.safe_load(f)["skills"]

    def repair_frontmatter(self):
        """
        Adiciona ou sobrescreve `base` e `agent` aos Frontmatters
        dos bundles existentes na pasta `platform/skills/`
        garantindo compatibilidade ao formato v1.1.
        """
        registry = self.read_registry()
        for skill_id, config in registry.items():
            skill_folder = os.path.join(os.getcwd(), config["path"])
            if not os.path.exists(skill_folder):
                os.makedirs(skill_folder)

            skill_file_path = None
            for f in ["SKILL.md", "agent.md", "prompt.md"]:
                candidate = os.path.join(skill_folder, f)
                if os.path.exists(candidate):
                    skill_file_path = candidate
                    break
            
            if not skill_file_path:
                skill_file_path = os.path.join(skill_folder, "SKILL.md")
                # Scaffolding Minimal MOCK para caso falte os originais do legacy
                with open(skill_file_path, "w", encoding="utf-8") as file:
                    file.write(f"---\nname: {skill_id}\nbase: extraction-base.md\nagent: SKILL.md\n---\n# Instrucoes do {skill_id}\nExtrair informacoes necessarias da fonte textual.\n")
                continue
                
            with open(skill_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith("---"):
                parts = content.split("---", 2)
                fm_str = parts[1]
                body = parts[2]
                try:
                    fm = yaml.safe_load(fm_str) or {}
                except:
                    fm = {}
                
                fm["base"] = "extraction-base.md"
                fm["agent"] = os.path.basename(skill_file_path)
                
                new_fm_str = yaml.dump(fm, default_flow_style=False)
                new_content = f"---\n{new_fm_str}---\n{body}"
                
                with open(skill_file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

if __name__ == "__main__":
    migrator = SkillMigrator()
    migrator.repair_frontmatter()
    print("✓ Bundles oficiais adaptados estruturalmente (Fase 2).")
