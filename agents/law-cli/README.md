# law-cli

Gera um pacote de base legal (`outputs/legal/law_pack_v1.json`) consultando leis já vetorizadas no Qdrant.

## Input
- outputs/processo/collector_out_processo_consolidado_v1.json (ou equivalente)

## Output
- outputs/legal/law_pack_v1.json

## Execução
Exemplos:
- Listar coleções:
  python agents/law-cli/main.py collections
- Gerar law_pack (auto-detect coleção):
  python agents/law-cli/main.py build --processo outputs/processo/collector_out_processo_consolidado_v1.json
- Forçar coleção e data:
  python agents/law-cli/main.py build --processo outputs/processo/collector_out_processo_consolidado_v1.json --collection bj_leis --effective-date 1994-06-10
