## Why

O `_compatible_partial_identity` rejeita `separador_de_evento` como compatível com a peça real do mesmo evento quando ambos descrevem a mesma página no overlap entre janelas. Isso faz a consolidação falhar com `ValueError` ("sobreposição indevida") e coloca todo o documento em `needs_review`, mesmo quando a evidência estrutural é suficiente.

Além disso, o LLM produz fragmentações não-determinísticas entre execuções: a mesma página pode ser classificada em eventos diferentes, ou o mesmo evento pode ser fragmentado em múltiplos descritores. A consolidação atual só une peças sobrepostas — não peças contíguas com a mesma identidade judicial forte.

No caso real, a página física 3 é um separador estrutural do evento 1 no Markdown original. O LLM pode devolvê-la como `separador_de_evento`, `nao_classificado` ou já incluída em `peticao_inicial`; essas três representações precisam convergir para a mesma peça canônica 3-18, identificada por evento 1 e `INIC1`.

## What Changes

- `_compatible_partial_identity`: regra de absorção para `separador_de_evento` sobreposto a peça real (já implementado).
- `_merge_partial_pieces`: etapa de coalescência determinística de fragmentos contíguos com mesma identidade forte (process_number, event, document_code) após a reconciliação de overlaps.
- Absorção de `nao_classificado` adjacente `à` peça específica com mesma identidade (exige `process_number` no locator da página órfã).
- Normalização de tipo documental para valor estável aceito pelo schema e routing_map: tipos da família de decisão (`despacho_decisao`, `decisao`, `decisao_interlocutoria`) são consolidados com base na precedência e no texto original.
- Nenhuma alteração em schemas canônicos, estratégias de extração por blocos ou configuração de LLM.
- Normalização pós-LLM baseada no Markdown e nos `judicial_locator`: um separador estrutural é absorvido pela peça específica seguinte somente com mesmo processo e evento, código documental seguinte válido, ausência de código conflitante no separador e ausência de documento específico concorrente no limite.
- A representação canônica do caso real é fixada em 7 peças; resultados 7×8 não atendem ao critério.

## Critério de Aceitação

O teste operacional com `Processo.pdf` deve produzir:
- Cobertura integral 1-35, sem lacunas ou duplicação
- 7 peças (capa_processo 1-2, peticao_inicial 3-18 com event separator absorvido, nao_classificado 19-21, nao_classificado 22-25, 3× decisao/despacho 26-35)
- Event separator page 3 absorvido em `peticao_inicial` (mesmo evento 1)
- Páginas 19-21 preservadas como `nao_classificado` autônomo (órfãs sem `process_number`)
- Tipos canônicos aceitos pelo `output-schema.json` e routing_map
- Três execuções em diretórios isolados produzem deterministicamente o mesmo hash canônico
- Todas as peças com `document_type_confidence` high ou low, nunca sem classificação

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `segmentador-juridico-resilient-processing`: requisitos expandidos para incluir coalescência por identidade forte, absorção de `nao_classificado` adjacente e normalização de tipo documental na família de decisão.

## Impact

- `stage_router.py`: novas funções `_coalesce_contiguous_fragments`, `_should_coalesce`; integração em `_merge_partial_pieces`.
- `test_segmentador_resilient_processing.py`: +14 testes de coalescência.
- Nenhum schema alterado.
