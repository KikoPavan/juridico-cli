import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_jus_autoridade_structure_validator_success():
    """
    Verifies that the local validate_structure.py script executes successfully
    and correctly validates the directory/file layout of the jus-autoridade skill.
    """
    script_path = PROJECT_ROOT / "platform" / "skills" / "jus-autoridade" / "scripts" / "validate_structure.py"
    skill_root = PROJECT_ROOT / "platform" / "skills" / "jus-autoridade"

    result = subprocess.run(
        [sys.executable, str(script_path), str(skill_root)],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "OK: Estrutura da skill Jus-Autoridade validada com sucesso" in result.stdout


def test_skill_dispatcher_resolves_jus_autoridade():
    """
    Verifies that the SkillDispatcher can load the jus-autoridade skill configuration,
    loads the expected system prompt, and correctly returns its metadata.
    """
    # Append runtime path to sys.path to allow imports
    runtime_path = PROJECT_ROOT / "platform" / "skill-runtime"
    if str(runtime_path) not in sys.path:
        sys.path.append(str(runtime_path))

    from skill_dispatcher import SkillDispatcher

    dispatcher = SkillDispatcher(platform_path=str(PROJECT_ROOT / "platform"))
    res = dispatcher.dispatch("jus-autoridade")

    assert res is not None
    assert res["bundle_id"] == "jus-autoridade"
    assert res["skill_config"]["profile"] == "high_reasoning"
    assert "platform/skills/jus-autoridade" in res["skill_config"]["path"]
    assert "authority_output_schema.json" in res["skill_config"]["schema_ref"]
    assert "validate_structure.py" in res["skill_config"]["validator"]

    # Verify key segments in the loaded system prompt
    assert res["system_prompt"] is not None
    assert len(res["system_prompt"]) > 0
    assert "CREAC" in res["system_prompt"]
    assert "ratio decidendi" in res["system_prompt"]
    assert "distinguishing" in res["system_prompt"].lower()
