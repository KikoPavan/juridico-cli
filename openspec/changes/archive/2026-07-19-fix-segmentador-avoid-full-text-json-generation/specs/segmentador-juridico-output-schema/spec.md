## ADDED Requirements

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
