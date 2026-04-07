# Dicionário de Campos — procuracao.schema.json (v3.1)

Derivado de `assets/procuracao.schema.json`.
Legenda: **Obrig.** = obrigatório pelo schema.

---

## Objeto raiz

| Campo                  | Tipo      | Obrig. | Descrição                                                                      |
|------------------------|-----------|--------|--------------------------------------------------------------------------------|
| `document_type`        | const     | **sim**| Sempre `"procuracao"`                                                          |
| `arquivo_origem`       | string    | **sim**| Basename do arquivo .md de origem; padrão `^[^/\\]+\.md$`; ≠ `collector-proc.md` |
| `schema_utilizado`     | string    | **sim**| Identificador do schema (ex.: `"schemas/procuracao.schema.json"`)              |
| `status`               | enum      | **sim**| `"sucesso"` \| `"falha"`                                                       |
| `tipo_evidencia`       | enum      | **sim**| `"juntada"` \| `"processo"`                                                    |
| `origem`               | enum      | **sim**| `"juntada"` \| `"processo"`                                                    |
| `tipo_documento`       | string    | **sim**| Tipo humano (ex.: `"Procuração"`); máx. 200 chars                              |
| `data_outorga`         | string    | **sim**| Data literal quando explícita; `""` quando não houver                          |
| `outorgantes`          | array     | **sim**| Nomes literais dos outorgantes (strings, ≥1 item)                              |
| `outorgados`           | array     | **sim**| Nomes literais dos outorgados/procuradores (strings, ≥1 item)                  |
| `transfere_poderes_pj` | boolean   | **sim**| `true` somente se outorgantes forem PJ (CNPJ/razão social/"pessoa jurídica")   |
| `transfere_poderes_pf` | boolean   | **sim**| `true` somente se outorgantes forem PF (CPF/RG/qualificação/"pessoa física")   |
| `descricao_poderes`    | string    | **sim**| Descrição curta derivada de `poderes_especificos`; máx. 6000 chars             |
| `poderes_especificos`  | array     | **sim**| Lista de poderes/cláusulas literais (strings, ≥1 item); máx. 6000/item         |
| `fonte`                | object    | **sim**| Origem do documento; ver abaixo                                                |
| `local`                | string    | não    | Local de assinatura quando explícito; `""` quando não houver                   |
| `restricoes_ou_limitacoes`| array  | não    | Restrições/limitações explícitas (strings)                                     |
| `assinantes`           | array     | não    | Assinantes nominados explicitamente (strings)                                  |

---

## `fonte` — Fonte da Procuração

| Campo             | Tipo   | Obrig. | Descrição                                             |
|-------------------|--------|--------|-------------------------------------------------------|
| `arquivo_md`      | string | **sim**| Basename do .md de origem; padrão `^[^/\\]+\.md$`    |
| `fls`             | string | **sim**| Folha/página quando explícito; `""` quando não houver |
| `rotulo_documento`| string | **sim**| Rótulo/título literal quando explícito; `""` senão    |

> Nota: `arquivo_md` e `arquivo_origem` devem ser idênticos e nunca apontar para
> `collector-proc.md` ou paths de prompts.
