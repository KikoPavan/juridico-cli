## Missão
Gerar um pacote de regras legais ("law_pack_v1") relevante ao caso, a partir do PROCESSO e JUNTADAS, consultando a biblioteca de leis indexada (Qdrant).

## Entradas
- PROCESSO consolidado (JSON)
- 0..n JUNTADAS (JSON)
- effective_date (YYYY-MM-DD) opcional
- top_k opcional

## Saídas
- outputs/legal/law_pack_v1.json (envelope + payload.rules com suporte/locator)
- logs/triage conforme paths no config.yaml

## Restrições
- Não inventar artigos/trechos: cada regra deve manter source_id/anchor e locator.
