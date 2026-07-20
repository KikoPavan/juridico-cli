## ADDED Requirements

### Requirement: Segmentação compacta válida é persistida para auditoria

Quando o LLM retornar uma segmentação compacta estruturalmente válida, ou quando um fallback determinístico permitido produzir a mesma estrutura, `run_segmentador_stage()` MUST persistir um envelope bruto/debug antes de iniciar a materialização das peças. O artefato MUST permanecer disponível se qualquer peça falhar e MUST ser distinto de `envelope_segmentacao.json`, que continua reservado ao envelope final validado.

#### Scenario: Falha da terceira peça preserva o envelope bruto

- **WHEN** uma segmentação compacta válida contém pelo menos três peças e a materialização de `peca_003` falha
- **THEN** o artefato bruto/debug com a decisão compacta existe no diretório de saída e `envelope_segmentacao.json` não é promovido como envelope final inválido

### Requirement: Falha de materialização identifica peça e evidências disponíveis

Quando uma peça não puder ser materializada após todas as estratégias permitidas, a etapa MUST gerar um erro que informe `piece_id`, `document_type`, `pages_start`, `pages_end`, anchors e os localizadores disponíveis no documento. A etapa MUST NOT preencher o texto com conteúdo inventado, com `text_excerpt` ou com texto integral retornado pelo LLM.

#### Scenario: Erro de peça contém diagnóstico acionável

- **WHEN** nenhuma evidência do Markdown permite materializar uma peça compacta
- **THEN** o erro identifica a peça, seus limites e anchors e apresenta um inventário dos localizadores disponíveis, enquanto o artefato bruto/debug permanece salvo

## MODIFIED Requirements

### Requirement: O texto das peças é materializado deterministicamente

Antes da persistência e validação final, a esteira MUST preencher o campo de texto integral exigido pelo envelope exclusivamente a partir do Markdown original. Para cada peça, a materialização MUST tentar, nesta ordem: intervalo por `judicial_locator` usando `pages_start/pages_end`; `page_number_start/page_number_end` como aliases; anchors com `page`; intervalo entre o início da peça atual e o início da próxima peça; e fallback por página quando houver localizadores suficientes para determinar o intervalo. Quando `pages_start/pages_end` estiverem disponíveis, o recorte MUST conter todo o texto entre os localizadores inicial e final correspondentes, preservar sua ordem e seus marcadores `[[judicial_locator: ...]]`, e MUST NOT falhar apenas pela presença de página de separação ou `event_separator` no intervalo.

#### Scenario: Texto integral vem do intervalo de localizadores

- **WHEN** o modelo retorna uma peça compacta delimitada por `pages_start: 7` e `pages_end: 9` e o Markdown possui localizadores correspondentes
- **THEN** Python preenche o texto com todo o trecho do localizador inicial ao final, incluindo os marcadores e qualquer página separadora intermediária, sem depender de conteúdo integral gerado pelo modelo

#### Scenario: Aliases são usados após limites canônicos

- **WHEN** uma peça não possui limites canônicos, contém `page_number_start: 10` e `page_number_end: 12`, e o Markdown possui localizadores correspondentes
- **THEN** a etapa materializa o intervalo das páginas 10 a 12 a partir do Markdown

#### Scenario: Terceira peça usa anchors ou limite da coleção

- **WHEN** uma segmentação de três peças não fornece um par canônico completo para `peca_003`, mas seus anchors ou os localizadores restantes determinam inequivocamente o intervalo
- **THEN** `peca_003` recebe o texto original correspondente e seus localizadores são preservados

