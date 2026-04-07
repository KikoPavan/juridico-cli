#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

AG="agents/law-cli"
TS="$(date -u +"%Y%m%d_%H%M%SZ")"
LOG="outputs/legal/00_logs/law-cli/inspect_${TS}.log"

mkdir -p "$(dirname "$LOG")"

{
  echo "=== INSPECT law-cli (${TS}) ==="
  echo

  echo "## 1) Estrutura do agente"
  ls -al "$AG"
  echo

  echo "## 2) config.yaml (padrão runtime/paths/jobs/validation etc.)"
  if test -f "$AG/config.yaml"; then
    echo "OK: tem config.yaml"
  else
    echo "ERRO: sem config.yaml"
  fi
  echo

  echo "### 2.1) Top-level keys"
  rg -n "^(agent:|runtime:|paths:|front_matter:|validation:|routing:|skills_map:|jobs:)" "$AG/config.yaml" || true
  echo

  echo "### 2.2) Campos de paths/jobs"
  rg -n "input_dir:|file_glob:|output_base_dir:|triage_dir:|logs_dir:|output_dir:|schema_(individual|consolidated):|skill_key:" "$AG/config.yaml" || true
  echo

  echo "## 3) CLI (Typer) help"
  uv run python3 "$AG/main.py" --help
  echo

  echo "## 4) Subcomando run help"
  uv run python3 "$AG/main.py" run --help
  echo

  echo "## 5) Compilação"
  uv run python3 -m py_compile "$AG/main.py"
  echo "main.py compila OK"
  echo

  echo "## 6) Contrato/flags no main.py (rastreamento rápido)"
  rg -n "@app\.command|def build_cmd\(|def build\(|def run\(|typer\.Option\(" "$AG/main.py" || true
  echo

  echo "=== FIM ==="
} | tee "$LOG"

echo "OK: log salvo em $LOG"
