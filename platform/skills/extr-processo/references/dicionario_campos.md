# Dicionário de Campos — processo.schema.json

Derivado de `assets/processo.schema.json` (dossiê agregado do caso — v2).
Legenda: **Obrig.** = obrigatório; tipos via `$ref` a `defs/common.schema.json`.

> Atenção: este schema é um **consolidado** (aggregado/índice). Os demais schemas
> do collector-proc são schemas 1:1 (extração de peça única).

---

## Objeto raiz

| Campo            | Tipo    | Obrig. | Descrição                                                                    |
|------------------|---------|--------|------------------------------------------------------------------------------|
| `document_type`  | const   | **sim**| Sempre `"processo"`                                                          |
| `case_id`        | string  | *      | Identificador lógico do lote/caso                                            |
| `process_number` | string  | *      | Número do processo (quando existir); *obrigatório junto com `case_id`        |
| `sources`        | array   | **sim**| Fontes 1:1 usadas para compor o dossiê (≥1 item)                             |
| `document_index` | array   | **sim**| Índice das peças detectadas/processadas (≥1 item)                            |
| `header_summary` | object  | não    | Visão consolidada de capa/cabeçalho                                          |
| `parties`        | array   | não    | Partes consolidadas                                                          |
| `representations`| array   | não    | Representações/advogados consolidados                                        |
| `timeline`       | array   | não    | Linha do tempo consolidada (opcional)                                        |
| `notes`          | array   | não    | Notas técnicas (opcional)                                                    |
| `conflicts`      | array   | **sim**| Conflitos detectados (pode ser `[]`)                                         |
| `merge_meta`     | object  | **sim**| Metadados da consolidação; ver abaixo                                        |

> *`anyOf`: ao menos um de `case_id` ou `process_number` é obrigatório.

---

## `document_index[]` — ProcessDocument

| Campo           | Tipo   | Obrig. | Descrição                                           |
|-----------------|--------|--------|-----------------------------------------------------|
| `document_type` | string | **sim**| Tipo da peça (≠ `"processo"`)                       |
| `source_id`     | UUID   | **sim**| ID único da fonte                                   |
| `source_sha256` | string | **sim**| Hash SHA256 do arquivo original                     |
| `anchors`       | array  | **sim**| Âncoras (≥1 item) com `kind`, `page_marker`, `quote`|
| `title`         | string | não    | Título/descrição curta da peça                      |
| `md_filename`   | string | não    | Arquivo .md que originou o output 1:1               |
| `document_date` | ISO date| não   | Data explícita da peça                              |

---

## `header_summary` — HeaderSummary

| Campo              | Tipo    | Obrig. | Descrição                              |
|--------------------|---------|--------|----------------------------------------|
| `court`            | string  | não    | Tribunal                               |
| `comarca`          | string  | não    | Comarca                                |
| `vara`             | string  | não    | Vara                                   |
| `classe`           | string  | não    | Classe processual                      |
| `assunto`          | string  | não    | Assunto                                |
| `distribution_date`| ISO date| não   | Data de distribuição                   |
| `anchors`          | array   | não    | Âncoras de suporte (recomendado)       |

---

## `parties[]` — Party

| Campo         | Tipo   | Obrig. | Descrição                                                              |
|---------------|--------|--------|------------------------------------------------------------------------|
| `name`        | string | **sim**| Nome da parte                                                          |
| `role`        | enum   | **sim**| `autor` \| `reu` \| `outro` (e outros valores do enum PartyRole)       |
| `role_raw`    | string | não    | Texto literal do papel quando não couber no enum                       |
| `qualification`| string| não   | Qualificação literal (CPF/CNPJ/RG/endereço etc.)                       |
| `document_ids`| array  | não    | IDs explícitos (CPF/CNPJ/RG etc.) se constarem                         |
| `address`     | string | não    | Endereço                                                               |
| `anchors`     | array  | **sim**| Âncoras (≥1) com `kind`, `page_marker`, `quote`                        |

---

## `representations[]` — Representation

| Campo                   | Tipo   | Obrig. | Descrição                               |
|-------------------------|--------|--------|-----------------------------------------|
| `represented_party_name`| string | **sim**| Nome da parte representada              |
| `lawyers`               | array  | **sim**| Lista de advogados (≥1); ver abaixo     |
| `anchors`               | array  | **sim**| Âncoras (≥1)                            |

### `lawyers[]` — Lawyer
| Campo  | Tipo   | Obrig. | Descrição                |
|--------|--------|--------|--------------------------|
| `name` | string | **sim**| Nome do advogado         |
| `oab`  | string | não    | Número OAB literal       |

---

## `merge_meta` — MergeMeta

| Campo            | Tipo    | Obrig. | Descrição                                              |
|------------------|---------|--------|--------------------------------------------------------|
| `merge_strategy` | const   | **sim**| Sempre `"llm_merge_assisted_v1"`                       |
| `merged_at`      | datetime| **sim**| ISO 8601 com hora                                      |
| `input_count`    | integer | **sim**| Número de inputs processados (≥0)                      |
| `ignored_inputs` | array   | não    | Inputs ignorados com `reason`, `source_id`, `md_filename`|

---

## `timeline[]` — TimelineEvent

| Campo              | Tipo   | Obrig. | Descrição                                           |
|--------------------|--------|--------|-----------------------------------------------------|
| `event_type`       | enum   | **sim**| Tipo do evento (enum EventType de common.schema.json)|
| `event_type_raw`   | string | não    | Texto literal quando não couber no enum             |
| `event_date`       | ISO date| não   | Data explícita do evento                            |
| `description`      | string | **sim**| Descrição curta e literal (máx. 2000 chars)         |
| `related_documents`| array  | não    | source_id e/ou md_filename relacionados             |
| `anchors`          | array  | **sim**| Âncoras (≥1)                                        |

---

## Tipo compartilhado — Anchor

| Campo        | Tipo   | Obrig. | Descrição                                           |
|--------------|--------|--------|-----------------------------------------------------|
| `kind`       | enum   | **sim**| `folha` \| `pagina` \| `secao` \| `outro`           |
| `page_marker`| string | **sim**| Marcador literal idêntico ao do documento           |
| `quote`      | string | **sim**| Trecho literal curto que prova o fato               |
