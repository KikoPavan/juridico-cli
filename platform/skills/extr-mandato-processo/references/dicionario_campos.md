# Dicionário de Campos — mandato_processo.schema.json

Derivado de `assets/mandato_processo.schema.json` (1:1, v2).

## Tipos recorrentes

| Tipo             | Estrutura                                                               |
|------------------|-------------------------------------------------------------------------|
| AnchoredString   | `{value: string, anchors: [Anchor...]}`                                 |
| AnchoredDate     | `{value: ISO date, anchors: [Anchor...]}`                               |
| AnchoredTextItem | `{text: string (máx 6000), label?: string, anchors: [Anchor...]}`       |
| Person           | `{name, qualification?, document_ids?, anchors}`                        |
| Power            | `{text, label?, power_type?, power_type_raw?, anchors}`                 |
| Anchor           | `{kind: folha\|pagina\|secao\|outro, page_marker: string, quote: string}`|

---

## Objeto raiz

| Campo                    | Tipo                  | Obrig.  | Descrição                                    |
|--------------------------|-----------------------|---------|----------------------------------------------|
| `document_type`          | const                 | **sim** | Sempre `"mandato_processo"`                  |
| `process_number`         | AnchoredString        | não     | Número do processo                           |
| `mandante`               | Person                | anyOf*  | Quem confere poderes                         |
| `mandatario`             | Person                | anyOf*  | Quem recebe poderes                          |
| `escopo`                 | array AnchoredTextItem| anyOf*  | Cláusulas de escopo/objeto do mandato        |
| `poderes`                | array Power           | anyOf*  | Poderes conferidos                           |
| `data`                   | AnchoredDate          | não     | Data do instrumento                          |
| `local`                  | AnchoredString        | não     | Local                                        |
| `assinantes`             | array Person          | não     | Assinantes nominados                         |
| `restricoes_ou_limitacoes`| array AnchoredTextItem| não   | Restrições/limitações explícitas             |
| `anchors`                | array Anchor          | não     | Âncoras gerais                               |

> *anyOf: ao menos um de `poderes`, `escopo`, `mandante`, `mandatario`.

---

## `poderes[]` — Power

| Campo           | Tipo   | Obrig. | Descrição                                             |
|-----------------|--------|--------|-------------------------------------------------------|
| `text`          | string | **sim**| Texto literal do poder (máx. 4000 chars)              |
| `label`         | string | não    | Rótulo curto                                          |
| `power_type`    | enum   | não    | `gerais` \| `especiais` \| `outro` (somente se explícito)|
| `power_type_raw`| string | não    | Texto literal do tipo de poder                        |
| `anchors`       | array  | **sim**| Âncoras (≥1)                                          |

---

## `mandante` / `mandatario` / `assinantes[]` — Person

| Campo          | Tipo   | Obrig. | Descrição                            |
|----------------|--------|--------|--------------------------------------|
| `name`         | string | **sim**| Nome                                 |
| `qualification`| string | não    | Qualificação literal (máx. 4000)     |
| `document_ids` | array  | não    | CPF/CNPJ/RG etc.                     |
| `anchors`      | array  | **sim**| Âncoras (≥1)                         |
