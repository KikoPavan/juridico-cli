# process-cover-piece-handling Specification

## Purpose

Define o tratamento administrativo seguro de capas processuais durante a curadoria e a normalização, evitando seu encaminhamento indevido a extratores jurídicos profundos.

## Requirements

### Requirement: Capa processual recebe curadoria administrativa segura

O `curador-relevancia` MUST tratar `capa_processo` como peça administrativa. Por padrão, a peça MUST receber `impacto_processual: irrelevante`, prioridade baixa e `acao_curatorial: remover`, com justificativa explícita e audit trail. Essa regra MUST prevalecer sobre fallbacks genéricos de confiança e relevância, salvo proteção explícita por impacto de sentença confirmado.

#### Scenario: Capa sem impacto confirmado é removida do fluxo profundo

- **WHEN** uma peça possui `document_type: capa_processo` e não possui impacto de sentença confirmado
- **THEN** o envelope curado registra impacto irrelevante, prioridade baixa, ação remover e justificativa auditável

#### Scenario: Proteção explícita não é ignorada

- **WHEN** uma capa possui `impacto_sentenca_confirmado: true`
- **THEN** a política de preservação já existente prevalece e impede remoção automática

### Requirement: Capa processual não é encaminhada a extrator profundo

Uma peça `capa_processo` MUST receber `encaminhamento: null` quando removida e MUST NOT ser encaminhada para qualquer skill `extr-*`. A distinção `cabecalho_processo` MUST permanecer inalterada e pode continuar usando seu roteamento existente.

#### Scenario: Curador não encaminha capa

- **WHEN** o curador processa uma `capa_processo` administrativa
- **THEN** a saída contém `encaminhamento: null` e nenhum identificador de extrator jurídico profundo

### Requirement: Normalizador tolera capa sem roteamento profundo

Se o `yaml-normalizador-juridico` receber uma peça `capa_processo`, ele MUST respeitar `acao_curatorial: remover` sem gerar artefato. Se receber a capa com outra ação por motivo excepcional, o normalizador MUST usar uma rota segura não profunda e não MUST invocar nem declarar uma skill `extr-*` para esse tipo.

#### Scenario: Capa removida não gera Markdown roteável

- **WHEN** o normalizador recebe `capa_processo` com `acao_curatorial: remover`
- **THEN** ele conclui sem erro e não gera Markdown para o dispatcher

#### Scenario: Capa excepcional segue para revisão segura

- **WHEN** o normalizador recebe `capa_processo` com uma ação diferente de remover
- **THEN** ele não quebra, marca a peça como não roteável ou para revisão manual e não seleciona uma skill `extr-*`
