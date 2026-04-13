#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

try:
    import jsonschema  # type: ignore
except Exception:
    jsonschema = None


@dataclass
class CheckResult:
    name: str
    status: str
    details: list[str] = field(default_factory=list)


@dataclass
class SkillAudit:
    skill_name: str
    skill_dir: Path
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, status: str, *details: str) -> None:
        self.checks.append(CheckResult(name=name, status=status, details=list(details)))

    @property
    def summary_status(self) -> str:
        if any(c.status == "FAIL" for c in self.checks):
            return "FAIL"
        if any(c.status == "WARN" for c in self.checks):
            return "WARN"
        return "PASS"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed in the current environment.")
    return yaml.safe_load(read_text(path))


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def path_status(path: Path) -> str:
    return "PASS" if path.exists() else "FAIL"


def find_first(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def list_existing(paths: list[Path]) -> list[Path]:
    return [p for p in paths if p.exists()]


def parse_frontmatter(md_text: str) -> dict[str, Any] | None:
    pattern = r"^---\s*\n(.*?)\n---\s*(?:\n|$)"
    match = re.search(pattern, md_text, flags=re.DOTALL)
    if not match:
        return None
    raw = match.group(1)
    if yaml is None:
        return {"_raw_frontmatter": raw}
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {"_frontmatter": data}


def flatten_dict_keys(data: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            full = f"{prefix}.{k}" if prefix else str(k)
            keys.append(full)
            keys.extend(flatten_dict_keys(v, full))
    elif isinstance(data, list):
        for i, item in enumerate(data[:3]):
            full = f"{prefix}[{i}]"
            keys.append(full)
            keys.extend(flatten_dict_keys(item, full))
    return keys


def registry_contains_skill(registry_data: Any, skill_name: str) -> tuple[bool, str]:
    if isinstance(registry_data, dict):
        # Common shapes
        for top_key in ("skills", "bundles", "entries", "registry"):
            block = registry_data.get(top_key)
            if isinstance(block, dict) and skill_name in block:
                return True, f"Found under '{top_key}.{skill_name}'."
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, dict):
                        if (
                            item.get("id") == skill_name
                            or item.get("name") == skill_name
                            or item.get("skill") == skill_name
                        ):
                            return True, f"Found under '{top_key}' list."
        # Generic recursive search
        stack = [registry_data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if (
                    node.get("id") == skill_name
                    or node.get("name") == skill_name
                    or node.get("skill") == skill_name
                ):
                    return True, "Found by recursive registry search."
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return False, "Skill not found in parsed registry."


def collect_required_docs(root: Path) -> list[tuple[str, Path]]:
    return [
        ("QWEN.md", root / "QWEN.md"),
        (
            "Arquitetura evolutiva",
            root / "docs/architecture/juridico_cli_arquitetura_evolutiva.md",
        ),
        (
            "Estado real consolidado",
            root / "docs/architecture/juridico_cli_estado_real_consolidado.md",
        ),
        (
            "Implementation state",
            root / "_bmad-output/implementation-artifacts/implementation-state.md",
        ),
        ("Project context", root / "_bmad-output/project-context.md"),
    ]


def validate_json_example(
    schema_path: Path, example_path: Path
) -> tuple[str, list[str]]:
    details: list[str] = []
    if jsonschema is None:
        return "WARN", [
            "jsonschema not installed; JSON example loaded but not schema-validated."
        ]
    try:
        schema = load_json(schema_path)
        example = load_json(example_path)
        jsonschema.validate(instance=example, schema=schema)
        details.append(
            f"Example '{example_path.name}' validates against '{schema_path.name}'."
        )
        return "PASS", details
    except Exception as exc:
        details.append(f"Validation failed: {exc}")
        return "FAIL", details


def audit_segmentador(root: Path) -> SkillAudit:
    skill_dir = root / "platform/skills/segmentador-juridico"
    audit = SkillAudit("segmentador-juridico", skill_dir)

    must_exist = [
        skill_dir / "SKILL.md",
        skill_dir / "assets/output-schema.json",
        skill_dir / "references",
    ]
    for p in must_exist:
        audit.add(f"Path exists: {p.relative_to(root)}", path_status(p))

    schema_path = skill_dir / "assets/output-schema.json"
    example_candidates = [
        skill_dir / "assets/example-output.json",
        skill_dir / "assets/example_output.json",
        skill_dir / "references/example_output.json",
        skill_dir / "references/exemplo_saida.json",
        skill_dir / "references/example_output.md",
    ]
    example_path = find_first(example_candidates)
    if example_path is None:
        audit.add("Example output", "WARN", "No known example output file found.")
    else:
        if example_path.suffix.lower() == ".json" and schema_path.exists():
            status, details = validate_json_example(schema_path, example_path)
            audit.add("Schema validation", status, *details)
        elif example_path.suffix.lower() == ".md":
            text = read_text(example_path)
            audit.add(
                "Markdown example found",
                "WARN",
                f"Found markdown example '{example_path.name}'. Auto schema validation skipped.",
                f"Size: {len(text)} chars.",
            )

    return audit


def audit_curador(root: Path) -> SkillAudit:
    skill_dir = root / "platform/skills/curador-relevancia"
    audit = SkillAudit("curador-relevancia", skill_dir)

    schema_candidates = [
        skill_dir / "assets/schema_saida.json",
        skill_dir / "assets/output-schema.json",
        skill_dir / "assets/output.schema.json",
    ]
    schema_path = find_first(schema_candidates)

    must_exist = [skill_dir / "SKILL.md", skill_dir / "references"]
    for p in must_exist:
        audit.add(f"Path exists: {p.relative_to(root)}", path_status(p))

    if schema_path is None:
        audit.add("Schema file", "FAIL", "No known output schema found under assets/.")
    else:
        audit.add(
            "Schema file", "PASS", f"Using schema: {schema_path.relative_to(root)}"
        )

    example_candidates = [
        skill_dir / "assets/exemplo_saida.json",
        skill_dir / "assets/exemplo_saida_padrao.json",
        skill_dir / "assets/exemplo_saida_sintetico.json",
        skill_dir / "references/example_output.json",
        skill_dir / "references/exemplo_saida.json",
        skill_dir / "references/example_output.md",
    ]
    example_path = find_first(example_candidates)
    if example_path is None:
        audit.add("Example output", "WARN", "No known example output file found.")
    else:
        if example_path.suffix.lower() == ".json" and schema_path is not None:
            status, details = validate_json_example(schema_path, example_path)
            audit.add("Schema validation", status, *details)
        elif example_path.suffix.lower() == ".md":
            text = read_text(example_path)
            audit.add(
                "Markdown example found",
                "WARN",
                f"Found markdown example '{example_path.name}'. Auto schema validation skipped.",
                f"Size: {len(text)} chars.",
            )

    return audit


def audit_normalizador(root: Path) -> SkillAudit:
    skill_dir = root / "platform/skills/yaml-normalizador-juridico"
    audit = SkillAudit("yaml-normalizador-juridico", skill_dir)

    schema_candidates = [
        skill_dir / "assets/io.schema.json",
        skill_dir / "assets/output-schema.json",
        skill_dir / "assets/output.schema.json",
    ]
    schema_path = find_first(schema_candidates)

    must_exist = [
        skill_dir / "SKILL.md",
        skill_dir / "references/example_output.md",
        skill_dir / "assets",
    ]
    for p in must_exist:
        audit.add(f"Path exists: {p.relative_to(root)}", path_status(p))

    if schema_path is None:
        audit.add("Schema file", "WARN", "No known schema file found under assets/.")
    else:
        audit.add(
            "Schema file", "PASS", f"Using schema: {schema_path.relative_to(root)}"
        )

    example_md = skill_dir / "references/example_output.md"
    if example_md.exists():
        text = read_text(example_md)
        frontmatter = parse_frontmatter(text)
        if frontmatter is None:
            audit.add(
                "Frontmatter parse",
                "FAIL",
                "example_output.md does not contain YAML frontmatter delimited by ---",
            )
        else:
            keys = flatten_dict_keys(frontmatter)
            legacy_hits = []
            raw_lower = text.lower()
            for token in (
                "legado",
                "legacy",
                "curation_action:",
                "impacto_sentenca:",
            ):
                if token in raw_lower:
                    legacy_hits.append(token)
            status = "WARN" if legacy_hits else "PASS"
            details = [
                f"Frontmatter keys detected: {', '.join(keys[:25]) if keys else '(none)'}",
            ]
            if legacy_hits:
                details.append(
                    "Review example_output.md for enum compatibility; detected tokens: "
                    + ", ".join(sorted(set(legacy_hits)))
                )
            audit.add("Frontmatter inspection", status, *details)

    routing_map = skill_dir / "assets/routing_map.yaml"
    if routing_map.exists():
        audit.add(
            "Routing map asset", "PASS", f"Found: {routing_map.relative_to(root)}"
        )
    else:
        audit.add("Routing map asset", "WARN", "assets/routing_map.yaml not found.")

    return audit


def build_report(
    root: Path,
    docs_results: list[CheckResult],
    registry_results: list[CheckResult],
    audits: list[SkillAudit],
) -> str:
    def bullets(results: list[CheckResult]) -> str:
        lines: list[str] = []
        for r in results:
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(r.status, "•")
            lines.append(f"- {icon} **{r.name}**")
            for d in r.details:
                lines.append(f"  - {d}")
        return "\n".join(lines)

    overall = "PASS"
    for audit in audits:
        if audit.summary_status == "FAIL":
            overall = "FAIL"
            break
        if audit.summary_status == "WARN":
            overall = "WARN"

    matured = []
    blocked = []
    for audit in audits:
        if audit.summary_status == "PASS":
            matured.append(audit.skill_name)
        else:
            blocked.append(audit.skill_name)

    sections: list[str] = []
    sections.append("# Relatório de Validação da Esteira Jurídica")
    sections.append("")
    sections.append("## Resumo executivo")
    sections.append(f"- Status geral: **{overall}**")
    sections.append(
        f"- Skills auditadas: **{', '.join(a.skill_name for a in audits)}**"
    )
    sections.append(
        f"- Maduras sem alerta nesta auditoria: **{', '.join(matured) if matured else 'nenhuma'}**"
    )
    sections.append(
        f"- Exigem ajuste ou revisão: **{', '.join(blocked) if blocked else 'nenhuma'}**"
    )
    sections.append("")
    sections.append("## Arquivos e documentos-base")
    sections.append(bullets(docs_results))
    sections.append("")
    sections.append("## Registry e runtime")
    sections.append(bullets(registry_results))
    sections.append("")

    for audit in audits:
        sections.append(f"## Skill — {audit.skill_name}")
        sections.append(f"- Diretório: `{audit.skill_dir.relative_to(root)}`")
        sections.append(f"- Status: **{audit.summary_status}**")
        sections.append(bullets(audit.checks))
        sections.append("")

    sections.append("## Diagnóstico objetivo")
    sections.append("- **Maduro**: somente o que passou sem alerta nesta auditoria.")
    sections.append("- **Parcialmente validado**: itens com `WARN`.")
    sections.append("- **Inconsistente**: itens com `FAIL`.")
    sections.append(
        "- **Bloqueio conhecido**: revisar `platform/skills/yaml-normalizador-juridico/references/example_output.md` antes de considerar a esteira pronta para integração."
    )
    sections.append("")
    sections.append("## Próximo passo recomendado")
    sections.append(
        "- Corrigir primeiro os pontos `FAIL` e `WARN` da skill `yaml-normalizador-juridico`."
    )
    sections.append(
        "- Reexecutar a auditoria e, depois, validar a cadeia ponta a ponta fora do pipeline executável."
    )
    sections.append("- Não alterar `apps/data-processing/` nesta fase.")
    sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the 3 juridical skills without touching the executable pipeline."
    )
    parser.add_argument(
        "--root", default=".", help="Repository root. Default: current directory."
    )
    parser.add_argument(
        "--report",
        default="docs/qwen_tasks/relatorio_validacao_esteira_juridica.md",
        help="Output report path relative to repo root.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] Repository root not found: {root}", file=sys.stderr)
        return 2

    docs_results: list[CheckResult] = []
    for name, path in collect_required_docs(root):
        status = "PASS" if path.exists() else "FAIL"
        details = (
            [f"Path: {path.relative_to(root)}"]
            if path.exists()
            else [f"Missing: {path.relative_to(root)}"]
        )
        docs_results.append(CheckResult(name=name, status=status, details=details))

    registry_results: list[CheckResult] = []
    skill_registry = root / "platform/skill-runtime/skill_registry.yaml"
    llm_registry = root / "platform/skill-runtime/llm_registry.yaml"

    if skill_registry.exists() and yaml is not None:
        try:
            reg = load_yaml(skill_registry)
            for skill_name in (
                "segmentador-juridico",
                "curador-relevancia",
                "yaml-normalizador-juridico",
            ):
                found, detail = registry_contains_skill(reg, skill_name)
                registry_results.append(
                    CheckResult(
                        name=f"Skill registry: {skill_name}",
                        status="PASS" if found else "FAIL",
                        details=[detail, f"Path: {skill_registry.relative_to(root)}"],
                    )
                )
        except Exception as exc:
            registry_results.append(
                CheckResult(
                    name="Skill registry parse",
                    status="FAIL",
                    details=[
                        f"Could not parse {skill_registry.relative_to(root)}: {exc}"
                    ],
                )
            )
    else:
        registry_results.append(
            CheckResult(
                name="Skill registry",
                status="FAIL",
                details=["skill_registry.yaml missing or PyYAML unavailable."],
            )
        )

    if llm_registry.exists():
        registry_results.append(
            CheckResult(
                name="LLM registry exists",
                status="PASS",
                details=[f"Path: {llm_registry.relative_to(root)}"],
            )
        )
    else:
        registry_results.append(
            CheckResult(
                name="LLM registry exists",
                status="FAIL",
                details=[f"Missing: {llm_registry.relative_to(root)}"],
            )
        )

    audits = [
        audit_segmentador(root),
        audit_curador(root),
        audit_normalizador(root),
    ]

    report_text = build_report(root, docs_results, registry_results, audits)

    report_path = (root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    print(f"[OK] Report written to: {report_path}")
    print("[INFO] Summary:")
    for audit in audits:
        print(f"  - {audit.skill_name}: {audit.summary_status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
