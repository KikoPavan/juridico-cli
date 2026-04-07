# Dicionário de Campos — peticao_processo.schema.json

Derivado de `assets/peticao_processo.schema.json` (1:1, v2).

## Tipos recorrentes

| Tipo              | Estrutura                                                              |
|-------------------|------------------------------------------------------------------------|
| AnchoredString    | `{value: string, anchors: [Anchor...]}`                                |
| AnchoredTextItem  | `{text: string, label?: string, anchors: [Anchor...]}`                 |
| Anchor            | `{kind: folha\|pagina\|secao\|outro, page_marker: string, quote: string}` |

---

## Objeto raiz

| Campo                   | Tipo                  | Obrig.  | Descrição                                              |
|-------------------------|-----------------------|---------|--------------------------------------------------------|
| `document_type`         | const                 | **sim** | Sempre `"peticao_processo"`                            |
| `process_number`        | AnchoredString        | não     | Número do processo (quando constar)                    |
| `parties`               | array PartySummary    | anyOf*  | Partes identificadas na petição                        |
| `representations`       | array Representation  | não     | Advogados/representantes                               |
| `peticao_identification`| AnchoredString        | não     | Identificação textual da peça                          |
| `valor_da_causa`        | AnchoredString        | anyOf*  | Valor da causa como texto literal                      |
| `fatos`                 | array AnchoredTextItem| anyOf*  | Fatos narrados (itens literais)                        |
| `fundamentos`           | array AnchoredTextItem| anyOf*  | Fundamentos (itens literais)                           |
| `provas_e_requerimentos`| array AnchoredTextItem| não    | Provas, requerimentos e pleitos acessórios             |
| `pedidos`               | array Pedido          | anyOf*  | Pedidos principais/expressos                           |
| `anchors`               | array Anchor          | não     | Âncoras gerais (preferir por item)                     |

> *anyOf: ao menos um de `pedidos`, `fatos`, `fundamentos`, `valor_da_causa`, `parties`.

---

## `pedidos[]` — Pedido

| Campo       | Tipo   | Obrig. | Descrição                                          |
|-------------|--------|--------|----------------------------------------------------|
| `text`      | string | **sim**| Texto literal do pedido (máx. 4000 chars)          |
| `label`     | string | não    | Rótulo curto (ex.: `"Pedido 1"`, `"a)"`)           |
| `pedido_key`| string | não    | Chave para deduplicação/merge (não inferir)        |
| `anchors`   | array  | **sim**| Âncoras (≥1)                                       |

---

## `parties[]` — PartySummary

| Campo          | Tipo   | Obrig. | Descrição                                                |
|----------------|--------|--------|----------------------------------------------------------|
| `name`         | string | **sim**| Nome da parte                                            |
| `role`         | enum   | **sim**| `autor` \| `reu` \| `outro` (e outros do enum PartyRole) |
| `role_raw`     | string | não    | Texto literal quando `role = outro`                      |
| `qualification`| string | não    | Qualificação literal (máx. 4000 chars)                   |
| `document_ids` | array  | não    | CPF/CNPJ/RG etc. quando explícitos                       |
| `anchors`      | array  | **sim**| Âncoras (≥1)                                             |
