#!/usr/bin/env bash
# md-frontmatter-yaml · run_example.sh
# ======================================
# Executa um teste ponta a ponta com um Markdown genérico limpo.
# Gera o arquivo de exemplo, aplica o frontmatter e valida o resultado.
#
# Uso:
#   bash scripts/run_example.sh [--verbose] [--report] [--strict]
#
# Dependências: Python 3.10+, pyyaml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(cd "$SKILL_DIR/../../.." && pwd)"   # ~/devops/juridico-cli

INPUT_DIR="$PROJECT_DIR/var/input/md-frontmatter-yaml"
OUTPUT_DIR="$PROJECT_DIR/var/output/md-frontmatter-yaml"
INPUT_MD="$INPUT_DIR/manual_procedimentos_limpo.md"
OUTPUT_MD="$OUTPUT_DIR/manual_procedimentos_final.md"

VERBOSE_FLAG=""
REPORT_FLAG=""
STRICT_FLAG=""

for arg in "$@"; do
  case "$arg" in
    --verbose) VERBOSE_FLAG="--verbose" ;;
    --report)  REPORT_FLAG="--report"   ;;
    --strict)  STRICT_FLAG="--strict"   ;;
  esac
done

mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

# ---------------------------------------------------------------------------
# Verificar pyyaml
# ---------------------------------------------------------------------------
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "[run_example] Instalando pyyaml..."
  pip install pyyaml --break-system-packages -q
fi

# ---------------------------------------------------------------------------
# Gerar Markdown de exemplo (se não existir)
# ---------------------------------------------------------------------------
if [ ! -f "$INPUT_MD" ]; then
  echo "[run_example] Gerando Markdown de entrada de exemplo..."
  cat > "$INPUT_MD" << 'MD_CONTENT'
<!-- page 1 -->
# MANUAL DE PROCEDIMENTOS OPERACIONAIS

Versão 3.2 — Revisado em Março de 2024
Responsável: Equipe de Infraestrutura

---

## 1. OBJETIVO

Este manual define os procedimentos padrão para execução das atividades
operacionais da unidade. Destina-se a todos os colaboradores envolvidos
nos processos de produção, controle e entrega.

<!-- page 2 -->
## 2. ESCOPO

O presente documento aplica-se a:

- Equipe de produção
- Equipe de controle de qualidade
- Equipe de logística
- Supervisores e coordenadores

## 3. DEFINIÇÕES

- **Ordem de Serviço (OS):** documento que autoriza a execução de uma atividade.
- **Não Conformidade (NC):** desvio identificado em relação ao padrão estabelecido.
- **Registro:** evidência documentada de uma atividade realizada.

<!-- page 3 -->
### 4. PROCEDIMENTO GERAL

4.1 Recebimento de Materiais

Ao receber materiais, o colaborador deve:

1. Conferir a nota fiscal com o pedido de compra
2. Verificar integridade das embalagens
3. Registrar entrada no sistema de controle

---

4.2 Execução da Atividade

Durante a execução, observe:

- Utilizar os EPIs indicados para cada função
- Preencher o formulário de OS ao início e ao fim
- Comunicar ao supervisor qualquer NC identificada

<!-- page 4 -->
## 5. REGISTROS E EVIDÊNCIAS

Todos os registros devem ser:

- Preenchidos de forma legível e completa
- Assinados pelo responsável pela execução
- Arquivados pelo prazo mínimo de 5 anos

<!-- page 5: empty -->
MD_CONTENT
  echo "[run_example] Criado: $INPUT_MD"
else
  echo "[run_example] Arquivo de entrada já existe: $INPUT_MD"
fi

# ---------------------------------------------------------------------------
# Aplicar frontmatter
# ---------------------------------------------------------------------------
echo ""
echo "[run_example] Aplicando frontmatter..."
echo "  Input:  $INPUT_MD"
echo "  Output: $OUTPUT_MD"
echo ""

python3 "$SCRIPT_DIR/apply_frontmatter.py" \
  --input   "$INPUT_MD" \
  --output  "$OUTPUT_MD" \
  --doc-type "manual" \
  --tags    "operações,manutenção,procedimentos" \
  $VERBOSE_FLAG $REPORT_FLAG

# ---------------------------------------------------------------------------
# Validar com verificação de preservação do corpo
# ---------------------------------------------------------------------------
echo ""
python3 "$SCRIPT_DIR/validate_output.py" \
  --input    "$OUTPUT_MD" \
  --original "$INPUT_MD" \
  $STRICT_FLAG

# ---------------------------------------------------------------------------
# Preview do frontmatter gerado
# ---------------------------------------------------------------------------
echo ""
echo "─── Frontmatter gerado ─────────────────────────────────────────────"
python3 - << PYEOF
from pathlib import Path
content = Path("$OUTPUT_MD").read_text()
end = content.find("\n---\n", 4)
if end != -1:
    print(content[:end+5])
else:
    print(content[:500])
PYEOF
echo "─────────────────────────────────────────────────────────────────────"
echo ""
echo "[run_example] Arquivo gerado: $OUTPUT_MD"
