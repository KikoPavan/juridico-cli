## ADDED Requirements

### Requirement: Paginação global é consistente com peças e localizadores

O `metadata.total_pages` final MUST ser o maior valor confiável entre a paginação informada pelo Markdown/frontmatter, a maior página numérica encontrada em todos os `judicial_locator` da origem e o maior `pages_end` das peças materializadas. O valor MUST NOT ser menor que qualquer `pages_end` persistido.

#### Scenario: Peça alcança página posterior ao total inicialmente calculado

- **WHEN** localizadores ou peças materializadas alcançam a página 35 e uma estimativa anterior informa 29
- **THEN** `metadata.total_pages` é no mínimo 35

### Requirement: Identidade global exige consenso confiável

Em documento agregado, `metadata.document_code` e `metadata.event` MUST ser preenchidos somente quando os localizadores substanciais do documento possuírem um único valor confiável para o respectivo campo. Havendo múltiplos valores, ausência de consenso ou token malformado, o campo global MUST ser `null` ou permanecer ausente conforme o schema. Um fragmento como `umento` MUST NOT ser promovido a `document_code` global.

#### Scenario: Processo agregado possui vários códigos documentais

- **WHEN** o Markdown contém códigos `INIC1`, `PED HABILIT1` e `DESPADEC1` em peças distintas
- **THEN** o envelope não declara um desses códigos nem um fragmento espúrio como `metadata.document_code`

## MODIFIED Requirements

### Requirement: O texto das peças é materializado deterministicamente

Antes da persistência e validação final, a esteira MUST preencher o campo de texto integral exigido pelo envelope exclusivamente a partir do Markdown original e dos limites, anchors e localizadores válidos da segmentação. Quando `pages_start/pages_end` estiverem disponíveis e houver localizadores suficientes, o recorte MUST usar uma sequência posicional contígua e MUST conter somente segmentos iniciados por localizadores cujas páginas estejam no intervalo reconciliado. Ocorrências posteriores das mesmas páginas em outras peças MUST NOT ser incorporadas. Um `event_separator` fora do intervalo MUST NOT ser incluído; qualquer exceção explicitamente associada à fronteira MUST ser registrada em auditoria. O texto materializado MUST preservar a ordem e os marcadores originais aceitos no intervalo.

#### Scenario: Capa limitada às páginas 1 e 2

- **WHEN** uma `capa_processo` possui intervalo reconciliado 1–2 e o documento contém outras ocorrências de páginas 1 e 2 em eventos posteriores
- **THEN** o texto da capa contém apenas a sequência de localizadores pertencente à capa e nenhum marcador de evento posterior

#### Scenario: Despacho limitado às páginas 27 e 28

- **WHEN** um despacho possui intervalo reconciliado 27–28
- **THEN** todos os localizadores materializados possuem página 27 ou 28, salvo separador explicitamente associado e auditado

