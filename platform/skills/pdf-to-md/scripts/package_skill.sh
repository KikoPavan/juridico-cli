#!/usr/bin/env bash
# pdf-to-md · package_skill.sh
# ==============================
# Empacota a skill pdf-to-md em .zip para distribuição.
#
# Saída padrão: ~/devops/juridico-cli/var/artifacts/skills/pdf-to-md.zip
#
# Uso:
#   bash scripts/package_skill.sh [--output CAMINHO_ZIP]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(cd "$SKILL_DIR/../../.." && pwd)"

OUTPUT_ZIP="$PROJECT_DIR/var/artifacts/skills/pdf-to-md.zip"

# Parse --output flag
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT_ZIP="$2"; shift 2 ;;
    --output=*) OUTPUT_ZIP="${1#*=}"; shift ;;
    *) shift ;;
  esac
done

echo "[package_skill] Empacotando skill: pdf-to-md"
echo "  Origem:  $SKILL_DIR"
echo "  Destino: $OUTPUT_ZIP"
echo ""

mkdir -p "$(dirname "$OUTPUT_ZIP")"
[ -f "$OUTPUT_ZIP" ] && rm "$OUTPUT_ZIP"

PARENT="$(dirname "$SKILL_DIR")"
NAME="$(basename "$SKILL_DIR")"

cd "$PARENT"
zip -r "$OUTPUT_ZIP" "$NAME" \
  --exclude "*/__pycache__/*" \
  --exclude "*/*.pyc" \
  --exclude "*/.DS_Store" \
  --exclude "*/\.*"

echo ""
echo "[package_skill] Conteúdo do ZIP:"
unzip -l "$OUTPUT_ZIP" | tail -n +4 | head -n -2

echo ""
SIZE=$(du -sh "$OUTPUT_ZIP" | cut -f1)
echo "[package_skill] ✓ Empacotado com sucesso!"
echo "  Arquivo: $OUTPUT_ZIP"
echo "  Tamanho: $SIZE"
