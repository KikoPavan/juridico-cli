import os
import sys
import yaml


def _load_module_from_path(module_name, file_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class SkillDispatcher:
    """
    Despachador canônico de skills. Resolve skill, perfil de LLM e carrega
    bundle via bundle_loader. Ponto único de entrada do runtime.
    """

    def __init__(self, platform_path="platform"):
        self.platform_path = platform_path
        runtime_path = os.path.join(platform_path, "skill-runtime")
        skills_path = os.path.join(platform_path, "skills")

        loader_mod = _load_module_from_path(
            "bundle_loader",
            os.path.join(runtime_path, "bundle_loader.py"),
        )
        self.loader = loader_mod.BundleLoader(base_path=skills_path)
        self.skill_reg = self._load_yaml(os.path.join(runtime_path, "skill_registry.yaml"))
        self.llm_reg = self._load_yaml(os.path.join(runtime_path, "llm_registry.yaml"))

    def _load_yaml(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def dispatch(self, bundle_id):
        """
        Resolve a skill pelo ID, carrega o bundle e retorna payload pronto para execução.

        Retorna dict com:
            system_prompt  — instrução completa para o LLM
            skill_config   — entrada do skill_registry (path, profile, schema_ref)
            llm_profile    — entrada do llm_registry para o perfil da skill
            bundle_id      — ID da skill despachada
        """
        skill_config = self.skill_reg["skills"].get(bundle_id)
        if not skill_config:
            raise ValueError(f"Skill não registrada: {bundle_id}")

        profile_name = skill_config.get("profile", "fast_extraction")
        llm_profile = self.llm_reg["profiles"].get(profile_name, {})

        system_prompt, frontmatter = self.loader.load_bundle(bundle_id)

        return {
            "system_prompt": system_prompt,
            "skill_config": skill_config,
            "llm_profile": llm_profile,
            "bundle_id": bundle_id,
        }
