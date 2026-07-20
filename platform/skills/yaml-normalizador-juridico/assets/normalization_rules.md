# Regras de Normalização — yaml-normalizador-juridico

---

## 1. Princípio Geral

> **Não inventar. Não alterar. Preservar e estruturar.**

A skill recebe dados já processados e curados. Sua função é empacotar esses dados em um
formato padronizado — não interpolar, não inferir, não enriquecer além do contratado.

---

## 2. Política para Campos Nulos ou Ausentes

| Situação                                        | Ação obrigatória                              |
|-------------------------------------------------|-----------------------------------------------|
| Campo opcional ausente no input                 | Usar `null` no YAML (não omitir a chave)      |
| Campo opcional presente mas vazio (`""`)        | Converter para `null`                         |
| Lista opcional ausente                          | Usar `[]` (lista vazia, não `null`)           |
| Campo obrigatório ausente                       | Lançar `MissingFieldError` e abortar a peça  |
| Campo com valor desconhecido (`"N/A"`, `"?"`)   | Converter para `null` e registrar em log      |

---

## 3. Normalização de Datas (`document_date`)

### 3.1 Formatos aceitos no input

| Formato de entrada        | Saída normalizada  |
|---------------------------|-------------------|
| `DD/MM/YYYY`              | `YYYY-MM-DD`       |
| `DD de Mês de YYYY`       | `YYYY-MM-DD`       |
| `YYYY-MM-DD`              | `YYYY-MM-DD` (pass-through) |
| Ausente / vazio / nulo    | `null`             |
| Formato não reconhecido   | `null` + log       |

### 3.2 Meses em português

| Extenso      | Número |
|--------------|--------|
| janeiro      | 01     |
| fevereiro    | 02     |
| março        | 03     |
| abril        | 04     |
| maio         | 05     |
| junho        | 06     |
| julho        | 07     |
| agosto       | 08     |
| setembro     | 09     |
| outubro      | 10     |
| novembro     | 11     |
| dezembro     | 12     |

### 3.3 Validação de data

- Datas resultantes inválidas (ex: `2024-02-30`) → `null` + log de aviso.
- Datas futuras (> data de execução + 1 dia) → manter, mas adicionar tag `data_futura`.

---

## 4. Normalização de Partes (`parties_normalized`)

### 4.1 Fonte

Derivado de `parties_raw` (campo opcional do input). Se ausente → `[]`.

### 4.2 Transformações aplicadas

| Transformação              | Exemplo                                    |
|----------------------------|--------------------------------------------|
| Maiúsculas                 | `João Silva` → `JOAO SILVA`                |
| Remoção de acentos         | `JOÃO SILVA` → `JOAO SILVA`                |
| Trim de espaços            | `  JOAO SILVA  ` → `JOAO SILVA`            |
| Remoção de pontuação extra | `JOAO SILVA.` → `JOAO SILVA`              |
| Colapso de espaços duplos  | `JOAO  SILVA` → `JOAO SILVA`              |

### 4.3 Preservação do original

- A lista `parties_raw` do input **não é modificada** nem espelhada no frontmatter.
- `parties_normalized` contém apenas versões normalizadas.
- Se a normalização produzir string vazia → excluir da lista.

### 4.4 Entidades especiais

- CPF/CNPJ: **não extrair nem incluir** em `parties_normalized`.
- "et al." ou termos plurais genéricos: manter como estão, sem expansão.

---

## 5. Política de Status e Review

### 5.1 Mapeamento de `acao_curatorial`

| `acao_curatorial` | `review_status`   | `status`       |
|-------------------|-------------------|----------------|
| `manter`          | `approved`        | `ready`        |
| `comprimir`       | `approved`        | `ready`        |
| `revisar`         | `pending_review`  | `needs_review` |
| `remover`         | N/A               | N/A            |
| valor desconhecido| `pending_review`  | `needs_review` |

### 5.2 Condição `unroutable`

Se o `document_type` não constar no `routing_map.yaml`:
- `skill_key: REVISAR_MANUAL`
- `review_status: unroutable`
- `status: needs_review`
- Adicionar tag `nao_roteavel`

---

## 6. Distinção entre Tipos de Metadado

| Categoria          | Definição                                                      | Marcação no frontmatter     |
|-------------------|----------------------------------------------------------------|-----------------------------|
| **Recebido**      | Campo vindo diretamente do input, sem modificação              | Nenhuma marcação especial   |
| **Derivado**      | Campo calculado a partir de campos do input (ex: `skill_key`)  | Comentário `# derivado`     |
| **Inferido**      | Campo estimado heuristicamente (ex: normalização de nomes)     | Comentário `# inferido`     |
| **Não confirmado**| Campo presente mas não validável nesta etapa                   | Tag `nao_confirmado` em `tags` |

---

## 7. Normalização de `skill_key`

- Derivada exclusivamente do `routing_map.yaml`.
- Nunca inventada, nunca interpolada fora do mapa.
- Se múltiplos `document_type` mapearem para a mesma `skill_key`: comportamento normal.
- Se `document_type = "nao_classificado"`: sempre `REVISAR_MANUAL`.
- Toda rota ausente ou `REVISAR_MANUAL` força `review_status: unroutable` e
  `status: needs_review`, mesmo quando a ação recebida for `manter` ou `resumir`.

---

## 8. Normalização do Texto da Peça

Transformações **permitidas** no corpo textual:

| Transformação                           | Justificativa                         |
|-----------------------------------------|---------------------------------------|
| Trim de linhas em branco no início/fim  | Formatação mínima                     |
| Colapso de mais de 3 linhas em branco   | Redução de ruído visual               |
| Normalização de quebras de linha `\r\n` | Compatibilidade cross-platform        |

Transformações **proibidas**:

- Alteração de conteúdo, palavras, frases ou parágrafos.
- Remoção de seções do texto.
- Adição de texto não presente no original.
- Reformatação semântica (ex: converter para Markdown estruturado).

---

## 9. Tags Automáticas

A skill pode adicionar tags automáticas ao campo `tags` do frontmatter:

| Condição                                        | Tag adicionada       |
|-------------------------------------------------|----------------------|
| `acao_curatorial == "revisar"`                  | `requer_revisao`     |
| `document_type` não mapeado no routing_map      | `nao_roteavel`       |
| `impacto_sentenca_confirmado == true`           | `impacto_sentenca`   |
| `prioridade == "alta"`                          | `prioridade_alta`    |
| Data futura detectada em `document_date`        | `data_futura`        |
| Metadado inferido (não confirmado)              | `nao_confirmado`     |
