## Context

O normalizador já lê `routing_map.yaml`, mas o curador mantém um dicionário próprio em Python. Os dois conjuntos divergiram e ambos passaram a referenciar extratores ausentes de `platform/skill-runtime/skill_registry.yaml`. Como a decisão atravessa duas skills e o runtime, a mudança precisa definir uma única autoridade de rota e uma verificação automática da fronteira entre configuração e registro.

## Goals / Non-Goals

**Goals:**

- Fazer de `routing_map.yaml` a fonte canônica da associação entre `document_type` e destino.
- Considerar roteável somente um destino `extr-*` registrado no `skill_registry.yaml`.
- Produzir revisão manual segura e estados coerentes para tipos sem extrator.
- Eliminar a divergência comportamental entre curador e normalizador com testes parametrizados sobre tipos comuns.

**Non-Goals:**

- Criar, renomear ou modificar extratores.
- Alterar `pdf-to-md` ou `md-clean-markdown`.
- Mudar classificação documental, regras de relevância ou o tratamento administrativo de `capa_processo` além do necessário para preservar a ausência de extração profunda.
- Introduzir novo serviço, runtime ou dependência externa.

## Decisions

### `routing_map.yaml` será a autoridade compartilhada

O curador carregará o mesmo arquivo usado pelo normalizador, resolvendo o caminho de forma estável a partir da árvore do projeto e usando uma função pequena de leitura/resolução. Assim, novos tipos são cadastrados uma vez e a política de extensão já documentada no mapa permanece válida.

Alternativa considerada: manter o dicionário Python e compará-lo em testes. Embora aceitável como defesa, ainda duplica dados e permite divergência até a execução dos testes; por isso será usada apenas se uma limitação concreta impedir o carregamento compartilhado.

### `REVISAR_MANUAL` será o único destino não registrado permitido

Um teste de integridade percorrerá todas as entradas e o fallback do mapa. Cada `skill_key` deverá existir em `skill_registry.yaml`, exceto o sentinela `REVISAR_MANUAL`. Entradas manuais terão metadados de não roteabilidade, e o normalizador continuará impondo `review_status: unroutable` e `status: needs_review` mesmo quando a ação curatorial recebida for `manter` ou `resumir`.

### Tipos específicos serão roteados; tipos genéricos serão conservadores

`contrato_social`, `escritura_imovel` e `escritura_hipotecaria` terão destinos registrados específicos. `contrato` e `escritura` não inferirão subtipo e irão para revisão manual. A mesma política será aplicada a `recurso`, `laudo_pericial`, `nota_fiscal`, `boleto`, `citacao`, `intimacao` e `nao_classificado`. `sentenca` reutilizará `extr-decisao-processo`.

### O contrato do curador continuará usando ausência de encaminhamento para não roteáveis

Para compatibilidade com o envelope curado, rotas `REVISAR_MANUAL` serão representadas por `encaminhamento: null` no curador; no normalizador, o mesmo tipo será resolvido ao sentinela e aos estados de revisão. O teste de consistência comparará equivalência semântica (`null` ↔ `REVISAR_MANUAL`) e igualdade literal para destinos `extr-*`.

## Risks / Trade-offs

- [Carregamento do mapa falha por caminho ou YAML inválido] → resolver o caminho relativamente ao módulo, falhar de modo explícito/testável e cobrir carregamento em teste focado.
- [Consumidores interpretam `encaminhamento: null` e `REVISAR_MANUAL` como divergentes] → documentar e testar a equivalência entre os contratos de cada estágio.
- [Novo extrator é adicionado ao mapa sem registro] → teste de integridade bloqueia a mudança antes da integração.
- [Tipos genéricos deixam de ser extraídos automaticamente] → aceitar revisão manual como trade-off intencional para evitar extração juridicamente incorreta.
