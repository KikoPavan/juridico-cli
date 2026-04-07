from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AG_DIR = ROOT / "agents" / "law-cli"
CFG = AG_DIR / "config.yaml"
MAIN = AG_DIR / "main.py"

if not AG_DIR.exists():
    raise SystemExit(f"ERRO: não encontrei {AG_DIR}")

# 1) Backup + escreve config.yaml no padrão (runtime/paths/skills_map/jobs/validation)
if CFG.exists():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = CFG.with_suffix(f".yaml.bak_{ts}")
    bak.write_text(CFG.read_text(encoding="utf-8"), encoding="utf-8")

CFG.write_text(
    """runtime:
  agent_name: "law-cli"
  agent_version: "0.1.0"
  description: "Gera law_pack_v1.json consultando leis no Qdrant (index_library_qdrant.py)"
paths:
  output_dir: "outputs/legal"
  logs_dir: "outputs/legal/00_logs/law-cli"
  triage_dir: "outputs/legal/00_triage/law-cli"
  tmp_dir: "outputs/legal/00_tmp/law-cli"
  processo_default: "outputs/processo/01_collector/collector_out_processo_consolidated.json"
  juntada_default: "outputs/juntada/01_collector/collector_out_juntada_procuracao_Juraci_para_Francisco.json"
skills_map: {}
jobs:
  build:
    out: "outputs/legal/law_pack_v1.json"
    top_k: 10
    doc_kind: "lei"
    index_script: "scripts/index_library_qdrant.py"
validation:
  io_schema: "agents/law-cli/io.schema.json"
""",
    encoding="utf-8",
)

# 2) Patch no main.py: garantir que out/top_k usem defaults do config.yaml (sem mudar CLI)
if not MAIN.exists():
    raise SystemExit(f"ERRO: não encontrei {MAIN}")

s = MAIN.read_text(encoding="utf-8")

# 2.1) Inserir helper de config se não existir
if "_load_project_cfg" not in s:
    insert_after = "app = typer.Typer"
    m = re.search(r"^app\s*=\s*typer\.Typer.*$", s, flags=re.M)
    if not m:
        raise SystemExit(
            "ERRO: não encontrei 'app = typer.Typer(...)' para inserir helpers."
        )

    helper = """
AGENT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = AGENT_DIR / "config.yaml"

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

def _load_project_cfg() -> dict:
    if yaml is None or not DEFAULT_CONFIG_PATH.exists():
        return {}
    data = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    return data if isinstance(data, dict) else {}

def _cfg_get(cfg: dict, *keys, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return default if cur is None else cur
""".lstrip("\n")

    # insere após a linha do app
    pos = m.end()
    s = s[:pos] + "\n\n" + helper + "\n" + s[pos:]

# 2.2) Inserir defaults dentro do build_cmd (função do comando build/run)
m2 = re.search(r"^def\s+build_cmd\s*\(", s, flags=re.M)
if not m2:
    # fallback: às vezes o comando pode se chamar build()
    m2 = re.search(r"^def\s+build\s*\(", s, flags=re.M)
    if not m2:
        raise SystemExit("ERRO: não encontrei def build_cmd(...) nem def build(...).")

# acha o fim do cabeçalho da função (linha que termina com '):')
start = m2.start()
head_end = s.find("):", start)
if head_end == -1:
    raise SystemExit(
        "ERRO: não consegui localizar o fim do cabeçalho da função build/build_cmd."
    )
head_end = s.find("\n", head_end)
if head_end == -1:
    raise SystemExit("ERRO: arquivo inesperado (sem newline após cabeçalho).")

# se já existe bloco cfg dentro da função, não duplica
func_body_preview = s[head_end : head_end + 500]
if "_load_project_cfg()" not in func_body_preview:
    injection = (
        "    cfg = _load_project_cfg()\n"
        "    if out is None:\n"
        "        out = Path(_cfg_get(cfg, 'jobs', 'build', 'out', default='outputs/legal/law_pack_v1.json'))\n"
        "    if top_k is None:\n"
        "        top_k = int(_cfg_get(cfg, 'jobs', 'build', 'top_k', default=10))\n\n"
    )
    s = s[: head_end + 1] + injection + s[head_end + 1 :]

MAIN.write_text(s, encoding="utf-8")

print("OK: law-cli alinhado ao padrão (config.yaml + defaults no main.py).")
