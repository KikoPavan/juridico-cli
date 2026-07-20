## Why

O mapa de roteamento canônico e o mapa embutido no curador encaminham alguns tipos documentais para extratores inexistentes ou para destinos divergentes, permitindo que peças avancem como roteáveis sem uma skill registrada. A correção deve tornar o `skill_registry.yaml` a fronteira de validade e preservar tipos sem extrator para revisão manual segura.

## What Changes

- Alinhar `routing_map.yaml` ao conjunto de `skill_key` existente em `skill_registry.yaml`, admitindo apenas skills registradas ou o sentinela `REVISAR_MANUAL`.
- Adicionar rotas explícitas para `contrato_social`, `escritura_imovel` e `escritura_hipotecaria` e preservar as rotas válidas de peças processuais, incluindo `sentenca` por `extr-decisao-processo`.
- Tornar `contrato`, `escritura` e os demais tipos sem extrator não roteáveis, com `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review` no resultado normalizado.
- Alinhar o curador à fonte canônica de roteamento, preferencialmente carregando `routing_map.yaml`, sem manter decisões de destino conflitantes.
- Preservar `capa_processo` fora da extração jurídica profunda, seja removida pelo curador ou encaminhada para revisão manual defensiva.
- Adicionar testes de integridade entre mapa e registro e testes de consistência entre as rotas observadas pelo curador e pelo normalizador.
- Manter fora do escopo alterações em `pdf-to-md`, `md-clean-markdown` e em qualquer skill `extr-*`.

## Capabilities

### New Capabilities

- `registered-extractor-routing`: Define a fonte canônica, as rotas explícitas válidas e a validação de integridade entre tipos documentais, mapa de roteamento, curador e registro de skills.

### Modified Capabilities

- `safe-unroutable-piece-handling`: Explicita quais tipos conhecidos sem extrator, inclusive contratos e escrituras genéricos, devem terminar em revisão manual e nunca declarar uma skill inexistente.

## Impact

- Afeta `platform/skills/yaml-normalizador-juridico/assets/routing_map.yaml`, o roteamento em `platform/skills/curador-relevancia/scripts/curar.py` e testes focados dessas skills/pipeline.
- Usa `platform/skill-runtime/skill_registry.yaml` como autoridade para validar destinos `extr-*`; não adiciona extratores nem altera contratos externos.
- Deve consultar `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md` durante a implementação.
