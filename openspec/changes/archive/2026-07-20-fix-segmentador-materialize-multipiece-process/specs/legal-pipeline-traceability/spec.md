## MODIFIED Requirements

### Requirement: Segmentação deriva rastreabilidade dos localizadores de origem

Quando o Markdown de entrada contiver `judicial_locator`, o `segmentador-juridico` MUST usar os localizadores correspondentes a cada peça para preencher valores ausentes de `process_number`, `event`, `document_code`, `pages_start`, `pages_end` e `anchors`. O menor e o maior número de página do grupo MUST definir o intervalo na ausência de valores canônicos explícitos, os marcadores originais MUST permanecer no texto materializado e localizadores de separação ou `event_separator` entre os limites MUST NOT impedir a materialização. Em documentos com múltiplas peças, a associação MUST considerar os limites e anchors da peça atual e o início da próxima peça, sem atribuir texto que não exista no Markdown de origem.

#### Scenario: Grupo do evento fornece identidade e intervalo

- **WHEN** o Markdown contém localizadores do processo `4000153-37.2026.8.26.0136/SP`, evento `1`, código `INIC1`, entre as páginas 1 e 15
- **THEN** a peça materializada contém o mesmo processo, evento e código, `pages_start: 1`, `pages_end: 15`, anchors correspondentes e os localizadores no texto

#### Scenario: Metadado explícito não é apagado por localizador parcial

- **WHEN** uma peça possui valor canônico explícito e seu `judicial_locator` omite esse atributo
- **THEN** o enriquecimento preserva o valor explícito e usa o localizador somente para campos ausentes

#### Scenario: Documento multipiece preserva localizadores da terceira peça

- **WHEN** um Markdown contém vários grupos de `judicial_locator`, uma página separadora e uma segmentação compacta com pelo menos três peças
- **THEN** a terceira peça é materializada com os localizadores pertencentes ao seu intervalo em ordem, sem a página separadora impedir o processamento
