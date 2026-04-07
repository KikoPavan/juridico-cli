#!/usr/bin/env python3
"""
firac_analyzer.py — Jus-Breve
Gerador e validador de análise jurídica pelo método FIRAC.

Uso:
    python scripts/firac_analyzer.py validate --file <resultado.json>
    python scripts/firac_analyzer.py render-markdown --file <resultado.json> [--output <saida.md>]
    python scripts/firac_analyzer.py template
    python scripts/firac_analyzer.py check-barrier --file <resultado.json>
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos padrão
# ---------------------------------------------------------------------------
SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_ROOT / "assets" / "firac_schema.json"


# ---------------------------------------------------------------------------
# Barreira de Contenção Fática
# ---------------------------------------------------------------------------

def check_fact_barrier(data: dict) -> tuple[bool, list[str]]:
    """
    Verifica a Barreira de Contenção Fática do FIRAC.
    Retorna (passa: bool, avisos: list[str]).
    """
    warnings = []
    firac = data.get("firac", {})
    facts = firac.get("facts", [])

    # Verifica se há fatos comprovados
    comprovados = [f for f in facts if f.get("status_probatorio") == "COMPROVADO"]
    especulativos = [f for f in facts if f.get("status_probatorio") == "ESPECULATIVO"]

    if not comprovados:
        warnings.append(
            "BLOQUEIO: Nenhum fato COMPROVADO identificado. "
            "Análise não pode prosseguir para formulação de Issues."
        )
        return False, warnings

    # Verifica se Issues referenciam apenas fatos não-especulativos
    ids_especulativos = {f["id"] for f in especulativos}
    issues = firac.get("issue", [])
    for issue in issues:
        refs = set(issue.get("facts_ref", []))
        contaminadas = refs & ids_especulativos
        if contaminadas:
            warnings.append(
                f"VIOLAÇÃO BARREIRA: Issue '{issue['id']}' referencia fatos ESPECULATIVOS: "
                f"{contaminadas}. Issues devem basear-se apenas em fatos COMPROVADOS ou "
                f"INFERIDOS_NECESSARIOS."
            )

    if warnings:
        return False, warnings

    return True, [
        f"Barreira fática OK: {len(comprovados)} fato(s) COMPROVADO(s), "
        f"{len(especulativos)} especulativo(s) isolado(s)."
    ]


# ---------------------------------------------------------------------------
# Validação de Schema
# ---------------------------------------------------------------------------

def validate_output(data: dict) -> tuple[bool, list[str]]:
    """
    Valida um output FIRAC. Usa jsonschema se disponível, fallback manual.
    """
    errors = []

    try:
        import jsonschema
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.load(f)
        validator = jsonschema.Draft7Validator(schema)
        schema_errors = list(validator.iter_errors(data))
        if schema_errors:
            for err in schema_errors:
                errors.append(f"[Schema] {err.json_path}: {err.message}")
            return False, errors
    except ImportError:
        # Validação manual básica
        required_top = ["skill", "versao", "status_analise", "metadados",
                        "firac", "avaliacao_risco", "qualidade"]
        for field in required_top:
            if field not in data:
                errors.append(f"Campo obrigatório ausente: '{field}'")

        if data.get("skill") != "jus-breve":
            errors.append("Campo 'skill' deve ser 'jus-breve'")

        status = data.get("status_analise")
        if status == "BLOQUEADO" and not data.get("motivo_bloqueio"):
            errors.append("status_analise BLOQUEADO exige campo 'motivo_bloqueio'")

        firac = data.get("firac", {})
        facts = firac.get("facts", [])
        if not facts:
            errors.append("'firac.facts' deve ter ao menos 1 item")

        # Padrões de ID
        patterns = {
            "facts": "F", "issue": "I", "rule": "R",
            "application": "A", "conclusion": "C"
        }
        for section, prefix in patterns.items():
            for item in firac.get(section, []):
                item_id = item.get("id", "")
                if not re.match(rf"^{prefix}-\d{{2}}$", item_id):
                    errors.append(
                        f"ID inválido em '{section}': '{item_id}' "
                        f"(esperado: '{prefix}-NN')"
                    )

        # Validação de respostas
        valid_respostas = {"SIM", "NAO", "CONDICIONAL", "INCONCLUSIVO"}
        for c in firac.get("conclusion", []):
            if c.get("resposta") not in valid_respostas:
                errors.append(
                    f"Conclusão '{c.get('id')}': resposta inválida '{c.get('resposta')}'"
                )
            if c.get("resposta") == "CONDICIONAL" and not c.get("condicao"):
                errors.append(
                    f"Conclusão '{c.get('id')}': CONDICIONAL exige campo 'condicao'"
                )

        # Validação de risco
        valid_risco = {"CRITICO", "RELEVANTE", "MODERADO", "BAIXO", "NULO"}
        for c in firac.get("conclusion", []):
            if c.get("nivel_risco") not in valid_risco:
                errors.append(
                    f"Conclusão '{c.get('id')}': nivel_risco inválido '{c.get('nivel_risco')}'"
                )

    if not errors:
        # Executa verificação da barreira fática
        barrier_ok, barrier_msgs = check_fact_barrier(data)
        if not barrier_ok:
            errors.extend(barrier_msgs)

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Geração de Markdown
# ---------------------------------------------------------------------------

RISCO_ICON = {
    "CRITICO": "🔴", "RELEVANTE": "🟠", "MODERADO": "🟡", "BAIXO": "🟢", "NULO": "⚪"
}
STATUS_ICON = {
    "PRESENTE": "✅", "AUSENTE": "❌", "PARCIAL": "⚠️",
    "CONTROVERSO": "🔶", "DEPENDENTE_PROVA": "🔍"
}


def render_markdown(data: dict) -> str:
    meta = data.get("metadados", {})
    firac = data.get("firac", {})
    avaliacao = data.get("avaliacao_risco", {})
    qualidade = data.get("qualidade", {})
    partes = meta.get("partes") or {}
    hoje = date.today().isoformat()

    lines = [
        "---",
        "",
        "## 📋 Sumário Executivo — Jus-Breve",
        "",
        f"**Tipo de Peça:** {meta.get('tipo_peca', 'N/I')}  ",
        f"**Ramo do Direito:** {meta.get('ramo_direito', 'N/I')}  ",
        f"**Objetivo:** {meta.get('objetivo_analise', 'N/I')}  ",
        f"**Partes:** {partes.get('polo_ativo', 'N/I')} × {partes.get('polo_passivo', 'N/I')}  ",
        f"**Nº Processo:** {meta.get('numero_processo') or 'N/I'}  ",
        f"**Data da Análise:** {hoje}  ",
        "",
        "---",
        "",
        "### 📁 F — Inventário Fático",
        "",
        "| ID | Fato | Tipo | Fonte | Status |",
        "|----|------|------|-------|--------|",
    ]

    for f in firac.get("facts", []):
        status = f.get("status_probatorio", "")
        status_badge = {
            "COMPROVADO": "✅ COMPROVADO",
            "CONTROVERTIDO": "⚠️ CONTROVERTIDO",
            "ESPECULATIVO": "❌ ESPECULATIVO"
        }.get(status, status)
        desc = f.get("descricao", "").replace("|", "\\|")
        lines.append(
            f"| {f['id']} | {desc} | {f.get('tipo','')} | "
            f"{f.get('fonte','')} | {status_badge} |"
        )

    lines += [
        "",
        "> ⚠️ Fatos **ESPECULATIVOS** não fundamentam questões jurídicas nesta análise.",
        "",
        "---",
        "",
        "### ⚖️ I — Questão(ões) Jurídica(s)",
        "",
    ]

    for issue in firac.get("issue", []):
        refs = ", ".join(issue.get("facts_ref", []))
        prejudicial_tag = " | 🔴 `PREJUDICIAL`" if issue.get("prejudicial") else ""
        lines.append(f"> **[{issue['id']}]** {issue['questao']}{prejudicial_tag}")
        lines.append(f"> *Baseado em: {refs}*")
        lines.append("")

    lines += ["---", "", "### 📖 R — Normas Aplicáveis", ""]

    for rule in firac.get("rule", []):
        refs = ", ".join(rule.get("issue_ref", []))
        tipo_badge = f"`{rule.get('tipo_norma','')}`"
        lines.append(
            f"- **{rule['diploma']}, {rule['artigo']}** "
            f"*({rule['hierarquia']} | {tipo_badge})* → Issues: {refs}"
        )
        lines.append(f"  > {rule['enunciado']}")
        lines.append("")

    lines += ["---", "", "### 🔗 A — Subsunção Contextualizada", ""]

    for app in firac.get("application", []):
        s_icon = STATUS_ICON.get(app.get("status", ""), "")
        lines += [
            f"**[{app['id']}] Fato `{app['fact_ref']}` × Norma `{app['rule_ref']}`**",
            f"- **Elemento verificado:** {app.get('elemento_norma','')}",
            f"- **Status:** {s_icon} {app.get('status','')}",
            f"- **Contexto:** {app.get('contexto','')}",
        ]
        if app.get("contrafactual"):
            lines.append(f"- **Contrafactual:** {app['contrafactual']}")
        if app.get("precedente_ref"):
            lines.append(f"- **Precedente:** {app['precedente_ref']}")
        lines.append("")

    lines += ["---", "", "### ✅ C — Conclusão", ""]

    for conc in firac.get("conclusion", []):
        resp_icon = {
            "SIM": "✅", "NAO": "❌", "CONDICIONAL": "⚠️", "INCONCLUSIVO": "❓"
        }.get(conc.get("resposta", ""), "")
        risco = conc.get("nivel_risco", "")
        r_icon = RISCO_ICON.get(risco, "")
        lines += [
            f"**[{conc['issue_ref']}] {resp_icon} {conc.get('resposta','')}** "
            f"— Risco: {r_icon} {risco}",
            f"> {conc.get('fundamento','')}",
        ]
        if conc.get("tese_juridica"):
            lines.append(f"> 📌 *Tese: {conc['tese_juridica']}*")
        if conc.get("dispositivo"):
            lines.append(f"> ⚖️ *Dispositivo: {conc['dispositivo']}*")
        if conc.get("condicao"):
            lines.append(f"> ⚠️ *Condição: {conc['condicao']}*")
        lines.append("")

    nivel_geral = avaliacao.get("nivel_geral", "N/I")
    r_icon_geral = RISCO_ICON.get(nivel_geral, "")
    lines += [
        "---",
        "",
        "### 🚦 Avaliação de Risco Consolidada",
        "",
        f"**Risco Geral: {r_icon_geral} {nivel_geral}**",
        "",
        "| Risco | Nível |",
        "|-------|-------|",
    ]

    for risco in avaliacao.get("riscos", []):
        n = risco.get("nivel", "")
        ri = RISCO_ICON.get(n, "")
        desc = risco.get("descricao", "").replace("|", "\\|")
        lines.append(f"| {desc} | {ri} {n} |")

    lines += ["", "---", "", "### 📊 Qualidade da Análise", ""]
    confianca_icon = {"ALTA": "🟢", "MEDIA": "🟡", "BAIXA": "🔴"}.get(
        qualidade.get("confianca", ""), ""
    )
    cobertura_icon = {
        "COMPLETA": "✅", "PARCIAL": "⚠️", "INSUFICIENTE": "❌"
    }.get(qualidade.get("cobertura_fatica", ""), "")

    lines += [
        f"**Confiança:** {confianca_icon} {qualidade.get('confianca', 'N/I')}  ",
        f"**Cobertura Fática:** {cobertura_icon} {qualidade.get('cobertura_fatica', 'N/I')}  ",
        "",
    ]

    limitacoes = qualidade.get("limitacoes", [])
    if limitacoes:
        lines.append("**Limitações:**")
        for lim in limitacoes:
            lines.append(f"- {lim}")
        lines.append("")

    if qualidade.get("recomendacao"):
        lines.append(f"> 💡 **Próximos Passos:** {qualidade['recomendacao']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Template em Branco
# ---------------------------------------------------------------------------

def blank_firac_template() -> dict:
    return {
        "skill": "jus-breve",
        "versao": "1.0.0",
        "status_analise": "COMPLETO",
        "motivo_bloqueio": None,
        "metadados": {
            "tipo_peca": "OUTROS",
            "ramo_direito": "CIVIL",
            "objetivo_analise": "RELATORIO",
            "partes": {"polo_ativo": None, "polo_passivo": None},
            "tribunal_juizo": None,
            "data_peca": None,
            "periodo_fatos": {"inicio": None, "fim": None},
            "numero_processo": None
        },
        "firac": {
            "facts": [
                {
                    "id": "F-01",
                    "descricao": "",
                    "tipo": "CONTRATUAL",
                    "fonte": "CITACAO_DIRETA",
                    "status_probatorio": "COMPROVADO",
                    "pagina_ref": None
                }
            ],
            "issue": [
                {
                    "id": "I-01",
                    "questao": "",
                    "prejudicial": True,
                    "facts_ref": ["F-01"]
                }
            ],
            "rule": [
                {
                    "id": "R-01",
                    "diploma": "",
                    "artigo": "",
                    "enunciado": "",
                    "hierarquia": "LEI_FEDERAL",
                    "tipo_norma": "NORMA_DIRETA",
                    "issue_ref": ["I-01"]
                }
            ],
            "application": [
                {
                    "id": "A-01",
                    "fact_ref": "F-01",
                    "rule_ref": "R-01",
                    "elemento_norma": "",
                    "status": "PRESENTE",
                    "contexto": "",
                    "contrafactual": None,
                    "precedente_ref": None
                }
            ],
            "conclusion": [
                {
                    "id": "C-01",
                    "issue_ref": "I-01",
                    "resposta": "INCONCLUSIVO",
                    "fundamento": "",
                    "tese_juridica": None,
                    "dispositivo": None,
                    "nivel_risco": "MODERADO",
                    "condicao": None
                }
            ]
        },
        "avaliacao_risco": {
            "nivel_geral": "MODERADO",
            "riscos": []
        },
        "qualidade": {
            "confianca": "BAIXA",
            "cobertura_fatica": "PARCIAL",
            "limitacoes": [],
            "recomendacao": None
        }
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Jus-Breve — Gerador e validador de análise FIRAC"
    )
    subparsers = parser.add_subparsers(dest="command")

    # validate
    val_p = subparsers.add_parser("validate", help="Valida JSON FIRAC")
    val_p.add_argument("--file", required=True)

    # render-markdown
    rnd_p = subparsers.add_parser("render-markdown", help="Gera Markdown a partir de JSON")
    rnd_p.add_argument("--file", required=True)
    rnd_p.add_argument("--output")

    # check-barrier
    bar_p = subparsers.add_parser(
        "check-barrier", help="Verifica apenas a Barreira de Contenção Fática"
    )
    bar_p.add_argument("--file", required=True)

    # template
    subparsers.add_parser("template", help="Imprime template em branco")

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
            print("✅ Output FIRAC válido.")
        else:
            print("❌ Erros de validação:")
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

    elif args.command == "check-barrier":
        path = Path(args.file)
        if not path.exists():
            print(f"❌ Arquivo não encontrado: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        ok, msgs = check_fact_barrier(data)
        for msg in msgs:
            print(f"{'✅' if ok else '❌'} {msg}")
        if not ok:
            sys.exit(1)

    elif args.command == "template":
        print(json.dumps(blank_firac_template(), ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
