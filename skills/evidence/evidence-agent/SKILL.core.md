# SKILL: Evidence Core (CAD-OBR)

## Objetivo
Cruzar dados de dívidas/ônus/novação para levantar evidências de inconsistências, manipulação de saldos, incongruências temporais e lacunas documentais.

## Regras
- Assuma como verdade o conjunto de informações fornecido no EVIDENCE_PACK.
- Não diga “não existe documento”. Use: “não consta referência suficiente no conjunto fornecido”.
- Cada finding deve ter suporte rastreável (support_rows com _src_file/_src_row).
- Produza inventário documental ao final:
  - documentos_apresentados: consolidação do que consta no pack
  - documentos_recomendados_para_colheita: o que falta para robustez probatória
