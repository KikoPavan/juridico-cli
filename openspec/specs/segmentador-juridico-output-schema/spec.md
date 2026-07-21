# segmentador-juridico-output-schema Specification

## Purpose

Define the requirements for the `segmentador-juridico` skill's output schema: its
resolvability by the skill registry, its contract for the Envelope de Processo
(`{metadata, pecas[]}`), and the regression coverage that protects the
reference example from drifting out of sync with the schema.

## Requirements

### Requirement: Schema de saída resolvível pelo registry
O arquivo apontado por `schema_ref` da entrada `segmentador-juridico` em
`platform/skill-runtime/skill_registry.yaml` SHALL existir em disco em
`platform/skills/segmentador-juridico/assets/output-schema.json` e SHALL
ser um JSON Schema (Draft 7) sintaticamente válido.

#### Scenario: run_segmentador_stage resolve o schema sem erro
- **WHEN** `run_segmentador_stage()` lê `schema_ref` do `skill_registry.yaml`
  para a skill `segmentador-juridico`
- **THEN** o arquivo referenciado existe e é carregado com sucesso, sem
  levantar `FileNotFoundError`

### Requirement: Contrato do Envelope de Processo
O `output-schema.json` SHALL descrever o Envelope de Processo
`{metadata, pecas[]}` conforme documentado em `SKILL.md` e
`references/variable-dictionary.md` da skill `segmentador-juridico`,
incluindo os campos obrigatórios de `metadata` (`processo_id`,
`total_pecas`, `gerado_por`, `timestamp`, `source_file`, `total_pages`,
`schema_version`) e de cada item de `pecas[]` (`piece_id`, `document_type`,
`document_type_confidence`, `pages_start`, `pages_end`, `pages_total`,
`title`, `summary`, `impacto_sentenca_proposto`, `text_excerpt`, `text`,
`anchors`, `observacoes`, `source_file`, `source_path`, `source_sha256`,
`process_group_id`, `origin_piece_index`, `relevancia_estimada`). O enum oficial
de `document_type` MUST incluir `capa_processo` e a documentação e validadores
manuais da skill MUST permanecer alinhados ao schema.

#### Scenario: exemplo de referência valida contra o schema
- **WHEN** `assets/example-output.json` é validado contra
  `assets/output-schema.json` usando `jsonschema.Draft7Validator`
- **THEN** a validação não produz nenhum erro

#### Scenario: validador da skill aceita o exemplo de referência
- **WHEN** `scripts/validate_output.py assets/example-output.json` é
  executado (usando o `--schema` padrão de `assets/output-schema.json`)
- **THEN** o processo termina com exit code `0` e imprime `[OK]`

#### Scenario: Envelope aceita capa processual

- **WHEN** uma peça materializada possui `document_type: capa_processo` e os demais campos obrigatórios válidos
- **THEN** o envelope passa pela validação canônica e pode ser persistido como `envelope_segmentacao.json`

### Requirement: Regressão de referência quebrada é detectável por teste
O projeto SHALL possuir um teste automatizado que falha caso o `schema_ref`
declarado no `skill_registry.yaml` para `segmentador-juridico` deixe de
apontar para um arquivo existente, ou caso `example-output.json` deixe de
validar contra `output-schema.json`.

#### Scenario: teste detecta schema ausente
- **WHEN** o arquivo `output-schema.json` é removido ou o `schema_ref` no
  registry é alterado para um caminho inexistente
- **THEN** a suíte de testes falha, sinalizando a quebra antes que
  `run_segmentador_stage()` seja executado em produção

### Requirement: Aliases de paginação são canonicalizados

O contrato do `segmentador-juridico` SHALL aceitar `page_number_start` e `page_number_end` como aliases opcionais de paginação. Antes de entregar uma peça ao `curador-relevancia`, a esteira MUST preencher `pages_start` a partir de `page_number_start` e `pages_end` a partir de `page_number_end` quando o respectivo campo canônico estiver ausente ou nulo. Um valor canônico não nulo MUST prevalecer sobre seu alias.

#### Scenario: Resposta do modelo com aliases é canonicalizada
- **WHEN** a resposta segmentada contém `page_number_start: 1`, `page_number_end: 15`, `pages_start: null` e `pages_end: null`
- **THEN** a peça validada entregue ao curador contém `pages_start: 1` e `pages_end: 15`

#### Scenario: Alias não sobrescreve valor canônico
- **WHEN** a resposta contém `pages_start: 2` e `page_number_start: 1`
- **THEN** a peça validada mantém `pages_start: 2`

### Requirement: Schema transporta metadados judiciais disponíveis

O schema de saída do `segmentador-juridico` SHALL permitir que cada peça e seus anchors transportem `process_number` ou `processo_id`, `event_id` ou `event`, `document_code` e `page` quando disponíveis, para consumo pelas etapas seguintes.

#### Scenario: Peça segmentada transporta identidade do documento
- **WHEN** a segmentação conhece processo `4000153-37.2026.8.26.0136/SP`, evento `1` e código `INIC1`
- **THEN** a saída validada mantém esses valores em campos aceitos pelo contrato e disponíveis ao curador

### Requirement: O LLM produz somente descritores compactos de segmentação

O `segmentador-juridico` MUST solicitar ao LLM somente decisões compactas por peça: `piece_id` ou índice lógico, `document_type`, `document_type_confidence`, limites canônicos ou aliases de página, `title` ou `text_excerpt`, `relevancia_estimada`, anchors compactos e identificadores judiciais quando disponíveis. O contrato intermediário enviado ao LLM MUST NOT exigir nem solicitar `text` ou `text_content` com a íntegra da peça.

#### Scenario: Petição extensa não é repetida na resposta do modelo
- **WHEN** `run_segmentador_stage()` envia ao LLM uma petição extensa para segmentação
- **THEN** o schema e o prompt da chamada aceitam descritores compactos e não atribuem ao modelo a cópia do texto integral no JSON

### Requirement: O texto das peças é materializado deterministicamente

Antes da persistência e validação final, a esteira MUST preencher o campo de texto integral exigido pelo envelope exclusivamente a partir do Markdown original. Para cada peça, a materialização MUST tentar, nesta ordem: intervalo por `judicial_locator` usando `pages_start/pages_end`; `page_number_start/page_number_end` como aliases; anchors com `page`; intervalo entre o início da peça atual e o início da próxima peça; e fallback por página quando houver localizadores suficientes. Quando `pages_start/pages_end` estiverem disponíveis, o recorte MUST usar uma sequência posicional contígua e conter somente segmentos iniciados por localizadores cujas páginas estejam no intervalo reconciliado. Ocorrências posteriores das mesmas páginas em outras peças MUST NOT ser incorporadas. Um `event_separator` fora do intervalo MUST NOT ser incluído; qualquer exceção explicitamente associada à fronteira MUST ser registrada em auditoria. O texto materializado MUST preservar a ordem e os marcadores originais aceitos no intervalo e MUST NOT ser inventado pelo modelo.

#### Scenario: Texto integral vem do Markdown original
- **WHEN** o modelo retorna uma peça compacta delimitada pelas páginas 1 a 15
- **THEN** Python preenche `text` ou o campo canônico equivalente com o trecho correspondente do Markdown original, sem depender de conteúdo integral gerado pelo modelo

#### Scenario: Aliases são usados após limites canônicos
- **WHEN** uma peça não possui limites canônicos, contém `page_number_start: 10` e `page_number_end: 12`, e o Markdown possui localizadores correspondentes
- **THEN** a etapa materializa o intervalo das páginas 10 a 12 a partir do Markdown

#### Scenario: Terceira peça usa anchors ou limite da coleção
- **WHEN** uma segmentação de três peças não fornece um par canônico completo para `peca_003`, mas seus anchors ou os localizadores restantes determinam inequivocamente o intervalo
- **THEN** `peca_003` recebe o texto original correspondente e seus localizadores são preservados

#### Scenario: Capa limitada às páginas 1 e 2
- **WHEN** uma `capa_processo` possui intervalo reconciliado 1–2 e o documento contém outras ocorrências de páginas 1 e 2 em eventos posteriores
- **THEN** o texto da capa contém apenas a sequência de localizadores pertencente à capa e nenhum marcador de evento posterior

#### Scenario: Despacho limitado às páginas 27 e 28
- **WHEN** um despacho possui intervalo reconciliado 27–28
- **THEN** todos os localizadores materializados possuem página 27 ou 28, salvo separador explicitamente associado e auditado

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

### Requirement: Respostas incompatíveis não são promovidas a envelope

A esteira MUST verificar que qualquer resposta candidata do LLM possui a estrutura compacta esperada antes de materializá-la. Uma resposta do fallback genérico com campos de extração e sem a raiz compatível com `metadata` e `pecas`, ou sem a coleção compacta aceita, MUST NOT ser usada como saída final do segmentador.

#### Scenario: Fallback de extrator é rejeitado
- **WHEN** o cliente retorna uma estrutura com `peticao_identification`, `parties`, `fundamentos_legais` e `pedidos`, sem `metadata` e `pecas`
- **THEN** `run_segmentador_stage()` não persiste essa estrutura como `envelope_segmentacao.json` e tenta somente uma recuperação determinística permitida

### Requirement: Documento judicial inequivocamente unitário possui fallback determinístico

Quando o Markdown possuir um único grupo de `judicial_locator`, a etapa MUST poder produzir deterministicamente um envelope com uma peça contendo todo o corpo original. A peça MUST receber páginas, anchors e identificadores do grupo, e seu `document_type` MUST ser inferido apenas quando heading, `document_code` ou nome do arquivo fornecer evidência segura.

#### Scenario: Petição Inicial do evento 1 é recuperada sem JSON volumoso
- **WHEN** a resposta do LLM falha ou é incompatível e o arquivo possui somente localizadores do mesmo processo, evento e código `INIC1`, nas páginas 1 a 15
- **THEN** a etapa produz uma peça com o texto completo original, `pages_start: 1`, `pages_end: 15`, identidade judicial e anchors preservados

### Requirement: O envelope materializado valida pelo schema canônico

Depois de reconstruir texto, canonicalizar aliases e enriquecer proveniência, `run_segmentador_stage()` MUST validar o envelope final usando `platform/skills/segmentador-juridico/assets/output-schema.json` antes de gravar `envelope_segmentacao.json`, incluindo documentos compostos cuja primeira peça seja `capa_processo`.

#### Scenario: Regressão unitária gera envelope válido
- **WHEN** `Petição Inicial_evento_1.md` ou fixture mínima equivalente passa por `run_segmentador_stage()`
- **THEN** o arquivo gerado contém `metadata` e `pecas`, possui texto preenchido por Python e não produz erros com `jsonschema.Draft7Validator` e o schema canônico

#### Scenario: Processo multipiece com capa gera envelope

- **WHEN** uma fixture multipiece contém uma `capa_processo` seguida por peças processuais reais e passa por `run_segmentador_stage()`
- **THEN** `envelope_segmentacao.json` é gravado, mantém a capa como primeira peça e valida contra o schema canônico

### Requirement: Consolidação multiparte preserva o contrato canônico
Para documentos longos ou multiparte, o `segmentador-juridico` MUST consolidar descritores parciais antes da materialização final. Cada peça consolidada SHALL preservar `process_number`, `event`, `document_code`, `pages_start`, `pages_end`, `judicial_locator`, arquivo de origem e ordem original das páginas quando essas evidências estiverem disponíveis. O texto integral MUST continuar sendo materializado exclusivamente do Markdown da mesma origem.

#### Scenario: Documento multiparte preserva identidade e origem
- **WHEN** janelas parciais identificam peças de eventos e códigos documentais distintos no mesmo processo
- **THEN** cada peça final mantém sua identidade judicial, seus locators, sua origem e seu intervalo real sem misturar outra origem

#### Scenario: Marcador de página permanece válido
- **WHEN** anchors ou locators são transportados à peça consolidada
- **THEN** `page_marker` nunca é vazio, `"[]"` nem representa página ausente da origem

### Requirement: Consolidação e envelope final possuem barreiras de validação distintas
A coleção compacta consolidada MUST validar contra o contrato intermediário e contra invariantes determinísticas de cobertura, ordem, identidade e limites antes de materializar texto. Depois da materialização e do enriquecimento, o envelope final MUST validar contra `platform/skills/segmentador-juridico/assets/output-schema.json` antes de ser promovido como `envelope_segmentacao.json` ou entregue ao handoff normal. Uma falha em qualquer barreira MUST impedir a promoção do arquivo afetado sem remover envelopes válidos de outras origens.

#### Scenario: Decisão consolidada inválida não é materializada
- **WHEN** a consolidação omite um descritor obrigatório, produz intervalo inválido ou viola cobertura, ordem ou identidade
- **THEN** nenhum texto é materializado e nenhum envelope final desse arquivo é promovido, enquanto o diagnóstico permanece disponível

#### Scenario: Envelope materializado viola o schema canônico
- **WHEN** a decisão compacta é válida mas o envelope enriquecido viola o schema canônico
- **THEN** `envelope_segmentacao.json` não é promovido nem entregue ao curador

#### Scenario: Arquivo válido sobrevive a outro inválido
- **WHEN** um arquivo do lote valida e outro falha na validação consolidada
- **THEN** o envelope válido permanece materializado e o inválido fica isolado para revisão

### Requirement: Regressão real é separada da suíte automatizada
A cobertura automatizada SHALL usar fake client e fixtures locais para todos os caminhos estruturados, particionados e de falha. A regressão com o `Processo.pdf` real SHALL possuir procedimento operacional preparado, MUST NOT ser executada automaticamente em testes unitários e MUST preceder o arquivamento da mudança.

#### Scenario: Suíte não chama Gemini
- **WHEN** as suítes automatizadas do segmentador são executadas
- **THEN** todas as respostas do modelo vêm de fake client e nenhuma chamada real ao Gemini ocorre

#### Scenario: Arquivamento depende do teste operacional
- **WHEN** implementação e testes automatizados estiverem concluídos mas o `Processo.pdf` ainda não tiver sido validado operacionalmente
- **THEN** a mudança permanece não arquivada
