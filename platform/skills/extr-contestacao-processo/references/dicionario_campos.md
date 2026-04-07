# Dicionário de Campos — contestacao_processo.schema.json

Derivado de `assets/contestacao_processo.schema.json` (1:1, v2).

## Tipos recorrentes

| Tipo             | Estrutura                                                               |
|------------------|-------------------------------------------------------------------------|
| AnchoredString   | `{value: string, anchors: [Anchor...]}`                                 |
| AnchoredTextItem | `{text: string, label?: string, anchors: [Anchor...]}`                  |
| Argumento        | `{text: string, label?: string, argument_key?: string, anchors: [...]}`|
| Anchor           | `{kind: folha\|pagina\|secao\|outro, page_marker: string, quote: string}`|

---

## Objeto raiz

| Campo                       | Tipo                  | Obrig.  | Descrição                                    |
|-----------------------------|-----------------------|---------|----------------------------------------------|
| `document_type`             | const                 | **sim** | Sempre `"contestacao_processo"`              |
| `process_number`            | AnchoredString        | não     | Número do processo                           |
| `parties`                   | array PartySummary    | não     | Partes identificadas                         |
| `representations`           | array Representation  | não     | Advogados/representantes                     |
| `contestacao_identification`| AnchoredString        | não     | Título literal da peça                       |
| `preliminares`              | array Argumento       | anyOf*  | Preliminares (quando existirem)              |
| `merito`                    | array Argumento       | anyOf*  | Argumentos de mérito/impugnações             |
| `provas_e_requerimentos`    | array AnchoredTextItem| não     | Provas e requerimentos                       |
| `pedidos_finais`            | array PedidoFinal     | anyOf*  | Pedidos finais formulados                    |
| `anchors`                   | array Anchor          | não     | Âncoras gerais                               |

> *anyOf: ao menos um de `preliminares`, `merito`, `pedidos_finais`.

---

## `preliminares[]` / `merito[]` — Argumento

| Campo          | Tipo   | Obrig. | Descrição                                          |
|----------------|--------|--------|----------------------------------------------------|
| `text`         | string | **sim**| Texto literal (máx. 6000 chars)                    |
| `label`        | string | não    | Rótulo curto (ex.: "I - Inépcia da inicial")       |
| `argument_key` | string | não    | Chave para dedupe/merge (não inferir)              |
| `anchors`      | array  | **sim**| Âncoras (≥1)                                       |

---

## `pedidos_finais[]` — PedidoFinal

| Campo       | Tipo   | Obrig. | Descrição                                    |
|-------------|--------|--------|----------------------------------------------|
| `text`      | string | **sim**| Texto literal do pedido final (máx. 4000)    |
| `label`     | string | não    | Rótulo curto (ex.: "a)", "Improcedência")    |
| `pedido_key`| string | não    | Chave para dedupe/merge (não inferir)        |
| `anchors`   | array  | **sim**| Âncoras (≥1)                                 |
