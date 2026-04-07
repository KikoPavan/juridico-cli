#!/usr/bin/env python3
"""
irac_analyzer.py — Jus-Diagnose
Gerador e validador de análise jurídica pelo método IRAC.

Uso:
    python scripts/irac_analyzer.py --input <arquivo.txt> [--output <resultado.json>]
    python scripts/irac_analyzer.py --validate [--file <resultado.json>]
    python scripts/irac_analyzer.py --render-markdown <resultado.json>
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Caminhos padrão
# ---------------------------------------------------------------------------
SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_ROOT / "assets" / "irac_schema.json"
REFS_PATH = SKILL_ROOT / "references" / "variables.md"


# ---------------------------------------------------------------------------
# Validação de Schema
# ---------------------------------------------------------------------------

def load_schema() -> dict:
    """Carrega o JSON Schema para validação."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema não encontrado: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_output(data: dict) -> tuple[bool, list[str]]:
    """
    Valida um output IRAC contra o schema.
    Retorna (válido: bool, erros: list[str]).
    Usa jsonschema se disponível; caso contrário, faz validação básica.
    """
    errors = []

    # Tenta validar com jsonschema
    try:
        import jsonschema
        schema = load_schema()
        validator = jsonschema.Draft7Validator(schema)
        schema_errors = list(validator.iter_errors(data))
        if schema_errors:
            for err in schema_errors:
                errors.append(f"[Schema] {err.json_path}: {err.message}")
            return False, errors
        return True, []
    except ImportError:
        pass  # Fallback para validação manual

    # Validação manual básica
    required_top = ["skill", "versao", "metadados", "irac", "qualidade"]
    for field in required_top:
        if field not in data:
            errors.append(f"Campo obrigatório ausente: '{field}'")

    if data.get("skill") != "jus-diagnose":
        errors.append("Campo 'skill' deve ser 'jus-diagnose'")

    irac = data.get("irac", {})
    for section in ["issue", "rule", "application", "conclusion"]:
        items = irac.get(section, [])
        if not isinstance(items, list) or len(items) == 0:
            errors.append(f"'irac.{section}' deve ser lista não vazia")

    # Valida padrões de ID
    id_patterns = {"issue": "I", "rule": "R", "application": "A", "conclusion": "C"}
    for section, prefix in id_patterns.items():
        for item in irac.get(section, []):
            item_id = item.get("id", "")
            if not re.match(rf"^{prefix}-\d{{2}}$", item_id):
                errors.append(
                    f"ID inválido em '{section}': '{item_id}' "
                    f"(esperado: '{prefix}-NN')"
                )

    # Valida enum de resposta nas conclusões
    valid_respostas = {"SIM", "NAO", "CONDICIONAL", "INCONCLUSIVO"}
    for c in irac.get("conclusion", []):
        if c.get("resposta") not in valid_respostas:
            errors.append(
                f"Conclusão '{c.get('id')}': resposta inválida '{c.get('resposta')}'"
            )
        if c.get("resposta") == "CONDICIONAL" and not c.get("condicao"):
            errors.append(
                f"Conclusão '{c.get('id')}': CONDICIONAL exige campo 'condicao'"
            )

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Geração de Markdown
# ---------------------------------------------------------------------------

def render_markdown(data: dict) -> str:
    """Gera o sumário executivo em Markdown a partir do objeto IRAC."""
    meta = data.get("metadados", {})
    irac = data.get("irac", {})
    qualidade = data.get("qualidade", {})
    hoje = date.today().isoformat()

    partes = meta.get("partes") or {}
    polo_ativo = partes.get("polo_ativo", "N/I")
    polo_passivo = partes.get("polo_passivo", "N/I")

    lines = [
        "---",
        "",
        "## 📋 Sumário Executivo — Jus-Diagnose",
        "",
        f"**Tipo de Peça:** {meta.get('tipo_peca', 'N/I')}  ",
        f"**Ramo do Direito:** {meta.get('ramo_direito', 'N/I')}  ",
        f"**Partes:** {polo_ativo} × {polo_passivo}  ",
        f"**Data da Análise:** {hoje}  ",
        "",
        "---",
        "",
        "### ⚖️ Questão(ões) Jurídica(s)",
        "",
    ]

    for issue in irac.get("issue", []):
        prejudicial_tag = " 🔴 `PREJUDICIAL`" if issue.get("prejudicial") else ""
        lines.append(f"> **[{issue['id']}]** {issue['questao']}{prejudicial_tag}")
        lines.append("")

    lines += ["---", "", "### 📖 Normas Aplicáveis", ""]

    for rule in irac.get("rule", []):
        refs = ", ".join(rule.get("issue_ref", []))
        lines.append(
            f"- **{rule['diploma']}, {rule['artigo']}** "
            f"*({rule['hierarquia']})* → Issues: {refs}"
        )
        lines.append(f"  > {rule['enunciado']}")
        lines.append("")

    lines += ["---", "", "### 🔗 Subsunção", ""]
    lines += [
        "| ID | Fato | Elemento da Norma | Norma Ref. | Status |",
        "|----|------|-------------------|------------|--------|",
    ]
    for app in irac.get("application", []):
        status_icon = {
            "PRESENTE": "✅", "AUSENTE": "❌", "PARCIAL": "⚠️", "CONTROVERSO": "🔶"
        }.get(app.get("status", ""), "")
        fato = app.get("fato", "").replace("|", "\\|")
        elem = app.get("elemento_norma", "").replace("|", "\\|")
        lines.append(
            f"| {app['id']} | {fato} | {elem} | "
            f"{app['rule_ref']} | {status_icon} {app.get('status', '')} |"
        )
    lines.append("")

    lines += ["---", "", "### ✅ Conclusão", ""]

    for conc in irac.get("conclusion", []):
        resp_icon = {
            "SIM": "✅", "NAO": "❌", "CONDICIONAL": "⚠️", "INCONCLUSIVO": "❓"
        }.get(conc.get("resposta", ""), "")
        lines.append(
            f"**[{conc['issue_ref']}] Resposta: "
            f"{resp_icon} {conc.get('resposta', '')}**"
        )
        lines.append(f"> {conc.get('fundamento', '')}")
        if conc.get("condicao"):
            lines.append(f"> ⚠️ *Condição: {conc['condicao']}*")
        lines.append("")

    lines += ["---", "", "### 📊 Qualidade da Análise", ""]
    confianca_icon = {
        "ALTA": "🟢", "MEDIA": "🟡", "BAIXA": "🔴"
    }.get(qualidade.get("confianca", ""), "")
    lines.append(f"**Confiança:** {confianca_icon} {qualidade.get('confianca', 'N/I')}")
    lines.append("")

    limitacoes = qualidade.get("limitacoes", [])
    if limitacoes:
        lines.append("**Limitações identificadas:**")
        for lim in limitacoes:
            lines.append(f"- {lim}")
        lines.append("")

    if qualidade.get("recomendacao"):
        lines.append(f"> 💡 **Recomendação:** {qualidade['recomendacao']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Estrutura de Output em Branco (template)
# ---------------------------------------------------------------------------

def blank_irac_template() -> dict:
    """Retorna um template em branco para preenchimento pelo modelo."""
    return {
        "skill": "jus-diagnose",
        "versao": "1.0.0",
        "metadados": {
            "tipo_peca": "OUTROS",
            "ramo_direito": "CIVIL",
            "partes": {"polo_ativo": None, "polo_passivo": None},
            "tribunal_juizo": None,
            "data_peca": None,
            "issues_multiplas": False
        },
        "irac": {
            "issue": [
                {"id": "I-01", "questao": "", "prejudicial": True}
            ],
            "rule": [
                {
                    "id": "R-01",
                    "diploma": "",
                    "artigo": "",
                    "enunciado": "",
                    "hierarquia": "LEI_FEDERAL",
                    "issue_ref": ["I-01"]
                }
            ],
            "application": [
                {
                    "id": "A-01",
                    "fato": "",
                    "elemento_norma": "",
                    "rule_ref": "R-01",
                    "status": "PRESENTE"
                }
            ],
            "conclusion": [
                {
                    "id": "C-01",
                    "issue_ref": "I-01",
                    "resposta": "INCONCLUSIVO",
                    "fundamento": "",
                    "condicao": None
                }
            ]
        },
        "qualidade": {
            "confianca": "BAIXA",
            "limitacoes": [],
            "recomendacao": None
        }
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Jus-Diagnose — Gerador e validador de análise IRAC"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Subcomando: validate
    val_parser = subparsers.add_parser("validate", help="Valida um JSON de output IRAC")
    val_parser.add_argument("--file", required=True, help="Caminho para o JSON a validar")

    # Subcomando: render
    rnd_parser = subparsers.add_parser(
        "render-markdown", help="Renderiza sumário Markdown a partir de JSON IRAC"
    )
    rnd_parser.add_argument("--file", required=True, help="Caminho para o JSON IRAC")
    rnd_parser.add_argument("--output", help="Arquivo de saída .md (opcional)")

    # Subcomando: template
    subparsers.add_parser("template", help="Imprime template em branco para preenchimento")

    args = parser.parse_args()

    if args.command == "validate":
        path = Path(args.file)
        if not path.exists():
            print(f"❌ Arquivo não encontrado: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        valid, errors = validate_output(data)
        if valid:
            print("✅ Output IRAC válido.")
        else:
            print("❌ Erros de validação encontrados:")
            for err in errors:
                print(f"  • {err}")
            sys.exit(1)

    elif args.command == "render-markdown":
        path = Path(args.file)
        if not path.exists():
            print(f"❌ Arquivo não encontrado: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        md = render_markdown(data)
        if args.output:
            Path(args.output).write_text(md, encoding="utf-8")
            print(f"✅ Markdown gerado em: {args.output}")
        else:
            print(md)

    elif args.command == "template":
        print(json.dumps(blank_irac_template(), ensure_ascii=False, indent=2))

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
