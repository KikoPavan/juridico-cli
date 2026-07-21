## ADDED Requirements

### Requirement: Decision Block Strategy Produces Only Canonical Decision Properties
Quando a Extração por Blocos for acionada para `bundle_id="extr-decisao-processo"`, o sistema SHALL usar uma estratégia própria cujos blocos e consolidação produzam exclusivamente propriedades presentes em `platform/skills/extr-decisao-processo/assets/decisao_processo.schema.json`.

#### Scenario: Decision result contains no fields from other skills
- **WHEN** uma decisão é extraída em modo de blocos
- **THEN** o resultado não contém propriedades exclusivas de petição ou contestação, incluindo `peticao_identification`, `contestacao_identification`, `parties`, `representations`, `pedidos`, `pedidos_finais`, `preliminares` ou `merito`

#### Scenario: Non-modeled evidence remains inside allowed literal fields
- **WHEN** partes, prazos, obrigações ou referências documentais aparecem no texto da decisão
- **THEN** a estratégia preserva a evidência somente como trecho literal ancorado em `relatorio`, `fundamentacao`, `dispositivo` ou `determinacoes`, conforme sua função no documento, e não cria propriedades raiz adicionais

### Requirement: Decision Blocks Are Derived From Decision Schema And Skill Instructions
A estratégia SHALL dividir a extração em blocos coerentes de identificação (`process_number`, `decision_type`, `decision_date`, `decisor`, `anchors`), relatório (`relatorio`), fundamentação (`fundamentacao`), conclusão decisória (`dispositivo`, `outcome`) e cumprimento (`determinacoes`), derivados do schema e de `platform/skills/extr-decisao-processo/SKILL.md`.

#### Scenario: Conclusion block requests only decision conclusion fields
- **WHEN** o bloco de conclusão decisória é processado
- **THEN** seu schema e prompt solicitam somente `document_type`, `dispositivo` e `outcome`, com texto literal e anchors próprios

#### Scenario: Compliance block preserves explicit operational commands
- **WHEN** a decisão contém intimação, prazo, obrigação, expedição, perícia ou remessa explícita
- **THEN** o bloco de cumprimento pode preservá-la literalmente em `determinacoes` com anchor, sem inferir comando ausente

### Requirement: Decision Strategy Accepts Only Canonically Routed Input Types
A estratégia SHALL ser aplicável ao bundle resolvido a partir dos tipos ativos `decisao`, `decisao_interlocutoria`, `sentenca` e `despacho` do `routing_map.yaml`, sem ampliar esse conjunto, e SHALL produzir `document_type="decisao_processo"` conforme o schema de saída.

#### Scenario: Every canonical decision route reaches the same bundle strategy
- **WHEN** o pipeline roteia qualquer um de `decisao`, `decisao_interlocutoria`, `sentenca` ou `despacho`
- **THEN** o bundle resultante é `extr-decisao-processo` e o modo em blocos resolve a estratégia de decisão

#### Scenario: Unconfirmed type is not added by the strategy
- **WHEN** um tipo documental não consta no mapa canônico como destino de `extr-decisao-processo`
- **THEN** a estratégia não o registra, não altera o roteamento e não o assume como suportado

### Requirement: Every Applicable Decision Block Is Validated Before Consolidation
Cada resposta de bloco SHALL ser validada contra um schema parcial composto somente pelas propriedades e restrições aplicáveis ao bloco antes do merge; falha de parsing ou validação SHALL acionar o fallback local daquele bloco e ser registrada em log.

#### Scenario: Invalid block response does not enter consolidation
- **WHEN** o fake client retorna para um bloco uma propriedade proibida, tipo inválido ou anchor incompatível
- **THEN** essa resposta não é mesclada, o bloco é registrado como fallback e somente uma saída local compatível pode participar da consolidação

### Requirement: Deterministic Decision Fallback Never Invents Judicial Content
Quando um bloco falhar, o fallback local SHALL usar somente evidência literal compatível com decisão e SHALL omitir o campo ou usar lista vazia quando permitido; ele MUST NOT inventar fundamentos, dispositivo, determinações, prazos, obrigações ou referências.

#### Scenario: Missing explicit section produces no invented content
- **WHEN** o bloco de fundamentação, dispositivo ou determinações falha e o Markdown não contém evidência literal reconhecível para a seção
- **THEN** o fallback retorna lista vazia ou omite o campo conforme permitido, sem texto fixo, resumo ou inferência

#### Scenario: Fallback use is observable by block
- **WHEN** qualquer bloco usa fallback
- **THEN** o log identifica claramente o nome do bloco e a causa da degradação

### Requirement: Decision Anchors Preserve Real Locators Without Fabricated Page Markers
A estratégia SHALL preservar anchors e marcadores reais derivados do documento e MUST NOT consolidar `page_marker` vazio, `"[]"`, número fictício ou locator inválido.

#### Scenario: Judicial locator supplies the page marker
- **WHEN** um trecho evidenciado está sob `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="32", document_code="DESPADEC1", page="2"]]`
- **THEN** seu anchor preserva uma referência real a esse locator/página e não a substitui por um default numérico inventado

#### Scenario: No reliable marker means no fabricated anchor
- **WHEN** um fallback encontra texto mas não consegue associá-lo a marcador real exigido pelo schema do item
- **THEN** ele omite o item ou campo em vez de criar `page_marker="1"`, `page_marker="[]"` ou locator sintético

### Requirement: Complete Decision Result Is Validated Before Persistence
O JSON consolidado SHALL ser filtrado pela allowlist de `schema.properties` e validado contra o schema canônico completo de `extr-decisao-processo` antes de retornar; um resultado inválido MUST NOT ser retornado como sucesso nem persistido.

#### Scenario: Valid fake-client result passes official validator
- **WHEN** o fake client fornece blocos válidos que são consolidados pela estratégia
- **THEN** o resultado contém somente propriedades permitidas e é aceito por `platform/skills/extr-decisao-processo/scripts/validate_output.py`

#### Scenario: Failed block cannot permit invalid persistence
- **WHEN** uma falha de bloco e seu fallback deixam o objeto consolidado sem satisfazer o `anyOf` ou outra restrição do schema completo
- **THEN** a estratégia levanta erro antes do retorno e nenhum arquivo JSON de resultado é persistido

### Requirement: Existing Gemini Preflight And Call Shape Remain Unchanged
A implementação SHALL usar o fluxo de invocação em blocos existente sem alterar o preflight Gemini validado nem reintroduzir schemas ou parâmetros de chamada capazes de provocar `400 INVALID_ARGUMENT`.

#### Scenario: Decision support is additive after strategy dispatch
- **WHEN** a estratégia de decisão é registrada
- **THEN** o preflight, a normalização de schema e a forma das chamadas Gemini existentes permanecem inalterados fora da nova estratégia
