# Dicionário de Campos — cabecalho_processo.schema.json

Derivado de `assets/cabecalho_processo.schema.json` (1:1, v2).
Legenda: **Obrig.** = obrigatório pelo schema ou anyOf.

---

## Tipo AnchoredString
Objeto com `value` (string não-vazia) + `anchors` (array ≥1).

## Tipo AnchoredDate
Objeto com `value` (ISO date) + `anchors` (array ≥1).

## Tipo Anchor

| Campo        | Tipo   | Obrig. | Descrição                              |
|--------------|--------|--------|----------------------------------------|
| `kind`       | enum   | **sim**| `folha` \| `pagina` \| `secao` \| `outro` |
| `page_marker`| string | **sim**| Marcador literal idêntico ao documento |
| `quote`      | string | **sim**| Trecho literal curto                   |

---

## Objeto raiz

| Campo              | Tipo              | Obrig.  | Descrição                                              |
|--------------------|-------------------|---------|--------------------------------------------------------|
| `document_type`    | const             | **sim** | Sempre `"cabecalho_processo"`                          |
| `process_number`   | AnchoredString    | anyOf*  | Número do processo                                     |
| `court`            | AnchoredString    | não     | Tribunal                                               |
| `comarca`          | AnchoredString    | não     | Comarca                                                |
| `vara`             | AnchoredString    | não     | Vara                                                   |
| `classe`           | AnchoredString    | anyOf*  | Classe processual                                      |
| `assunto`          | AnchoredString    | anyOf*  | Assunto                                                |
| `distribution_date`| AnchoredDate      | não     | Data de distribuição (ISO 8601)                        |
| `parties`          | array PartySummary| anyOf*  | Partes do processo                                     |
| `representations`  | array Representation| não   | Advogados/representantes                               |
| `anchors`          | array Anchor      | não     | Âncoras gerais (preferir âncoras por campo/item)       |

> *anyOf: ao menos um de `process_number`, `parties`, `classe`, `assunto` é obrigatório.

---

## `parties[]` — PartySummary

| Campo          | Tipo   | Obrig. | Descrição                                                   |
|----------------|--------|--------|-------------------------------------------------------------|
| `name`         | string | **sim**| Nome da parte                                               |
| `role`         | enum   | **sim**| `autor` \| `reu` \| `outro` (e outros valores do enum)      |
| `role_raw`     | string | não    | Texto literal do papel quando `role = outro`                |
| `qualification`| string | não    | Qualificação literal (máx. 4000 chars)                      |
| `document_ids` | array  | não    | CPF/CNPJ/RG etc. quando explícitos                          |
| `anchors`      | array  | **sim**| Âncoras (≥1)                                                |

---

## `representations[]` — Representation

| Campo                   | Tipo   | Obrig. | Descrição                           |
|-------------------------|--------|--------|-------------------------------------|
| `represented_party_name`| string | **sim**| Nome da parte representada          |
| `lawyers`               | array  | **sim**| Lista de advogados (≥1); ver abaixo |
| `anchors`               | array  | **sim**| Âncoras (≥1)                        |

### `lawyers[]` — Lawyer

| Campo  | Tipo   | Obrig. | Descrição          |
|--------|--------|--------|--------------------|
| `name` | string | **sim**| Nome do advogado   |
| `oab`  | string | não    | Número OAB literal |
