"""
validate_structure.py
Verifica se a estrutura obrigatória da skill Jus-Autoridade está correta.
"""

import os
import sys


SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_STRUCTURE = {
    "dirs": [
        "",
        "assets",
        "references",
        "scripts",
    ],
    "files": [
        "SKILL.md",
        os.path.join("assets", "creac_template.md"),
        os.path.join("assets", "precedent_analysis_schema.json"),
        os.path.join("assets", "authority_output_schema.json"),
        os.path.join("references", "metodologia_creac.md"),
        os.path.join("references", "metodologia_precedentes.md"),
        os.path.join("references", "dicionario_variaveis.md"),
        os.path.join("references", "checklist_auditoria_precedentes.md"),
        os.path.join("scripts", "validate_structure.py"),
    ],
}


def validate(root: str) -> bool:
    errors = []

    for d in REQUIRED_STRUCTURE["dirs"]:
        path = os.path.join(root, d) if d else root
        if not os.path.isdir(path):
            errors.append(f"[DIRETÓRIO AUSENTE] {path}")

    for f in REQUIRED_STRUCTURE["files"]:
        path = os.path.join(root, f)
        if not os.path.isfile(path):
            errors.append(f"[ARQUIVO AUSENTE]   {path}")

    if errors:
        print("ERRO: Estrutura da skill Jus-Autoridade INCOMPLETA:\n")
        for e in errors:
            print(f"  {e}")
        return False

    print("OK: Estrutura da skill Jus-Autoridade validada com sucesso.")
    print(f"   Raiz: {root}")
    print(f"   Diretorios verificados: {len(REQUIRED_STRUCTURE['dirs'])}")
    print(f"   Arquivos verificados: {len(REQUIRED_STRUCTURE['files'])}")
    return True


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else SKILL_ROOT
    ok = validate(root)
    sys.exit(0 if ok else 1)
