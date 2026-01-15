#!/usr/bin/env python3
"""
Levantamento do Estado do Projeto (juridico-cli) — varredura local (sem Antigravity)

Gera um relatório Markdown com:
- Contexto do repo (git)
- Árvore resumida
- Inventário granular por agente (OK/FALTA/N/A) + trechos de evidência
- I/O provável (por grep/snippets em configs/código)
- Inventário de schemas
- Inventário de prompts + checagem de regras críticas
- MCP server: localização + entrypoint + tools (heurístico) + consumo/ausência
- Outputs: amostras + checagem de source_id/âncoras
- Dependências (pyproject.toml) focadas em LangChain/LangGraph/LLMs
- Sumário CONFIRMADO / NÃO ENCONTRADO / INCONCLUSIVO

Uso:
  python tools/levantar_estado.py --repo . --out levantamento_auto.md
  python tools/levantar_estado.py --repo . --only agents --out 02_agents.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore


SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".tox",
    ".idea",
    ".vscode",
}

TEXT_EXT_ALLOWLIST = {
    ".py",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".psm1",
    ".bat",
    ".cmd",
    ".env",
    ".dockerfile",
    "",
}

PROMPT_HINTS = ("prompt", "prompts", "instructions", "instru", "system", "agent")
SCHEMA_HINTS = ("schema", "schemas", "io.schema.json", ".schema.json")

KEY_PATTERNS = {
    "io": [
        r"\binput\b",
        r"\binputs\b",
        r"\binput_dir\b",
        r"\bsource_dir\b",
        r"\boutput\b",
        r"\boutputs\b",
        r"\boutput_dir\b",
        r"\bout_dir\b",
        r"\bpaths?\b",
        r"\bstage\b",
        r"\b01_\b",
        r"\b02_\b",
        r"\b03_\b",
        r"\b04_\b",
        r"\bschema\b",
        r"\bio\.schema\.json\b",
    ],
    "mcp": [r"\bmcp\b", r"\bserver\b", r"\btools?\b", r"\bstdi[o]?\b", r"\bfastapi\b"],
    "llm": [
        r"\blangchain\b",
        r"\blanggraph\b",
        r"\bopenai\b",
        r"\bgoogle[-_]genai\b",
        r"\bgemini\b",
        r"\bclaude\b",
        r"\banthropic\b",
    ],
    "anchors": [
        r"\bsource_id\b",
        r"\bsha256\b",
        r"\bfls\b",
        r"\bfolha\b",
        r"\[\[Folha\b",
        r"\[Pág\.",
    ],
    "monetary": [
        r"\bCR\$\b",
        r"\bR\$\b",
        r"\b02_monetary\b",
        r"\b03_monetary\b",
        r"\bmonetary\b",
        r"\bnormalize\b",
    ],
}


@dataclass
class AgentInventory:
    name: str
    path: Path
    has_config: bool
    config_path: Optional[Path]
    has_io_schema: bool
    io_schema_path: Optional[Path]
    has_schemas_dir: bool
    schemas_dir: Optional[Path]
    schema_files: list[Path]
    prompt_files: list[Path]
    entrypoints: list[Path]
    has_tests: bool
    tests_paths: list[Path]
    docker_files: list[Path]


def is_probably_binary(p: Path) -> bool:
    try:
        data = p.read_bytes()[:2048]
    except Exception:
        return True
    if b"\x00" in data:
        return True
    # crude binary ratio
    nontext = sum(1 for b in data if b < 9 or (13 < b < 32) or b > 126)
    return nontext > max(20, int(len(data) * 0.2))


def read_text_safe(p: Path, max_bytes: int = 1_000_000) -> str:
    try:
        if p.stat().st_size > max_bytes:
            return ""
        raw = p.read_bytes()
        if b"\x00" in raw[:2048]:
            return ""
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def run(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True
        )
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return r.returncode, out.strip()
    except Exception as e:
        return 1, str(e)


def md_escape(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def snippet_with_context(
    text: str, pattern: str, context_lines: int = 3, max_blocks: int = 2
) -> str:
    if not text:
        return ""
    rx = re.compile(pattern, flags=re.IGNORECASE)
    lines = text.splitlines()
    hits = [i for i, ln in enumerate(lines) if rx.search(ln)]
    if not hits:
        return ""
    blocks = []
    for idx in hits[:max_blocks]:
        start = max(0, idx - context_lines)
        end = min(len(lines), idx + context_lines + 1)
        block = "\n".join(lines[start:end])
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


def collect_tree(root: Path, max_depth: int = 3) -> str:
    root = root.resolve()
    out_lines = []

    def walk(dir_path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(
                dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
            )
        except Exception:
            return
        for p in entries:
            if p.name in SKIP_DIRS:
                continue
            rel = p.relative_to(root)
            indent = "  " * depth
            if p.is_dir():
                out_lines.append(f"{indent}- {rel}/")
                walk(p, depth + 1)
            else:
                out_lines.append(f"{indent}- {rel}")

    out_lines.append(f"- {root.name}/")
    walk(root, 1)
    return "\n".join(out_lines)


def find_agents(root: Path) -> list[Path]:
    agents_dir = root / "agents"
    agent_paths = []
    if agents_dir.exists() and agents_dir.is_dir():
        for p in sorted(agents_dir.iterdir()):
            if p.is_dir() and p.name not in SKIP_DIRS:
                agent_paths.append(p)
    # also include top-level directories that look like agents (fallback)
    for p in sorted(root.iterdir()):
        if (
            p.is_dir()
            and p.name not in SKIP_DIRS
            and p.name.startswith(
                (
                    "collector",
                    "reconciler",
                    "monetary",
                    "mcp",
                    "firac",
                    "petition",
                    "compliance",
                )
            )
        ):
            if p not in agent_paths:
                agent_paths.append(p)
    return agent_paths


def list_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def discover_prompts(agent_dir: Path) -> list[Path]:
    prompts = []
    for p in agent_dir.rglob("*"):
        if p.is_dir():
            if p.name in SKIP_DIRS:
                continue
            continue
        if p.suffix.lower() in (".md", ".txt", ".yaml", ".yml") and any(
            h in str(p).lower() for h in PROMPT_HINTS
        ):
            prompts.append(p)
    # also: any .md under agent root
    for p in agent_dir.glob("*.md"):
        if p not in prompts:
            prompts.append(p)
    return sorted(set(prompts))


def discover_schemas(agent_dir: Path) -> Tuple[bool, Optional[Path], list[Path]]:
    schemas_dir = agent_dir / "schemas"
    schema_files = []
    if schemas_dir.exists() and schemas_dir.is_dir():
        for p in schemas_dir.rglob("*.json"):
            if (
                p.name.endswith(".schema.json")
                or p.name.endswith(".schema.jsonl")
                or "schema" in p.name
            ):
                schema_files.append(p)
        # also include any json with schema in filename
        for p in schemas_dir.rglob("*"):
            if (
                p.is_file()
                and "schema" in p.name.lower()
                and p.suffix.lower() == ".json"
            ):
                schema_files.append(p)
    # include io.schema.json if inside schemas/
    return (
        schemas_dir.exists() and schemas_dir.is_dir(),
        (schemas_dir if schemas_dir.exists() else None),
        sorted(set(schema_files)),
    )


def discover_entrypoints(agent_dir: Path) -> list[Path]:
    candidates = []
    for name in ("main.py", "__main__.py", "app.py", "cli.py"):
        p = agent_dir / name
        if p.exists():
            candidates.append(p)
    # any python file with "typer" or "argparse" as hint
    for p in agent_dir.rglob("*.py"):
        if p.name in ("main.py", "__main__.py"):
            continue
        txt = read_text_safe(p)
        if not txt:
            continue
        if "typer" in txt or "argparse" in txt or "click" in txt:
            candidates.append(p)
    return sorted(set(candidates))


def discover_tests(agent_dir: Path) -> Tuple[bool, list[Path]]:
    tests = []
    for p in (agent_dir / "tests", agent_dir / "test"):
        if p.exists() and p.is_dir():
            tests.append(p)
    # pytest files
    for p in agent_dir.rglob("test_*.py"):
        tests.append(p)
    return len(tests) > 0, sorted(set(tests))


def discover_docker(agent_dir: Path) -> list[Path]:
    out = []
    for name in (
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".dockerignore",
    ):
        p = agent_dir / name
        if p.exists():
            out.append(p)
    return sorted(set(out))


def inventory_agent(agent_dir: Path) -> AgentInventory:
    name = agent_dir.name
    config = None
    for p in (agent_dir / "config.yaml", agent_dir / "config.yml"):
        if p.exists():
            config = p
            break

    io_schema = agent_dir / "io.schema.json"
    has_io_schema = io_schema.exists()

    has_schemas_dir, schemas_dir, schema_files = discover_schemas(agent_dir)
    prompts = discover_prompts(agent_dir)
    entrypoints = discover_entrypoints(agent_dir)
    has_tests, tests_paths = discover_tests(agent_dir)
    docker_files = discover_docker(agent_dir)

    return AgentInventory(
        name=name,
        path=agent_dir,
        has_config=config is not None,
        config_path=config,
        has_io_schema=has_io_schema,
        io_schema_path=io_schema if has_io_schema else None,
        has_schemas_dir=has_schemas_dir,
        schemas_dir=schemas_dir,
        schema_files=schema_files,
        prompt_files=prompts,
        entrypoints=entrypoints,
        has_tests=has_tests,
        tests_paths=tests_paths,
        docker_files=docker_files,
    )


def find_repo_files_by_patterns(
    root: Path, patterns: list[str], max_hits: int = 50
) -> list[Tuple[Path, str]]:
    hits: list[Tuple[Path, str]] = []
    combined = re.compile("|".join(f"({p})" for p in patterns), flags=re.IGNORECASE)
    for p in list_files(root):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXT_ALLOWLIST:
            continue
        if is_probably_binary(p):
            continue
        txt = read_text_safe(p)
        if not txt:
            continue
        if combined.search(txt):
            hits.append((p, txt))
            if len(hits) >= max_hits:
                break
    return hits


def parse_pyproject_deps(root: Path) -> dict:
    out = {"project": [], "optional": {}, "tool": {}}
    pp = root / "pyproject.toml"
    if not pp.exists() or tomllib is None:
        return out
    try:
        data = tomllib.loads(pp.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return out
    proj = data.get("project", {})
    out["project"] = proj.get("dependencies", []) or []
    out["optional"] = proj.get("optional-dependencies", {}) or {}
    tool = data.get("tool", {}) or {}
    out["tool"] = tool
    return out


def select_output_samples(outputs_dir: Path, per_stage: int = 2) -> list[Path]:
    if not outputs_dir.exists():
        return []
    candidates = []
    for p in outputs_dir.rglob("*.json"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            sz = p.stat().st_size
        except Exception:
            continue
        candidates.append((sz, p))
    candidates.sort(key=lambda x: x[0])
    selected = [p for _, p in candidates[:30]]  # small set
    # prefer stage folders
    stage_selected = []
    stages = [
        "01_collector",
        "02_normalize",
        "03_monetary",
        "04_reconciler",
        "dataset_v1",
    ]
    for st in stages:
        st_files = [p for p in selected if st in str(p)]
        stage_selected.extend(st_files[:per_stage])
    # fallback add smallest
    for p in selected:
        if len(stage_selected) >= per_stage * 5:
            break
        if p not in stage_selected:
            stage_selected.append(p)
    return stage_selected


def json_evidence(p: Path, max_lines: int = 60) -> Tuple[str, dict]:
    txt = read_text_safe(p, max_bytes=2_000_000)
    evidence = {"has_source_id": False, "has_anchor": False, "anchor_hints": []}
    if not txt:
        return "", evidence
    # heuristics: keys and anchor text
    low = txt.lower()
    evidence["has_source_id"] = ("source_id" in low) or ("sha256" in low)
    anchor_hits = []
    for rx in KEY_PATTERNS["anchors"]:
        if re.search(rx, txt, flags=re.IGNORECASE):
            anchor_hits.append(rx)
    evidence["has_anchor"] = len(anchor_hits) > 0
    evidence["anchor_hints"] = anchor_hits[:5]
    lines = txt.splitlines()[:max_lines]
    return "\n".join(lines), evidence


def section_env(root: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"**Gerado em:** {now}", f"**Repo:** {root.resolve()}"]
    rc, out = run(["git", "rev-parse", "--show-toplevel"], cwd=root)
    if rc == 0:
        lines.append(f"**Git root:** {out}")
    rc, out = run(["git", "branch", "--show-current"], cwd=root)
    if rc == 0 and out:
        lines.append(f"**Branch:** {out}")
    rc, out = run(["git", "log", "-1", "--pretty=%H%n%ad%n%s"], cwd=root)
    if rc == 0 and out:
        h, d, s = (out.splitlines() + ["", "", ""])[:3]
        lines.append(f"**Último commit:** `{h}`")
        lines.append(f"**Data:** {d}")
        lines.append(f"**Mensagem:** {s}")
    rc, out = run(["git", "status", "--porcelain"], cwd=root)
    if rc == 0:
        lines.append(f"**Working tree sujo:** {'SIM' if out.strip() else 'NÃO'}")
        if out.strip():
            lines.append("\n**Mudanças (porcelain):**\n")
            lines.append("\n".join(f"- `{ln}`" for ln in out.splitlines()[:50]))
    return "\n".join(lines)


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    sep = ["---"] * len(header)
    body = rows[1:]
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for r in body:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def section_agents(root: Path, snip: int) -> Tuple[str, list[AgentInventory]]:
    agents = [inventory_agent(p) for p in find_agents(root)]
    rows = [
        [
            "Agente",
            "Path",
            "config",
            "io.schema",
            "schemas/",
            "prompts",
            "entrypoints",
            "tests",
            "docker",
        ]
    ]
    for a in agents:
        rows.append(
            [
                a.name,
                str(a.path.relative_to(root)),
                "OK" if a.has_config else "FALTA",
                "OK" if a.has_io_schema else "FALTA",
                "OK" if a.has_schemas_dir else "FALTA",
                f"{len(a.prompt_files)}",
                f"{len(a.entrypoints)}",
                "OK" if a.has_tests else "FALTA",
                f"{len(a.docker_files)}",
            ]
        )
    parts = [md_table(rows), ""]
    # evidence snippets for key files
    for a in agents:
        parts.append(f"### {a.name}")
        parts.append(f"- **Pasta:** `{a.path.relative_to(root)}`")
        if a.config_path:
            cfg_txt = read_text_safe(a.config_path)
            sn = snippet_with_context(
                cfg_txt,
                r"(input|output|schema|job|model|prompt)",
                context_lines=3,
                max_blocks=2,
            )
            parts.append(f"- **config:** `{a.config_path.relative_to(root)}`")
            if sn:
                parts.append(
                    "**Trecho (config):**\n\n```text\n"
                    + md_escape("\n".join(sn.splitlines()[:snip]))
                    + "\n```"
                )
        else:
            parts.append("- **config:** NÃO ENCONTRADO")
        if a.io_schema_path:
            ios_txt = read_text_safe(a.io_schema_path)
            head = "\n".join(ios_txt.splitlines()[:snip]) if ios_txt else ""
            parts.append(f"- **io.schema:** `{a.io_schema_path.relative_to(root)}`")
            if head:
                parts.append(
                    "**Trecho (io.schema):**\n\n```text\n" + md_escape(head) + "\n```"
                )
        else:
            parts.append("- **io.schema:** NÃO ENCONTRADO")
        if a.has_schemas_dir and a.schemas_dir:
            parts.append(
                f"- **schemas/:** `{a.schemas_dir.relative_to(root)}` ({len(a.schema_files)} arquivos encontrados)"
            )
            for sf in a.schema_files[:10]:
                parts.append(f"  - `{sf.relative_to(root)}`")
        else:
            parts.append("- **schemas/:** NÃO ENCONTRADO")
        if a.prompt_files:
            parts.append(f"- **prompts:** {len(a.prompt_files)} arquivo(s)")
            for pf in a.prompt_files[:10]:
                parts.append(f"  - `{pf.relative_to(root)}`")
        else:
            parts.append("- **prompts:** NÃO ENCONTRADO")
        if a.entrypoints:
            parts.append(f"- **entrypoints:**")
            for ep in a.entrypoints[:5]:
                txt = read_text_safe(ep)
                sn = snippet_with_context(
                    txt,
                    r"(main|run|cli|typer|argparse|LangGraph|langchain|schema|output|input)",
                    context_lines=3,
                    max_blocks=1,
                )
                parts.append(f"  - `{ep.relative_to(root)}`")
                if sn:
                    parts.append(
                        "    **Trecho (entrypoint):**\n\n```text\n"
                        + md_escape("\n".join(sn.splitlines()[:snip]))
                        + "\n```"
                    )
        else:
            parts.append("- **entrypoints:** NÃO ENCONTRADO")
        if a.has_tests:
            parts.append(f"- **tests:**")
            for tp in a.tests_paths[:5]:
                parts.append(f"  - `{tp.relative_to(root)}`")
        else:
            parts.append("- **tests:** NÃO ENCONTRADO")
        if a.docker_files:
            parts.append("- **docker:**")
            for df in a.docker_files[:5]:
                parts.append(f"  - `{df.relative_to(root)}`")
        else:
            parts.append("- **docker:** NÃO ENCONTRADO")
        parts.append("")
    return "\n".join(parts), agents


def section_io(root: Path, agents: list[AgentInventory], snip: int) -> str:
    parts = []
    for a in agents:
        parts.append(f"### {a.name}")
        evidence = []
        # config first
        if a.config_path:
            txt = read_text_safe(a.config_path)
            sn = snippet_with_context(
                txt,
                r"(input|inputs|output|outputs|dir|schema|io\.schema|stage|01_|02_|03_|04_)",
                3,
                3,
            )
            if sn:
                evidence.append(
                    f"**config:** `{a.config_path.relative_to(root)}`\n\n```text\n{md_escape('\\n'.join(sn.splitlines()[:snip]))}\n```"
                )
        # entrypoints
        for ep in a.entrypoints[:2]:
            txt = read_text_safe(ep)
            sn = snippet_with_context(
                txt,
                r"(input|output|schema|io\.schema|outputs_dir|data/|outputs/|context)",
                3,
                2,
            )
            if sn:
                evidence.append(
                    f"**code:** `{ep.relative_to(root)}`\n\n```text\n{md_escape('\\n'.join(sn.splitlines()[:snip]))}\n```"
                )
        parts.append(
            "\n\n".join(evidence)
            if evidence
            else "_Sem trechos I/O evidentes encontrados._"
        )
        parts.append("")
    return "\n".join(parts)


def section_schemas(root: Path, agents: list[AgentInventory]) -> str:
    all_schemas = []
    for p in list_files(root):
        if p.is_file() and p.suffix.lower() == ".json" and "schema" in p.name.lower():
            all_schemas.append(p)
    consolidated = [p for p in all_schemas if "consolidated" in p.name.lower()]
    parts = [
        f"- **Total arquivos com 'schema' no nome:** {len(all_schemas)}",
        f"- **Com 'consolidated' no nome:** {len(consolidated)}",
        "",
        "### Amostra (até 50):",
    ]
    for p in all_schemas[:50]:
        parts.append(f"- `{p.relative_to(root)}`")
    # correlate by agent directory
    parts.append("\n### Por agente (quantidade em schemas/):")
    for a in agents:
        parts.append(f"- **{a.name}:** {len(a.schema_files)}")
    return "\n".join(parts)


def section_prompts(root: Path, agents: list[AgentInventory], snip: int) -> str:
    parts = []
    checks = [
        (
            "Literalidade / sem inferência",
            r"(literal|não deduz|nao deduz|não infer|nao infer|sem supos)",
        ),
        ("Âncoras (fls/Folha/Pág.)", r"(fls|folha|\[\[folha|\[pág\.)"),
        ("source_id/sha256", r"(source_id|sha256)"),
        (
            "Formato de evidência/prova",
            r"(prova|evidên|eviden|citar|ancorar|âncora|ancora)",
        ),
    ]
    for a in agents:
        parts.append(f"### {a.name}")
        if not a.prompt_files:
            parts.append("_Nenhum prompt encontrado._\n")
            continue
        for pf in a.prompt_files[:10]:
            txt = read_text_safe(pf)
            if not txt:
                continue
            parts.append(f"- **Prompt:** `{pf.relative_to(root)}`")
            for label, rx in checks:
                ok = "OK" if re.search(rx, txt, flags=re.IGNORECASE) else "FALTA"
                parts.append(f"  - {label}: **{ok}**")
            # include snippet around anchor rules
            sn = snippet_with_context(
                txt, r"(fls|folha|source_id|sha256|literal|não deduz|nao deduz)", 3, 1
            )
            if sn:
                parts.append(
                    "\n```text\n"
                    + md_escape("\n".join(sn.splitlines()[:snip]))
                    + "\n```\n"
                )
        parts.append("")
    return "\n".join(parts)


def section_mcp(root: Path, snip: int) -> str:
    # heuristic: find directories with mcp in name
    mcp_dirs = []
    for p in root.rglob("*"):
        if p.is_dir() and "mcp" in p.name.lower() and p.name not in SKIP_DIRS:
            mcp_dirs.append(p)
    mcp_dirs = sorted(set(mcp_dirs))[:10]

    parts = []
    if not mcp_dirs:
        return "_Nenhum diretório MCP encontrado por heurística (nome contendo 'mcp')._"

    parts.append("### Diretórios MCP encontrados")
    for d in mcp_dirs:
        parts.append(f"- `{d.relative_to(root)}`")
        # try entrypoints
        entry = []
        for cand in ("main.py", "server.py", "app.py", "__main__.py"):
            cp = d / cand
            if cp.exists():
                entry.append(cp)
        if entry:
            for ep in entry[:2]:
                txt = read_text_safe(ep)
                sn = snippet_with_context(
                    txt, r"(tool|tools|mcp|server|FastAPI|stdio|route)", 3, 2
                )
                parts.append(f"  - entrypoint: `{ep.relative_to(root)}`")
                if sn:
                    parts.append(
                        "    ```text\n"
                        + md_escape("\n".join(sn.splitlines()[:snip]))
                        + "\n    ```"
                    )
    # find repo-wide references to mcp usage
    hits = find_repo_files_by_patterns(root, KEY_PATTERNS["mcp"], max_hits=30)
    parts.append("\n### Referências a MCP (amostra)")
    for p, txt in hits[:10]:
        sn = snippet_with_context(txt, r"(mcp|tools?)", 2, 1)
        parts.append(f"- `{p.relative_to(root)}`")
        if sn:
            parts.append(
                "  ```text\n" + md_escape("\n".join(sn.splitlines()[:snip])) + "\n  ```"
            )
    return "\n".join(parts)


def section_validate(root: Path) -> str:
    # heuristic: look for known validators/scripts
    candidates = []
    for p in list_files(root):
        if (
            p.is_file()
            and p.suffix.lower() in (".py", ".sh", ".md")
            and any(
                k in p.name.lower() for k in ("validate", "schema", "check", "lint")
            )
        ):
            candidates.append(p)
    parts = [
        "### Sugestão de validação mínima (sem executar automaticamente)",
        "- Validar JSON (formato): `python -m json.tool <arquivo.json>`",
        "- Verificar sintaxe Python: `python -m compileall .`",
        "",
        "### Detectado no repo (heurística: nomes contendo validate/schema/check/lint):",
    ]
    for p in sorted(candidates)[:30]:
        parts.append(f"- `{p.relative_to(root)}`")
    return "\n".join(parts)


def section_outputs(root: Path, snip: int) -> str:
    outputs_dir = root / "outputs"
    if not outputs_dir.exists():
        return "_Diretório outputs/ não encontrado._"
    samples = select_output_samples(outputs_dir, per_stage=2)
    if not samples:
        return "_Nenhum .json encontrado em outputs/ (ou não acessível)._"
    parts = ["### Amostras (JSON) + checagem de rastreabilidade\n"]
    for p in samples:
        excerpt, ev = json_evidence(p, max_lines=snip)
        parts.append(f"- **Arquivo:** `{p.relative_to(root)}`")
        parts.append(
            f"  - source_id/sha256: **{'SIM' if ev['has_source_id'] else 'NÃO'}**"
        )
        parts.append(
            f"  - âncoras (fls/Folha/Pág.): **{'SIM' if ev['has_anchor'] else 'NÃO'}**"
        )
        if ev["anchor_hints"]:
            parts.append(f"  - pistas: `{', '.join(ev['anchor_hints'])}`")
        if excerpt:
            parts.append("  ```text\n" + md_escape(excerpt) + "\n  ```")
        parts.append("")
    return "\n".join(parts)


def section_deps(root: Path) -> str:
    deps = parse_pyproject_deps(root)
    pp = root / "pyproject.toml"
    parts = []
    if pp.exists():
        parts.append(f"- **pyproject.toml:** `{pp.relative_to(root)}`")
    else:
        parts.append("- **pyproject.toml:** NÃO ENCONTRADO")
        return "\n".join(parts)

    project_deps = deps.get("project", []) or []
    focus = []
    for d in project_deps:
        low = str(d).lower()
        if any(
            k in low
            for k in (
                "langchain",
                "langgraph",
                "pydantic",
                "google",
                "genai",
                "openai",
                "anthropic",
                "qdrant",
                "chromadb",
                "fastapi",
                "uvicorn",
            )
        ):
            focus.append(d)

    parts.append("\n### Dependências (foco LangChain/LLM/RAG)")
    if focus:
        for d in focus:
            parts.append(f"- {d}")
    else:
        parts.append(
            "_Nenhuma dependência foco encontrada em project.dependencies (pode estar em optional-dependencies ou outro arquivo)._"
        )

    opt = deps.get("optional", {}) or {}
    if opt:
        parts.append("\n### optional-dependencies (chaves)")
        for k in sorted(opt.keys())[:30]:
            parts.append(f"- {k} ({len(opt.get(k, []) or [])} deps)")
    return "\n".join(parts)


def section_summary(root: Path, agents: list[AgentInventory]) -> str:
    confirmed = []
    not_found = []
    inconclusive = []

    if (root / "agents").exists():
        confirmed.append("Pasta `agents/` existe (estrutura por agentes).")
    else:
        not_found.append("Pasta `agents/` NÃO ENCONTRADA.")

    # agents missing critical files -> inconclusive
    for a in agents:
        missing = []
        if not a.has_config:
            missing.append("config")
        if not a.has_io_schema:
            missing.append("io.schema")
        if not a.has_schemas_dir:
            missing.append("schemas/")
        if not a.prompt_files:
            missing.append("prompts")
        if missing:
            inconclusive.append(f"{a.name}: itens faltando ({', '.join(missing)}).")
        else:
            confirmed.append(
                f"{a.name}: possui config + io.schema + schemas/ + prompt(s)."
            )

    # detect critical strings
    hits_monetary = find_repo_files_by_patterns(
        root, [r"\b02_monetary\b", r"\b03_monetary\b"], max_hits=5
    )
    if hits_monetary:
        confirmed.append(
            "Referências a `02_monetary`/`03_monetary` encontradas (verificar consistência de paths)."
        )
    hits_claude = find_repo_files_by_patterns(
        root, [r"\bclaude\b", r"\banthropic\b"], max_hits=5
    )
    if hits_claude:
        confirmed.append(
            "Referências a Claude/Anthropic encontradas (provável legado/acoplamento)."
        )

    parts = [
        "### CONFIRMADO",
        *(f"- {x}" for x in confirmed[:30]),
        "",
        "### NÃO ENCONTRADO",
        *(f"- {x}" for x in not_found[:30]),
        "",
        "### INCONCLUSIVO",
        *(f"- {x}" for x in inconclusive[:50]),
    ]
    return "\n".join(parts)


def build_report(
    root: Path, only: Optional[set[str]], out_path: Path, snip: int
) -> None:
    sections = []

    def want(key: str) -> bool:
        return (only is None) or (key in only)

    if want("env"):
        sections.append("# 0) Ambiente e contexto do repo\n")
        sections.append(section_env(root))
        sections.append("\n---\n")

    if want("tree"):
        sections.append("# 1) Mapa estrutural (árvore resumida)\n")
        sections.append(
            "```text\n" + md_escape(collect_tree(root, max_depth=3)) + "\n```"
        )
        sections.append("\n---\n")

    agents: list[AgentInventory] = []
    if (
        want("agents")
        or want("io")
        or want("schemas")
        or want("prompts")
        or want("summary")
    ):
        agents_text, agents = section_agents(root, snip=snip)
        if want("agents"):
            sections.append("# 2) Inventário granular por agente (OK/FALTA/N/A)\n")
            sections.append(agents_text)
            sections.append("\n---\n")

    if want("io"):
        sections.append("# 3) Contratos de I/O (evidências em config/código)\n")
        sections.append(section_io(root, agents, snip=snip))
        sections.append("\n---\n")

    if want("schemas"):
        sections.append("# 4) Schemas (inventário)\n")
        sections.append(section_schemas(root, agents))
        sections.append("\n---\n")

    if want("prompts"):
        sections.append("# 5) Prompts e regras críticas (checagem)\n")
        sections.append(section_prompts(root, agents, snip=snip))
        sections.append("\n---\n")

    if want("mcp"):
        sections.append("# 6) MCP server e tools (heurístico)\n")
        sections.append(section_mcp(root, snip=snip))
        sections.append("\n---\n")

    if want("validate"):
        sections.append("# 7) Execução mínima e validação (sugestões + detecção)\n")
        sections.append(section_validate(root))
        sections.append("\n---\n")

    if want("outputs"):
        sections.append("# 8) Outputs e rastreabilidade (amostras)\n")
        sections.append(section_outputs(root, snip=snip))
        sections.append("\n---\n")

    if want("deps"):
        sections.append("# 9) Dependências e prontidão para LangChain\n")
        sections.append(section_deps(root))
        sections.append("\n---\n")

    if want("summary"):
        sections.append("# 10) Sumário (CONFIRMADO / NÃO ENCONTRADO / INCONCLUSIVO)\n")
        sections.append(section_summary(root, agents))
        sections.append("\n")

    out_path.write_text("\n".join(sections), encoding="utf-8", errors="replace")


def parse_only(s: Optional[str]) -> Optional[set[str]]:
    if not s:
        return None
    items = [x.strip().lower() for x in s.split(",") if x.strip()]
    valid = {
        "env",
        "tree",
        "agents",
        "io",
        "schemas",
        "prompts",
        "mcp",
        "validate",
        "outputs",
        "deps",
        "summary",
    }
    unknown = [x for x in items if x not in valid]
    if unknown:
        raise SystemExit(
            f"--only contém itens inválidos: {unknown}. Válidos: {sorted(valid)}"
        )
    return set(items)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="Caminho da raiz do repositório")
    ap.add_argument(
        "--out", default="levantamento_auto.md", help="Arquivo markdown de saída"
    )
    ap.add_argument(
        "--only",
        default=None,
        help="Seções: env,tree,agents,io,schemas,prompts,mcp,validate,outputs,deps,summary (separadas por vírgula)",
    )
    ap.add_argument(
        "--snip-lines",
        type=int,
        default=30,
        help="Máximo de linhas por trecho evidência",
    )
    args = ap.parse_args()

    root = Path(args.repo).resolve()
    if not root.exists():
        print(f"Repo não existe: {root}", file=sys.stderr)
        return 2

    only = parse_only(args.only)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    build_report(root, only, out_path, snip=args.snip_lines)
    print(f"OK: relatório gerado em {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
