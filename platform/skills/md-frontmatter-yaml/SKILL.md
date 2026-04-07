---
name: md-frontmatter-yaml
description: >
  Recebe um arquivo Markdown já limpo e adiciona frontmatter YAML genérico
  no topo com metadados documentais básicos e conservadores. Funciona para
  qualquer tipo de documento (relatório, manual, artigo, formulário,
  documento corporativo ou técnico). Use esta skill sempre que o usuário
  quiser adicionar metadados YAML a um arquivo Markdown, preparar um .md
  para indexação ou processamento posterior, ou mencionar palavras como
  "adicionar frontmatter", "metadata YAML", "frontmatter yaml", "metadados
  do documento", "terceira etapa do pipeline", "indexar markdown" — mesmo
  que não mencione "md-frontmatter-yaml" explicitamente.
profile: local_preprocessing
version: 1.0.0
---

# md-frontmatter-yaml

Terceira etapa do pipeline documental do `juridico-cli`.

Recebe Markdown limpo (tipicamente saído de `md-clean-markdown`) e insere
frontmatter YAML genérico e válido no topo do arquivo. O corpo do Markdown
é preservado integralmente.

Esta skill é **agnóstica de domínio**: funciona para relatórios, manuais,
artigos, formulários, documentos corporativos, técnicos ou administrativos.
Não interpreta profundamente o conteúdo nem classifica domínios.

---

## O que esta skill faz

- Recebe 1 arquivo Markdown limpo por execução
- Detecta metadados documentais explícitos quando presentes no texto
  (título, data, autor) usando heurísticas conservadoras
- Gera frontmatter YAML válido com campos documentais básicos
- Insere o bloco YAML no topo do arquivo (`---` ... `---`)
- Preserva integralmente o corpo do Markdown original
- Popula campos inferíveis de forma conservadora; campos desconhecidos
  ficam como `null` ou são omitidos
- Aceita sobrescrita de campos via parâmetros de linha de comando
- Opcionalmente gera um `frontmatter_report.md`

## O que esta skill NÃO faz

- Não assume que o documento é processo judicial ou qualquer outro domínio
- Não extrai metadados especializados (número de processo, comarca, vara,
  partes processuais, classe processual) — isso é responsabilidade de
  skills de extração especializadas
- Não inventa metadados ausentes
- Não reescreve o corpo do texto
- Não faz limpeza pesada do Markdown (responsabilidade de `md-clean-markdown`)
- Não reclassifica o tipo do documento além do básico
- Não usa LLM para inferência de metadados nesta versão (detecção por regex)

---

## Posição no pipeline

```
[pdf-to-md]  →  [md-clean-markdown]  →  [md-frontmatter-yaml]  →  [extração / indexação]
```

---

## Campos suportados no frontmatter

| Campo            | Inferível? | Padrão quando ausente |
|------------------|------------|-----------------------|
| `title`          | ✅ (h1)    | `null`                |
| `document_type`  | ❌         | `"document"`          |
| `source_file`    | ✅         | nome do arquivo        |
| `source_path`    | ✅         | caminho absoluto       |
| `document_date`  | ✅ (regex) | `null`                |
| `author`         | ✅ (regex) | `null`                |
| `language`       | ❌         | `"pt-BR"`             |
| `tags`           | ❌         | `[]`                  |
| `status`         | ❌         | `"raw"`               |
| `created_by_skill`| ✅        | `"md-frontmatter-yaml"`|

→ Detalhes em [`assets/frontmatter_fields.md`](assets/frontmatter_fields.md)
→ Template em [`assets/frontmatter_template.jinja2`](assets/frontmatter_template.jinja2)
→ Regras em [`references/regras_frontmatter.md`](references/regras_frontmatter.md)

---

## Contrato de entrada

| Parâmetro       | CLI flag          | Obrig. | Padrão      | Descrição                                       |
|-----------------|-------------------|--------|-------------|-------------------------------------------------|
| `input_md`      | `--input`         | ✅     | —           | Caminho do `.md` limpo de entrada               |
| `output_md`     | `--output`        | ✅     | —           | Caminho do `.md` com frontmatter de saída       |
| `title`         | `--title`         | ❌     | detectado   | Sobrescreve o título inferido                   |
| `document_type` | `--doc-type`      | ❌     | `"document"`| Tipo do documento                               |
| `author`        | `--author`        | ❌     | detectado   | Sobrescreve o autor inferido                    |
| `date`          | `--date`          | ❌     | detectado   | Sobrescreve a data inferida (ISO 8601)           |
| `language`      | `--language`      | ❌     | `"pt-BR"`   | Idioma do documento                             |
| `tags`          | `--tags`          | ❌     | `[]`        | Tags separadas por vírgula                      |
| `status`        | `--status`        | ❌     | `"raw"`     | Status do documento                             |
| `verbose`       | `--verbose`       | ❌     | `false`     | Exibir log no stderr                            |
| `report`        | `--report`        | ❌     | `false`     | Gerar `frontmatter_report.md` junto ao output   |

→ Especificação completa em [`assets/output_contract.md`](assets/output_contract.md)

## Contrato de saída

**Saída principal:** `<output_md>` — `.md` com bloco YAML no topo  
**Saída auxiliar (se `--report`):** `frontmatter_report.md` no mesmo diretório

---

## Fluxo de execução

```
.md limpo de entrada
       │
       ▼
[apply_frontmatter.py]
       │
       ├── lê o arquivo de entrada
       ├── detecta título (primeiro H1)
       ├── detecta data (regex de padrões comuns)
       ├── detecta autor (regex de padrões comuns)
       ├── monta dicionário de metadados
       ├── renderiza frontmatter YAML
       └── escreve: YAML + corpo original
                │
                ├── (opcional) escreve frontmatter_report.md
                └── [validate_output.py]
```

---

## Uso rápido

```bash
# Aplicação básica
python scripts/apply_frontmatter.py \
  --input  ~/devops/juridico-cli/var/input/md-frontmatter-yaml/documento.md \
  --output ~/devops/juridico-cli/var/output/md-frontmatter-yaml/documento_final.md

# Com campos explícitos
python scripts/apply_frontmatter.py \
  --input     ~/devops/juridico-cli/var/input/md-frontmatter-yaml/documento.md \
  --output    ~/devops/juridico-cli/var/output/md-frontmatter-yaml/documento_final.md \
  --title     "Relatório Anual de Operações" \
  --doc-type  "report" \
  --author    "Departamento de Operações" \
  --date      "2024-03-31" \
  --tags      "operações,relatório,2024" \
  --report --verbose

# Exemplo pré-configurado
bash scripts/run_example.sh
```

---

## Referências internas

- [`assets/frontmatter_template.jinja2`](assets/frontmatter_template.jinja2)
- [`assets/frontmatter_fields.md`](assets/frontmatter_fields.md)
- [`assets/output_contract.md`](assets/output_contract.md)
- [`references/regras_frontmatter.md`](references/regras_frontmatter.md)
- [`references/dicionario_variaveis.md`](references/dicionario_variaveis.md)
- [`references/exemplo_entrada.md`](references/exemplo_entrada.md)
- [`references/exemplo_saida.md`](references/exemplo_saida.md)
