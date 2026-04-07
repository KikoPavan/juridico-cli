#!/usr/bin/env bash
# pdf-to-md · run_example.sh
# ===========================
# Executa um teste de ponta a ponta com um documento genérico.
# Gera um PDF sintético (relatório técnico corporativo) e converte para .md.
#
# Uso:
#   bash scripts/run_example.sh [--verbose] [--report]
#
# Requer: Python 3.10+, pdfminer.six ou pymupdf

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(cd "$SKILL_DIR/../../.." && pwd)"  # ~/devops/juridico-cli

INPUT_DIR="$PROJECT_DIR/var/input/pdf-to-md"
OUTPUT_DIR="$PROJECT_DIR/var/output/pdf-to-md"
EXAMPLE_PDF="$INPUT_DIR/relatorio_eficiencia_operacional.pdf"
EXAMPLE_MD="$OUTPUT_DIR/relatorio_eficiencia_operacional.md"

VERBOSE=""
REPORT=""
for arg in "$@"; do
  case $arg in
    --verbose) VERBOSE="--verbose" ;;
    --report)  REPORT="--report"  ;;
  esac
done

mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

# ---------------------------------------------------------------------------
# Gerar PDF de exemplo (relatório técnico genérico)
# ---------------------------------------------------------------------------
if [ ! -f "$EXAMPLE_PDF" ]; then
  echo "[run_example] Gerando PDF de exemplo (relatório técnico)..."

  EXAMPLE_PDF_PATH="$EXAMPLE_PDF" python3 - <<'PYEOF'
import os, sys
from pathlib import Path

output = Path(os.environ["EXAMPLE_PDF_PATH"])
output.parent.mkdir(parents=True, exist_ok=True)

try:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Página 1
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RELATÓRIO DE EFICIÊNCIA OPERACIONAL", ln=True, align="C")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, "Período: Janeiro a Junho de 2024", ln=True, align="C")
    pdf.cell(0, 8, "Departamento de Operações", ln=True, align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Sumário Executivo", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7,
        "Este relatório apresenta os principais indicadores de desempenho "
        "operacional registrados no primeiro semestre de 2024, com base nas "
        "métricas coletadas pelas equipes de campo e pelos sistemas de "
        "monitoramento interno.\n\n"
        "Os resultados indicam melhora consistente em 3 dos 5 indicadores "
        "acompanhados, com destaque para a redução do tempo médio de resposta "
        "e o aumento da taxa de disponibilidade dos equipamentos."
    )

    # Página 2
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "1. Indicadores de Desempenho", ln=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "1.1 Tempo Médio de Resposta (TMR)", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, "Meta: 4 horas | Realizado: 3,2 horas | Variação: -20%", ln=True)
    pdf.multi_cell(0, 7,
        "O TMR reduziu em 20% em relação ao semestre anterior, resultado "
        "da implementação do novo protocolo de triagem iniciado em março."
    )
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "1.2 Taxa de Disponibilidade de Equipamentos", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, "Meta: 95% | Realizado: 97,3% | Variação: +2,3 p.p.", ln=True)
    pdf.multi_cell(0, 7,
        "A taxa superou a meta estabelecida. As manutenções preventivas "
        "realizadas em fevereiro contribuíram diretamente para esse resultado."
    )
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "1.3 Índice de Retrabalho", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, "Meta: < 5% | Realizado: 6,8% | Variação: +1,8 p.p.", ln=True)
    pdf.multi_cell(0, 7, "O índice ficou acima da meta. Causas identificadas:")
    for item in [
        "Falha no processo de verificação de qualidade na etapa 3",
        "Ausência de padronização nos registros da equipe B",
        "Necessidade de atualização do manual de procedimentos",
    ]:
        pdf.cell(8, 7, "", ln=False)
        pdf.cell(0, 7, f"• {item}", ln=True)

    # Página 3
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "2. Ocorrências do Período", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7,
        "Durante o semestre foram registradas 142 ocorrências. Distribuição:"
    )
    pdf.ln(2)
    for row in [
        ("Falha de equipamento", "58", "40,8%"),
        ("Erro operacional",     "41", "28,9%"),
        ("Atraso de fornecedor", "27", "19,0%"),
        ("Outros",               "16", "11,3%"),
    ]:
        pdf.cell(80, 7, row[0], border=1)
        pdf.cell(30, 7, row[1], border=1, align="C")
        pdf.cell(30, 7, row[2], border=1, align="C")
        pdf.ln()
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "3. Recomendações", ln=True)
    pdf.set_font("Helvetica", size=11)
    for i, rec in enumerate([
        "Revisar o manual de procedimentos da equipe B até agosto/2024",
        "Implementar checklist digital na etapa de verificação de qualidade",
        "Negociar SLA mais rigoroso com os dois principais fornecedores",
        "Ampliar cobertura do programa de manutenção preventiva",
    ], 1):
        pdf.cell(0, 7, f"{i}. {rec}", ln=True)

    # Página 4
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "4. Próximos Passos", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7,
        "O Departamento de Operações apresentará plano de ação detalhado "
        "para os itens identificados até 31 de julho de 2024.\n\n"
        "O acompanhamento dos indicadores continuará com frequência mensal "
        "e os resultados serão consolidados no relatório do segundo semestre.\n\n"
        "Elaborado por: Equipe de Análise Operacional\n"
        "Data: 15 de julho de 2024\nVersão: 1.0"
    )

    pdf.output(str(output))
    print(f"[run_example] PDF gerado com fpdf2: {output}")

except ImportError:
    print("[run_example] fpdf2 não disponível — gerando PDF mínimo válido...")
    # PDF de 2 páginas com texto básico (sem dependências externas)
    p1 = b"BT /F1 12 Tf 72 770 Td (RELATORIO DE EFICIENCIA OPERACIONAL) Tj 0 -20 Td (Periodo: Janeiro a Junho de 2024) Tj ET"
    p2 = b"BT /F1 12 Tf 72 770 Td (1. Indicadores de Desempenho) Tj 0 -20 Td (1.1 Tempo Medio de Resposta: 3,2 horas) Tj ET"
    def make_pdf(streams):
        objs, offsets, pdf = [], [], b"%PDF-1.4\n"
        def add(obj):
            offsets.append(len(pdf))
            objs.append(obj)
            return len(objs)
        catalog = add(b"")
        pages   = add(b"")
        page_ids = []
        content_ids = []
        for s in streams:
            cid = add(s)
            content_ids.append(cid)
            pid = add(b"")
            page_ids.append(pid)
        font = add(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
        # re-build
        pdf_parts = [b"%PDF-1.4\n"]
        offsets2 = []
        def emit(obj_bytes):
            idx = len(offsets2) + 1
            offsets2.append(len(b"".join(pdf_parts)))
            pdf_parts.append(f"{idx} 0 obj\n".encode() + obj_bytes + b"\nendobj\n")
        emit(f"<</Type/Catalog/Pages {len(streams)*2+2} 0 R>>".encode())
        for i, (cid, pid) in enumerate(zip(content_ids, page_ids)):
            pass
        # simplified single-pass
        out = b"%PDF-1.4\n"
        refs, off = [], []
        def o(b):
            off.append(len(out)); refs.append(b); return len(refs)
        # just write plain text PDF
        import struct
        lines = [b"%PDF-1.4"]
        obj_offsets = []
        objs_data = [
            b"<</Type/Catalog/Pages 2 0 R>>",
            f"<</Type/Pages/Kids[{' '.join(f'{3+i*2} 0 R' for i in range(len(streams)))}]/Count {len(streams)}>>".encode(),
        ]
        for i, s in enumerate(streams):
            objs_data.append(f"<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Contents {4+i*2} 0 R/Resources<</Font<</F1 {3+len(streams)*2} 0 R>>>>>>".encode())
            objs_data.append(f"<</Length {len(s)}>>stream\n".encode() + s + b"\nendstream")
        objs_data.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
        body = b""
        for i, d in enumerate(objs_data):
            obj_offsets.append(len(b"\n".join(lines)) + len(body) + 1)
            body += f"\n{i+1} 0 obj\n".encode() + d + b"\nendobj"
        xref_offset = len(b"\n".join(lines)) + len(body) + 1
        xref = f"\nxref\n0 {len(objs_data)+1}\n0000000000 65535 f \n"
        for o in obj_offsets:
            xref += f"{o:010d} 00000 n \n"
        trailer = f"trailer<</Size {len(objs_data)+1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF\n"
        return b"\n".join(lines) + body + xref.encode() + trailer.encode()
    output.write_bytes(make_pdf([p1, p2]))
    print(f"[run_example] PDF mínimo gerado: {output}")
PYEOF
else
  echo "[run_example] PDF já existe: $EXAMPLE_PDF"
fi

# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------
echo ""
echo "[run_example] Convertendo..."
echo "  Input:  $EXAMPLE_PDF"
echo "  Output: $EXAMPLE_MD"
echo ""

python3 "$SCRIPT_DIR/convert_pdf_to_md.py" \
  --input  "$EXAMPLE_PDF" \
  --output "$EXAMPLE_MD" \
  $VERBOSE $REPORT

echo ""
echo "[run_example] Convertido."

# ---------------------------------------------------------------------------
# Validar
# ---------------------------------------------------------------------------
echo ""
echo "[run_example] Validando output..."
python3 "$SCRIPT_DIR/validate_output.py" --input "$EXAMPLE_MD"

# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------
echo ""
echo "[run_example] Preview (primeiras 20 linhas):"
echo "──────────────────────────────────────────────"
head -n 20 "$EXAMPLE_MD" || true
echo "──────────────────────────────────────────────"
echo ""
echo "[run_example] Arquivo completo: $EXAMPLE_MD"
