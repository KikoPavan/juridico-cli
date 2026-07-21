# segmentador-juridico-resilient-processing Specification — Delta

## MODIFIED Requirements

### Requirement: Peças parciais são consolidadas deterministicamente

O estágio MUST ordenar descritores parciais pela posição original e SHALL unir descritores de janelas adjacentes somente quando origem, processo, intervalo, identidade documental e continuidade sustentarem que representam a mesma peça. Uma peça que cruza janelas MUST resultar em uma única peça final. Mudanças confiáveis de evento, código, tipo ou cabeçalho MUST preservar peças adjacentes distintas.

Um descritor `separador_de_evento` SHALL ser absorvido pela peça documental real do mesmo evento quando houver evidência suficiente de que ambos descrevem a mesma página ou overlap entre janelas. A absorção SHALL seguir a precedência documental: `separador_de_evento`/`nao_classificado` < tipo genérico < tipo específico. O tipo final, `document_code` e intervalo SHALL ser os da peça mais específica.

Após reconciliar overlaps e preencher lacunas, o estágio SHALL coalescer fragmentos contíguos com a mesma identidade judicial forte em uma única peça. Fragmentos `nao_classificado` SHALL ser absorvidos pela peça específica adjacente à esquerda quando houver compatibilidade de locators.

Depois das respostas do LLM, o estágio MUST canonicalizar separadores estruturais usando o Markdown original e os `judicial_locator`, independentemente de o LLM representar a página como `separador_de_evento`, `nao_classificado` ou parte da peça seguinte. A absorção na peça específica seguinte MUST exigir mesmo processo e evento, código documental seguinte válido, nenhum código específico conflitante no separador e nenhuma peça específica concorrente no mesmo limite. Locator sem `process_number` confiável MUST bloquear essa absorção.

Quando um grupo contíguo completo de locators possuir processo, evento e código documental fortes, seus limites SHALL prevalecer sobre fronteiras parciais propostas pelo LLM. Fragmentos de mesma identidade SHALL ser consolidados, e fragmentos `nao_classificado` totalmente contidos no grupo SHALL ser absorvidos. A regra MUST NOT alcançar intervalos sem identidade forte.

#### Scenario: Peça atravessa duas janelas
- **WHEN** duas janelas sobrepostas descrevem a mesma peça contínua na fronteira
- **THEN** a consolidação produz uma única peça com o intervalo integral da origem

#### Scenario: Peças adjacentes distintas não são unidas
- **WHEN** descritores contíguos possuem mudança confiável de evento, código ou cabeçalho documental
- **THEN** a consolidação mantém duas peças distintas

#### Scenario: Intervalos finais são consistentes
- **WHEN** a consolidação termina com evidência suficiente para todas as peças
- **THEN** os intervalos seguem a ordem da origem sem lacunas ou sobreposições indevidas fora da sobreposição descartada

#### Scenario: Separador de evento e peça real no mesmo evento são absorvidos
- **WHEN** um `separador_de_evento` e uma peça documental específica (ex: `despacho_decisao`) ocupam a mesma página de overlap entre janelas, com mesmo `event`, mesmo `process_number`, e o separador não possui `document_code` conflitante
- **THEN** a consolidação produz uma única peça com tipo e `document_code` da peça específica

#### Scenario: Separador de evento sem peça correspondente não é absorvido
- **WHEN** um `separador_de_evento` está presente sem peça real correspondente no mesmo evento e overlap
- **THEN** o separador permanece representado de forma controlada ou é encaminhado para revisão conforme o contrato existente

#### Scenario: Dois tipos específicos incompatíveis continuam rejeitados
- **WHEN** dois descritores de tipos específicos diferentes (ex: `contestacao` e `despacho_decisao`) se sobrepõem sem evidência de continuidade
- **THEN** a consolidação rejeita com `ValueError` (sobreposição indevida)

#### Scenario: Separadores de eventos diferentes não são unidos
- **WHEN** um `separador_de_evento` do evento 13 se sobrepõe a uma peça do evento 14 na mesma página
- **THEN** a consolidação rejeita com `ValueError` (sobreposição indevida)

#### Scenario: Overlap entre janelas não duplica página
- **WHEN** a página de overlap entre duas janelas contém separador + peça real do mesmo evento
- **THEN** a página aparece uma única vez no intervalo final da peça consolidada

#### Scenario: Fragmentos contíguos com mesma identidade forte são coalescidos
- **WHEN** dois fragmentos adjacentes possuem mesmo event, mesmo document_code e mesmo process_number
- **THEN** a consolidação produz uma única peça com intervalo unificado

#### Scenario: `nao_classificado` adjacente é absorvido pela peça específica
- **WHEN** um fragmento `nao_classificado` está `à` direita de uma peça específica com identidade forte, é contíguo, e seus locators são compatíveis
- **THEN** o `nao_classificado` é absorvido e o intervalo da peça específica é estendido

#### Scenario: `nao_classificado` não é absorvido quando identidade difere
- **WHEN** o `nao_classificado` adjacente possui locator com evento ou código diferente da peça à esquerda
- **THEN** o `nao_classificado` permanece como peça independente

#### Scenario: Três representações da página 3 convergem
- **WHEN** a página 3 possui estrutura original de separador do evento 1 e o LLM a devolve como `separador_de_evento`, `nao_classificado` ou incluída diretamente em `peticao_inicial`
- **THEN** as três respostas produzem o mesmo envelope canônico de 7 peças, com `peticao_inicial`/`INIC1` cobrindo 3-18

#### Scenario: Páginas órfãs sem processo não são absorvidas
- **WHEN** as páginas 19-21 não possuem `process_number` confiável nos locators
- **THEN** elas permanecem como uma peça `nao_classificado` autônoma

#### Scenario: Evento ou código conflitante bloqueia separador
- **WHEN** o separador possui evento diferente da peça seguinte ou `document_code` específico conflitante
- **THEN** ele não é absorvido

#### Scenario: Canonicalização operacional é reproduzível
- **WHEN** `Processo.pdf` é segmentado três vezes em diretórios isolados
- **THEN** todas as execuções produzem as mesmas 7 peças, identidades, intervalos, cobertura 1-35 e hash canônico

## ADDED Requirements

### Requirement: Precedência documental explícita

A consolidação SHALL aplicar a seguinte precedência de tipos documentais para resolver conflitos de identidade entre descritores parciais:

```
separador_de_evento / nao_classificado
< tipo documental genérico (ex: peticao, despacho, decisao)
< tipo documental específico (ex: pedido_de_habilitacao, despacho_decisao)
```

Esta precedência SHALL ser usada somente quando origem, evento e intervalo forem compatíveis. Dois tipos específicos incompatíveis MUST NOT ser unidos automaticamente apenas porque um está acima do outro na precedência.

#### Scenario: Precedência resolve separador + tipo específico
- **WHEN** `separador_de_evento` e `despacho_decisao` no mesmo evento e overlap
- **THEN** o tipo final é `despacho_decisao` (mais específico)

#### Scenario: Precedência não une tipos específicos incompatíveis
- **WHEN** `contestacao` (tipo específico) e `despacho_decisao` (tipo específico) no mesmo evento
- **THEN** a consolidação rejeita a sobreposição como indevida

### Requirement: Normalização determinística do tipo documental

O tipo documental final SHALL ser normalizado para um valor estável aceito pelo schema do output e pelo routing_map. Tipos da família de decisão (`despacho`, `despacho_decisao`, `decisao`, `decisao_interlocutoria`) SHALL ser consolidados para o valor mais específico e estável.

#### Scenario: `despacho_decisao` e `despacho` do mesmo evento produzem tipo estável
- **WHEN** dois fragmentos com tipos `despacho_decisao` e `despacho`, mesmo event e mesmo document_code, são coalescidos
- **THEN** o tipo final é aceito pelo schema do output
