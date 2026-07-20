# registered-extractor-routing Specification

## Purpose

Garantir que o roteamento documental use somente extratores registrados, mantenha uma política canônica compartilhada entre curador e normalizador e preserve tipos sem destino seguro para revisão manual.

## Requirements

### Requirement: Mapa referencia somente destinos válidos

Cada `skill_key` declarado nas entradas e no fallback de `routing_map.yaml` MUST corresponder a uma chave existente em `skill_registry.yaml` ou ao sentinela `REVISAR_MANUAL`.

#### Scenario: Verificação de integridade do mapa
- **WHEN** a suíte compara todas as rotas configuradas com o registro de skills
- **THEN** ela falha se encontrar qualquer destino diferente de `REVISAR_MANUAL` que não esteja registrado

### Requirement: Tipos específicos usam extratores registrados

O roteamento MUST resolver `contrato_social` para `extr-contrato-social`, `escritura_imovel` para `extr-escritura-imovel`, `escritura_hipotecaria` para `extr-escritura-hipotecaria`, `peticao_inicial` para `extr-peticao-processo`, `contestacao` para `extr-contestacao-processo`, `despacho`, `decisao_interlocutoria` e `sentenca` para `extr-decisao-processo`, `mandato` para `extr-mandato-processo`, `procuracao` para `extr-procuracao` e `cabecalho_processo` para `extr-cabecalho-processo`.

#### Scenario: Documento de subtipo específico é roteado
- **WHEN** o pipeline recebe `contrato_social`, `escritura_imovel` ou `escritura_hipotecaria`
- **THEN** curador e normalizador selecionam semanticamente o extrator específico registrado correspondente

#### Scenario: Sentença reutiliza extrator de decisão
- **WHEN** o pipeline recebe `document_type: sentenca` sem existir `extr-sentenca-processo` no registro
- **THEN** a rota selecionada é `extr-decisao-processo`

### Requirement: Curador e normalizador compartilham a política de rota

O curador MUST derivar seus encaminhamentos da política canônica de `routing_map.yaml`, ou MUST reproduzir exatamente essa política com uma verificação automática de consistência. Para destinos manuais, `encaminhamento: null` no envelope curado MUST ser tratado como semanticamente equivalente a `REVISAR_MANUAL` no normalizador.

#### Scenario: Rotas comuns permanecem consistentes
- **WHEN** um teste parametrizado consulta curador e normalizador para os mesmos tipos documentais comuns
- **THEN** os destinos `extr-*` coincidem e cada rota manual resulta em `null` no curador e `REVISAR_MANUAL` no normalizador

### Requirement: Capa não segue para extração profunda

`capa_processo` MUST permanecer removível pelo curador e, quando excepcionalmente preservada, MUST usar somente revisão manual sem encaminhamento a skill `extr-*`.

#### Scenario: Capa preservada defensivamente
- **WHEN** uma `capa_processo` não é removida antes da normalização
- **THEN** ela recebe `REVISAR_MANUAL` e não declara extrator jurídico profundo
