#!/usr/bin/env bash
# md-frontmatter-yaml · package_skill.sh
# ========================================
# Empacota a skill md-frontmatter-yaml em arquivo .zip para distribuição.
#
# Saída: ~/devops/juridico-cli/var/artifacts/skills/md-frontmatter-yaml.zip
#
# Uso:
#   bash scripts/package_skill.sh [--output CAMINHO]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(cd "$SKILL_DIR/../../.." && pwd)"   # ~/devops/juridico-cli

DEFAULT_ZIP="$PROJECT_DIR/var/artifacts/skills/md-frontmatter-yaml.zip"
OUTPUT_ZIP="$DEFAULT_ZIP"

for i in "$@"; do
  case "$i" in
    --output=*) OUTPUT_ZIP="${i#*=}" ;;
    --output)   shift; OUTPUT_ZIP="$1" ;;
  esac
done

echo "[package_skill] Empacotando: md-frontmatter-yaml"
echo "  Origem:  $SKILL_DIR"
echo "  Destino: $OUTPUT_ZIP"
echo ""

mkdir -p "$(dirname "$OUTPUT_ZIP")"
[ -f "$OUTPUT_ZIP" ] && rm "$OUTPUT_ZIP"

PARENT_DIR="$(dirname "$SKILL_DIR")"
SKILL_NAME="$(basename "$SKILL_DIR")"

cd "$PARENT_DIR"

zip -r "$OUTPUT_ZIP" "$SKILL_NAME" \
  --exclude "*/__pycache__/*" \
  --exclude "*/*.pyc" \
  --exclude "*/.DS_Store" \
  --exclude "*/\.*"

echo ""
echo "[package_skill] Conteúdo do ZIP:"
unzip -l "$OUTPUT_ZIP" \
  | grep -v "^Archive" \
  | grep -v "^\-\-\-" \
  | grep -v "^  Length"

echo ""
SIZE=$(du -sh "$OUTPUT_ZIP" | cut -f1)
echo "[package_skill] ✓ Empacotado com sucesso!"
echo "  Arquivo: $OUTPUT_ZIP"
echo "  Tamanho: $SIZE"
