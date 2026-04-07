# Dicionário de Campos — decisao_processo.schema.json

Derivado de `assets/decisao_processo.schema.json` (1:1, v2).

## Tipos recorrentes

| Tipo              | Estrutura                                                                    |
|-------------------|------------------------------------------------------------------------------|
| AnchoredString    | `{value: string, anchors: [Anchor...]}`                                      |
| AnchoredDate      | `{value: ISO date, anchors: [Anchor...]}`                                    |
| AnchoredTextItem  | `{text: string (máx 7000), label?: string, anchors: [Anchor...]}`            |
| DispositivoItem   | `{text: string (máx 6000), label?: string, anchors: [Anchor...]}`            |
| Anchor            | `{kind: folha\|pagina\|secao\|outro, page_marker: string, quote: string}`    |

---

## Objeto raiz

| Campo           | Tipo                  | Obrig.  | Descrição                                                             |
|-----------------|-----------------------|---------|-----------------------------------------------------------------------|
| `document_type` | const                 | **sim** | Sempre `"decisao_processo"`                                           |
| `process_number`| AnchoredString        | não     | Número do processo                                                    |
| `decision_type` | AnchoredDecisionType  | anyOf*  | Tipo: `decisao`\|`sentenca`\|`acordao`\|`despacho`\|`outro` + value_raw|
| `decision_date` | AnchoredDate          | anyOf*  | Data da decisão                                                       |
| `decisor`       | Decisor               | anyOf*  | Identificação do decisor/órgão; ver abaixo                            |
| `relatorio`     | array AnchoredTextItem| não     | Trechos do relatório                                                  |
| `fundamentacao` | array AnchoredTextItem| anyOf*  | Trechos da fundamentação                                              |
| `dispositivo`   | array DispositivoItem | anyOf*  | Dispositivo (foco de ancoragem)                                       |
| `outcome`       | Outcome               | anyOf*  | Resultado quando explícito; ver abaixo                                |
| `determinacoes` | array AnchoredTextItem| não     | Determinações específicas (intimações, prazos etc.)                   |
| `anchors`       | array Anchor          | não     | Âncoras gerais (preferir por item)                                    |

> *anyOf: ao menos um de `dispositivo`, `outcome`, `decision_date`, `decisor`, `fundamentacao`.

---

## `decisor` — Decisor

| Campo           | Tipo   | Obrig.  | Descrição                                    |
|-----------------|--------|---------|----------------------------------------------|
| `name`          | string | anyOf*  | Nome do juiz/desembargador/ministro          |
| `role`          | string | não     | Cargo literal (ex.: "Juiz de Direito")       |
| `orgao_julgador`| string | anyOf*  | Órgão julgador                               |
| `tribunal`      | string | anyOf*  | Tribunal                                     |
| `anchors`       | array  | **sim** | Âncoras (≥1)                                 |

> *anyOf: ao menos um de `name`, `orgao_julgador`, `tribunal`.

---

## `outcome` — Outcome

| Campo      | Tipo   | Obrig. | Descrição                                                  |
|------------|--------|--------|------------------------------------------------------------|
| `value`    | enum   | **sim**| Enum DecisionOutcome de common.schema.json                 |
| `value_raw`| string | não    | Texto literal do resultado                                 |
| `anchors`  | array  | **sim**| Âncoras (≥1)                                               |
