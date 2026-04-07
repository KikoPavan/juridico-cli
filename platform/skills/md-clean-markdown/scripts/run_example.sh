#!/usr/bin/env bash
# md-clean-markdown · run_example.sh
# =====================================
# Executa um teste ponta a ponta com um Markdown bruto genérico.
# Cria o arquivo de exemplo, executa a limpeza e valida o resultado.
#
# Uso:
#   bash scripts/run_example.sh [--verbose] [--report] [--strict]
#
# Dependências: Python 3.10+

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(cd "$SKILL_DIR/../../.." && pwd)"   # ~/devops/juridico-cli

INPUT_DIR="$PROJECT_DIR/var/input/md-clean-markdown"
OUTPUT_DIR="$PROJECT_DIR/var/output/md-clean-markdown"
INPUT_MD="$INPUT_DIR/manual_procedimentos_bruto.md"
OUTPUT_MD="$OUTPUT_DIR/manual_procedimentos_limpo.md"

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
# Gerar Markdown bruto de exemplo (se não existir)
# ---------------------------------------------------------------------------
if [ ! -f "$INPUT_MD" ]; then
  echo "[run_example] Gerando Markdown bruto de exemplo..."
  cat > "$INPUT_MD" << 'MD_CONTENT'
<!-- page 1 -->
#MANUAL DE PROCEDIMENTOS OPERACIONAIS   

Versão 3.2 — Revisado em Março de 2024   
Departamento de Operações   


   

===========================

<!-- page 2 -->
##2. ESCOPO

O presente documento aplica-se a:   

* Equipe de produção   
* Equipe de controle de qualidade   
+ Equipe de logística   
* Supervisores e coordenadores   


## 3. DEFINIÇÕES   

Abaixo estão os principais termos utilizados neste manual:   

* **Ordem de Serviço (OS):** documento que autoriza a execução de uma atividade.   
+ **Não Conformidade (NC):** desvio identificado em relação ao padrão estabelecido.   
* **Registro:** evidência documentada de uma atividade realizada.   



<!-- page 3 -->
###4. PROCEDIMENTO GERAL


4.1 Recebimento de Materiais   

Ao receber materiais, o colaborador deve:   

1. Conferir a nota fiscal com o pedido de compra   
2. Verificar integridade das embalagens   
3. Registrar entrada no sistema de controle   

* * *

4.2 Execução da Atividade   

Durante a execução, observe:   

+ Utilizar os EPIs indicados para cada função   
+ Preencher o formulário de OS ao início e ao fim   
+ Comunicar ao supervisor qualquer NC identificada   


<!-- page 4 -->
##5. RESPONSABILIDADES



| Função          | Responsabilidade                         |   
|-----------------|-------------------------------------------|   
| Operador        | Executar conforme procedimento            |   
| Supervisor      | Validar e registrar as OSs                |   
| Coordenador     | Garantir conformidade geral do processo   |   

_ _ _

##6. REGISTROS E EVIDÊNCIAS   

Todos os registros devem ser:   

* Preenchidos de forma legível e completa   
* Assinados pelo responsável pela execução   
* Arquivados pelo prazo mínimo de 5 anos   



.................

<!-- page 5: empty -->
MD_CONTENT
  echo "[run_example] Arquivo criado: $INPUT_MD"
else
  echo "[run_example] Arquivo de entrada já existe: $INPUT_MD"
fi

# ---------------------------------------------------------------------------
# Executar limpeza
# ---------------------------------------------------------------------------
echo ""
echo "[run_example] Executando limpeza..."
echo "  Input:  $INPUT_MD"
echo "  Output: $OUTPUT_MD"
echo ""

python3 "$SCRIPT_DIR/clean_markdown.py" \
  --input  "$INPUT_MD" \
  --output "$OUTPUT_MD" \
  $VERBOSE_FLAG $REPORT_FLAG

# ---------------------------------------------------------------------------
# Validar output
# ---------------------------------------------------------------------------
echo ""
python3 "$SCRIPT_DIR/validate_output.py" --input "$OUTPUT_MD" $STRICT_FLAG

# ---------------------------------------------------------------------------
# Diff resumido (se diff disponível)
# ---------------------------------------------------------------------------
if command -v diff &>/dev/null; then
  echo ""
  echo "─── Diff (entrada vs saída) ─────────────────────────────────────────"
  diff --unified=0 "$INPUT_MD" "$OUTPUT_MD" | head -60 || true
  echo "─────────────────────────────────────────────────────────────────────"
fi

# ---------------------------------------------------------------------------
# Preview da saída
# ---------------------------------------------------------------------------
echo ""
echo "─── Preview da saída (primeiras 30 linhas) ──────────────────────────"
head -n 30 "$OUTPUT_MD" || true
echo "─────────────────────────────────────────────────────────────────────"
echo ""
echo "[run_example] Arquivo gerado: $OUTPUT_MD"
