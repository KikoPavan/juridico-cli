# Campos do Frontmatter — md-frontmatter-yaml

Versão: 1.0.0

Descrição de cada campo suportado, seu significado, regra de preenchimento
e comportamento quando ausente.

---

## Campos principais

### `title`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string` ou `null`                                 |
| Inferível?      | ✅ — detectado pelo primeiro heading `# Título`    |
| Padrão ausente  | `null`                                             |
| Sobrescrita CLI | `--title "Texto do título"`                        |

**Regra:** usar o texto do primeiro heading de nível 1 encontrado no corpo
do documento. Se não houver H1, usar `null`. Nunca inventar.

---

### `document_type`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string`                                           |
| Inferível?      | ❌ — não inferido automaticamente                  |
| Padrão ausente  | `"document"`                                       |
| Sobrescrita CLI | `--doc-type "report"`                              |

**Valores sugeridos (não exclusivos):**
`document`, `report`, `manual`, `article`, `form`, `technical`, `administrative`, `corporate`

**Regra:** quando não informado via CLI, usar `"document"` como valor conservador.
Não tentar classificar o tipo automaticamente a partir do conteúdo.

---

### `source_file`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string`                                           |
| Inferível?      | ✅ — nome do arquivo de entrada                    |
| Padrão ausente  | nome do arquivo                                    |

**Regra:** sempre preencher com o nome do arquivo de entrada (sem o caminho
completo). É um campo de rastreabilidade obrigatório.

---

### `source_path`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string`                                           |
| Inferível?      | ✅ — caminho absoluto do arquivo de entrada        |
| Padrão ausente  | caminho resolvido                                  |

**Regra:** sempre preencher com o caminho absoluto do arquivo de entrada.
Permite rastrear a origem do documento no sistema de arquivos.

---

### `document_date`

| Atributo        | Valor                                                     |
|-----------------|-----------------------------------------------------------|
| Tipo            | `string` (ISO 8601: `YYYY-MM-DD`) ou `null`               |
| Inferível?      | ✅ — detectado por regex no início do corpo               |
| Padrão ausente  | `null`                                                    |
| Sobrescrita CLI | `--date "2024-03-15"`                                     |

**Padrões detectados automaticamente:**
- `DD/MM/YYYY` → convertido para `YYYY-MM-DD`
- `YYYY-MM-DD` → usado diretamente
- `DD de mês de YYYY` (ex.: `15 de março de 2024`) → convertido
- `Mês de YYYY` (ex.: `Março de 2024`) → `YYYY-MM` (parcial)

**Regra:** detectar apenas nas primeiras 20 linhas do corpo. Na dúvida, usar
`null`. Não inventar data.

---

### `author`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string` ou `null`                                 |
| Inferível?      | ✅ — detectado por padrões como "Responsável:"     |
| Padrão ausente  | `null`                                             |
| Sobrescrita CLI | `--author "Nome do Autor"`                         |

**Padrões detectados automaticamente (nas primeiras 30 linhas):**
- `Responsável: <nome>`
- `Autor: <nome>`
- `Elaborado por: <nome>`
- `Preparado por: <nome>`
- `Redator: <nome>`

**Regra:** detectar apenas padrões explícitos. Não inferir autoria
a partir de assinaturas ou rodapés. Na dúvida, usar `null`.

---

### `language`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string`                                           |
| Inferível?      | ❌                                                 |
| Padrão ausente  | `"pt-BR"`                                          |
| Sobrescrita CLI | `--language "en-US"`                               |

**Regra:** usar o padrão `pt-BR` salvo indicação contrária via CLI.
Seguir o formato IETF BCP 47 (ex.: `pt-BR`, `en-US`, `es-ES`).

---

### `tags`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `list[string]`                                     |
| Inferível?      | ❌ — não inferido automaticamente                  |
| Padrão ausente  | `[]`                                               |
| Sobrescrita CLI | `--tags "tag1,tag2,tag3"`                          |

**Regra:** aceitar lista de tags via CLI separadas por vírgula. Sem inferência
automática a partir do conteúdo. Tags são opcionais.

---

### `status`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string`                                           |
| Inferível?      | ❌                                                 |
| Padrão ausente  | `"raw"`                                            |
| Sobrescrita CLI | `--status "processed"`                             |

**Valores sugeridos:** `raw`, `clean`, `processed`, `reviewed`, `archived`

**Regra:** usar `"raw"` como valor padrão (indica documento ainda não revisado).

---

### `created_by_skill`

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| Tipo            | `string`                                           |
| Inferível?      | ✅ — sempre `"md-frontmatter-yaml"`                |
| Padrão ausente  | `"md-frontmatter-yaml"`                            |

**Regra:** sempre preencher com o nome desta skill. Campo de rastreabilidade
do pipeline. Nunca omitir.

---

## Campos fora do escopo desta skill

Os campos abaixo **não são suportados** por esta skill genérica.
Se necessários, devem ser adicionados por uma skill de extração especializada:

| Campo               | Responsabilidade                     |
|---------------------|--------------------------------------|
| `process_number`    | Skill de extração jurídica           |
| `court`             | Skill de extração jurídica           |
| `comarca`           | Skill de extração jurídica           |
| `vara`              | Skill de extração jurídica           |
| `parties`           | Skill de extração jurídica           |
| `classe_processual` | Skill de extração jurídica           |
