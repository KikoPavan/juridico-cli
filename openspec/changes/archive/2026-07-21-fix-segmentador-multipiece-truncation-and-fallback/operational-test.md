## Teste operacional pendente: Processo.pdf

Este procedimento é deliberadamente externo à suíte automatizada e realiza chamadas reais ao Gemini. Executá-lo somente com credenciais operacionais válidas, depois das validações automatizadas e antes de arquivar a change.

```bash
SEGMENTADOR_OP_DIR="$(mktemp -d var/tmp/processo-segmentador-XXXXXX)"
mkdir -p "$SEGMENTADOR_OP_DIR/pdf" "$SEGMENTADOR_OP_DIR/md" "$SEGMENTADOR_OP_DIR/clean" "$SEGMENTADOR_OP_DIR/segmentador"
cp var/input/raw/pdfs/Processo.pdf "$SEGMENTADOR_OP_DIR/pdf/Processo.pdf"
uv run python apps/data-processing/main.py convert --input "$SEGMENTADOR_OP_DIR/pdf" --output "$SEGMENTADOR_OP_DIR/md"
uv run python apps/data-processing/main.py clean --input "$SEGMENTADOR_OP_DIR/md" --output "$SEGMENTADOR_OP_DIR/clean"
SEGMENTADOR_OP_DIR="$SEGMENTADOR_OP_DIR" PYTHONPATH=apps/data-processing/src:packages/shared-llm uv run python -c "import os; from pathlib import Path; from data_processing.orchestrator.stage_router import run_segmentador_stage; root=Path(os.environ['SEGMENTADOR_OP_DIR']); print(run_segmentador_stage(root/'clean', root/'segmentador'))"
```

Critérios de aceite:

- o preflight registra `page_windows` para `Processo.md`;
- todas as janelas terminam sem JSON truncado;
- o resultado não usa estratégia `extr-*`;
- `envelope_segmentacao.json` existe, valida pelo schema canônico e contém todas as peças sem duplicação, lacunas ou sobreposição indevida;
- `process_number`, evento, código, páginas, origem e `judicial_locator` conferem com o Markdown convertido;
- qualquer ambiguidade produz `segmentacao_lote.json` com `needs_review`, diagnóstico exclusivo e nenhum envelope final inválido.

Após executar, registrar diretório, timestamp, resultado e inspeção humana. Até isso ocorrer, a tarefa 7.6 permanece desmarcada e a change não pode ser arquivada.

## Resultado registrado em 2026-07-21

- Origem real analisada: `var/tmp/processo-segmentador-1CX82M/pdf/Processo.pdf`.
- Markdown limpo reutilizado: `var/tmp/processo-segmentador-1CX82M/clean/Processo_clean.md`.
- Saída aceita: `var/tmp/processo-segmentador-1CX82M/segmentador-pos-fix-cobertura/envelope_segmentacao.json`.
- Preflight: 35 páginas, 54.604 caracteres, estratégia `page_windows`.
- Janelas: 1–12 (3 descritores), 12–23 (2), 23–34 (4), 34–35 (1).
- Consolidação: 8 peças finais, `peca_001` a `peca_008`, ordenadas pelas páginas.
- Inspeção: cobertura física exata 1–35, sem lacunas nem duplicações; `judicial_locator` e `source_file` preservados em todas as peças.
- Validação: envelope aprovado por `platform/skills/segmentador-juridico/assets/output-schema.json`.
- Nenhuma estratégia `extr-*` foi usada. A change permanece não arquivada e sem commit/push.
