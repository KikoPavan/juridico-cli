# Dicionário de Campos — yaml-normalizador-juridico

Dicionário completo dos campos do frontmatter YAML gerado por esta skill.
Para cada campo: definição, origem, tipo, valores válidos e política para nulos.

---

## Campos de Identificação

### `piece_id`
- **Definição:** Identificador único e imutável da peça dentro do processo.
- **Origem:** Input direto do `curador-relevancia`.
- **Tipo:** `string`
- **Exemplo:** `"peca-003-contestacao"`
- **Nulo:** Nunca. Campo obrigatório; ausência causa `MissingFieldError`.

### `document_type`
- **Definição:** Classificação tipológica do documento conforme taxonomia do `juridico-cli`.
- **Origem:** Input direto do `segmentador-juridico` via `curador-relevancia`.
- **Tipo:** `string`
- **Valores comuns:** `peticao_inicial`, `contestacao`, `sentenca`, `procuracao`, etc.
- **Nulo:** Nunca. Campo obrigatório.

### `skill_key`

`capa_processo` usa `REVISAR_MANUAL` como defesa não roteável caso alcance o normalizador
com ação diferente de `remover`; esse tipo nunca declara uma skill `extr-*`.

Qualquer `document_type` sem entrada roteável usa a mesma defesa: `skill_key: REVISAR_MANUAL`,
`review_status: unroutable` e `status: needs_review`, independentemente da ação curatorial.
- **Definição:** Chave da skill `extr-*` responsável pela extração profunda desta peça.
- **Origem:** Derivado de `document_type` via `assets/routing_map.yaml`.
- **Tipo:** `string`
- **Valores especiais:** `REVISAR_MANUAL` indica tipo não mapeado.
- **Nulo:** Nunca. Em caso de fallback, usar `REVISAR_MANUAL`.

### `title`
- **Definição:** Título descritivo da peça, se identificável.
- **Origem:** Campo opcional do input.
- **Tipo:** `string | null`
- **Nulo:** Permitido. Usar `null` se ausente ou vazio.

---

## Campos de Rastreabilidade

### `source_file`
- **Definição:** Nome do arquivo PDF ou documento de origem (sem caminho).
- **Origem:** Input direto.
- **Tipo:** `string`
- **Exemplo:** `"processo_1234567_2024.pdf"`
- **Nulo:** Nunca.

### `source_path`
- **Definição:** Caminho absoluto do arquivo de origem no sistema de arquivos.
- **Origem:** Input direto.
- **Tipo:** `string`
- **Exemplo:** `"/data/processos/2024/processo_1234567_2024.pdf"`
- **Nulo:** Nunca.

### `source_sha256`
- **Definição:** Hash SHA-256 do arquivo de origem para verificação de integridade.
- **Origem:** Input direto.
- **Tipo:** `string` (64 caracteres hexadecimais)
- **Nulo:** Nunca. A skill não recalcula — apenas preserva.

### `pages_start`
- **Definição:** Número da página inicial da peça no PDF de origem (base 1).
- **Origem:** Input direto.
- **Tipo:** `integer`
- **Nulo:** Nunca.

### `pages_end`
- **Definição:** Número da página final da peça no PDF de origem (base 1, inclusivo).
- **Origem:** Input direto.
- **Tipo:** `integer`
- **Nulo:** Nunca. Deve ser ≥ `pages_start`.

### `process_group_id`
- **Definição:** Identificador do grupo processual ao qual esta peça pertence.
  Agrupa todas as peças de um mesmo processo.
- **Origem:** Input direto.
- **Tipo:** `string`
- **Exemplo:** `"proc-2024-0042"`
- **Nulo:** Nunca.

### `origin_piece_index`
- **Definição:** Índice ordinal (base 0) da peça no documento original, conforme
  sequência atribuída pelo `segmentador-juridico`.
- **Origem:** Input direto.
- **Tipo:** `integer`
- **Nulo:** Nunca.

### `process_number`
- **Definição:** Número do processo preservado no frontmatter final.
- **Origem:** `process_number`, fallback `processo_id`, depois primeiro `judicial_locator` do texto.
- **Tipo:** `string | null`
- **Nulo:** Permitido apenas quando nenhuma fonte o fornece.

### `event`
- **Definição:** Evento processual da peça.
- **Origem:** `event`, fallback `event_id`, depois primeiro `judicial_locator` do texto.
- **Tipo:** `string | integer | null`
- **Nulo:** Permitido apenas quando nenhuma fonte o fornece.

### `document_code`
- **Definição:** Código documental do evento.
- **Origem:** Input direto, depois primeiro `judicial_locator` do texto.
- **Tipo:** `string | null`
- **Nulo:** Permitido apenas quando nenhuma fonte o fornece.

`page_number_start` e `page_number_end` são aliases aceitos para preencher
`pages_start` e `pages_end` somente quando os campos canônicos estão vazios.

---

## Campos de Decisão Curatorial

### `acao_curatorial`
- **Definição:** Decisão aplicada pelo `curador-relevancia` a esta peça.
- **Origem:** `acao_curatorial` do input.
- **Tipo:** `string`
- **Valores:** `manter`, `revisar`, `comprimir`
  (peças `remover` não geram artefato)
- **Nulo:** Nunca.

### `priority`
- **Definição:** Prioridade de processamento definida pelo curador.
- **Origem:** `prioridade` do input.
- **Tipo:** `string`
- **Valores:** `alta`, `media`, `baixa`
- **Nulo:** Nunca.

### `impacto_processual`
- **Definição:** Nível de relevância processual estimado pelo curador.
- **Origem:** Input direto.
- **Tipo:** `string`
- **Valores:** `alto`, `medio`, `baixo`, `nulo`, `indeterminado`
- **Nulo:** Nunca.

### `impacto_sentenca_confirmado`
- **Definição:** Indica se esta peça tem impacto confirmado sobre a sentença.
- **Origem:** `impacto_sentenca_confirmado` do input.
- **Tipo:** `boolean`
- **Nulo:** Nunca.

---

## Campos de Status de Processamento

### `review_status`
- **Definição:** Estado de revisão da peça no pipeline.
- **Origem:** Derivado de `acao_curatorial` + resultado do roteamento.
- **Tipo:** `string`
- **Valores:**
  - `approved`: peça aprovada para extração imediata.
  - `pending_review`: peça requer revisão humana antes de prosseguir.
  - `unroutable`: `document_type` não mapeado no `routing_map.yaml`.
- **Nulo:** Nunca.

### `status`
- **Definição:** Status operacional da peça no pipeline atual.
- **Origem:** Derivado de `acao_curatorial`.
- **Tipo:** `string`
- **Valores:**
  - `ready`: pronto para o dispatcher.
  - `needs_review`: aguarda triagem manual.
  - `skipped`: pulado (não deve aparecer em artefatos normais).
- **Nulo:** Nunca.

---

## Campos de Controle da Skill

### `language`
- **Definição:** Código de idioma principal do documento.
- **Origem:** Padrão `pt-BR`; pode ser sobrescrito pelo input.
- **Tipo:** `string` (BCP-47)
- **Nulo:** Nunca. Default: `pt-BR`.

### `created_by_skill`
- **Definição:** Identificador da skill que gerou este artefato.
- **Origem:** Constante imutável.
- **Tipo:** `string`
- **Valor fixo:** `yaml-normalizador-juridico`
- **Nulo:** Nunca.

### `normalized_at`
- **Definição:** Timestamp ISO-8601 da execução da normalização.
- **Origem:** Gerado em tempo de execução pelo script.
- **Tipo:** `string` (datetime com timezone)
- **Exemplo:** `"2024-08-15T14:32:00-03:00"`
- **Nulo:** Nunca.

---

## Campos Jurídicos Opcionais

### `document_date`
- **Definição:** Data do documento normalizada em ISO-8601.
- **Origem:** Campo opcional do input, normalizado pela skill.
- **Tipo:** `string | null`
- **Formato:** `YYYY-MM-DD`
- **Nulo:** Sim, quando não identificável ou não fornecido.

### `parties_normalized`
- **Definição:** Lista de partes processuais com nomes normalizados
  (maiúsculas, sem acento, sem pontuação extra).
- **Origem:** Derivado de `parties_raw` do input.
- **Tipo:** `array[string]`
- **Nulo:** Lista vazia `[]` quando não disponível.

### `court`
- **Definição:** Tribunal, vara ou juízo responsável.
- **Origem:** Campo opcional do input.
- **Tipo:** `string | null`
- **Exemplo:** `"3ª Vara Cível da Comarca de São Paulo"`
- **Nulo:** Sim.

### `judge`
- **Definição:** Nome do magistrado responsável.
- **Origem:** Campo opcional do input.
- **Tipo:** `string | null`
- **Nulo:** Sim.

### `tags`
- **Definição:** Lista de tags automáticas e manuais associadas à peça.
- **Origem:** Derivado automaticamente conforme `normalization_rules.md` §9.
- **Tipo:** `array[string]`
- **Nulo:** Lista vazia `[]` quando nenhuma tag aplicável.

### `notes`
- **Definição:** Notas curtas sobre a peça, geralmente a `justificativa_curta` do curador.
- **Origem:** `justificativa_curta` do input.
- **Tipo:** `string | null`
- **Nulo:** Sim.

### `audit_trail`
- **Definição:** Histórico completo de decisões das etapas anteriores do pipeline,
  acrescido da entrada desta normalização.
- **Origem:** Preservado integralmente do input; nova entrada acrescentada.
- **Tipo:** `array[audit_entry]`
- **Estrutura de cada entrada:**
  ```yaml
  - stage: <nome-da-skill>
    timestamp: <ISO-8601>
    action: <ação realizada>
    notes: <observações opcionais>
  ```
- **Nulo:** Nunca. Mínimo: 1 entrada (a desta skill).
