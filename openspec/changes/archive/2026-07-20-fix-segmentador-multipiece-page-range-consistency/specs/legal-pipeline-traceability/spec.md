## MODIFIED Requirements

### Requirement: Segmentação deriva rastreabilidade dos localizadores de origem

Quando o Markdown de entrada contiver `judicial_locator`, o `segmentador-juridico` MUST usar prioritariamente os localizadores efetivamente materializados em cada peça para preencher ou reconciliar `process_number`, `event`, `document_code`, `pages_start`, `pages_end` e `anchors`. O menor e o maior número de página da sequência contígua da peça MUST definir o intervalo real quando conflitarem com descritores do LLM. Os marcadores originais MUST permanecer no texto, e qualquer alteração dos valores propostos MUST registrar em auditoria os valores anteriores, os valores aplicados e o motivo. Metadados globais MUST NOT sobrescrever identidade específica comprovada pelos localizadores internos da peça.

#### Scenario: Grupo do evento fornece identidade e intervalo

- **WHEN** o texto materializado contém somente localizadores do evento `1`, código `INIC1`, entre as páginas 4 e 15
- **THEN** a peça contém esse evento e código, `pages_start: 4`, `pages_end: 15`, anchors correspondentes e os localizadores originais

#### Scenario: Limite proposto é reconciliado e auditado

- **WHEN** o LLM propõe um intervalo ou código diferente da sequência de localizadores inequivocamente associada à peça
- **THEN** o envelope usa a evidência dos localizadores e registra o ajuste com valores propostos e aplicados

#### Scenario: Metadado global não contamina peça

- **WHEN** o documento agregado não possui código global confiável e a peça contém localizadores com `document_code: PED HABILIT1`
- **THEN** a peça preserva `PED HABILIT1` sem receber código de outra peça nem fragmento global

