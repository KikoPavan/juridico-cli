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
`process_group_id`, `origin_piece_index`, `relevancia_estimada`).

#### Scenario: exemplo de referência valida contra o schema
- **WHEN** `assets/example-output.json` é validado contra
  `assets/output-schema.json` usando `jsonschema.Draft7Validator`
- **THEN** a validação não produz nenhum erro

#### Scenario: validador da skill aceita o exemplo de referência
- **WHEN** `scripts/validate_output.py assets/example-output.json` é
  executado (usando o `--schema` padrão de `assets/output-schema.json`)
- **THEN** o processo termina com exit code `0` e imprime `[OK]`

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

Antes da persistência e validação final, a esteira MUST preencher o campo de texto integral exigido pelo envelope a partir do Markdown original e dos limites ou anchors válidos da segmentação. O texto materializado MUST preservar a ordem e os marcadores `[[judicial_locator: ...]]` contidos no intervalo correspondente.

#### Scenario: Texto integral vem do Markdown original
- **WHEN** o modelo retorna uma peça compacta delimitada pelas páginas 1 a 15
- **THEN** Python preenche `text` ou o campo canônico equivalente com o trecho correspondente do Markdown original, sem depender de conteúdo integral gerado pelo modelo

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

Depois de reconstruir texto, canonicalizar aliases e enriquecer proveniência, `run_segmentador_stage()` MUST validar o envelope final usando `platform/skills/segmentador-juridico/assets/output-schema.json` antes de gravar `envelope_segmentacao.json`.

#### Scenario: Regressão unitária gera envelope válido
- **WHEN** `Petição Inicial_evento_1.md` ou fixture mínima equivalente passa por `run_segmentador_stage()`
- **THEN** o arquivo gerado contém `metadata` e `pecas`, possui texto preenchido por Python e não produz erros com `jsonschema.Draft7Validator` e o schema canônico
