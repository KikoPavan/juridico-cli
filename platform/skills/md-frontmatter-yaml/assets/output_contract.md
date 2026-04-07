# Contrato Operacional — md-frontmatter-yaml

Versão: 1.0.0

---

## Entrada

### Parâmetros obrigatórios

| Parâmetro   | Tipo  | CLI flag    | Descrição                                            |
|-------------|-------|-------------|------------------------------------------------------|
| `input_md`  | `str` | `--input`   | Caminho do `.md` limpo de entrada                    |
| `output_md` | `str` | `--output`  | Caminho do `.md` com frontmatter de saída            |

### Parâmetros opcionais — sobrescrita de metadados

| Parâmetro       | Tipo   | CLI flag       | Padrão        | Descrição                                    |
|-----------------|--------|----------------|---------------|----------------------------------------------|
| `title`         | `str`  | `--title`      | detectado     | Título do documento                          |
| `document_type` | `str`  | `--doc-type`   | `"document"`  | Tipo do documento                            |
| `author`        | `str`  | `--author`     | detectado     | Autor ou responsável pelo documento          |
| `date`          | `str`  | `--date`       | detectado     | Data do documento (formato ISO 8601)         |
| `language`      | `str`  | `--language`   | `"pt-BR"`     | Idioma (formato IETF BCP 47)                 |
| `tags`          | `str`  | `--tags`       | `""`          | Tags separadas por vírgula                   |
| `status`        | `str`  | `--status`     | `"raw"`       | Status do documento                          |
| `verbose`       | `bool` | `--verbose`    | `false`       | Exibir log no stderr                         |
| `report`        | `bool` | `--report`     | `false`       | Gerar `frontmatter_report.md`                |

### Restrições de entrada

- Exatamente 1 arquivo Markdown por execução
- O arquivo **não** deve já conter frontmatter YAML (o script verifica e aborta)
- Encoding esperado: UTF-8
- O arquivo deve estar limpo (saído de `md-clean-markdown` ou equivalente)

---

## Saída

### Saída principal — `<output_md>`

Arquivo Markdown com frontmatter YAML no topo:

```markdown
---
title: "Título detectado"
document_type: document
source_file: documento.md
source_path: /caminho/absoluto/documento.md
document_date: "2024-03-15"
author: "Nome do Autor"
language: pt-BR
tags:
  - tag1
  - tag2
status: raw
created_by_skill: md-frontmatter-yaml
---

<!-- page 1 -->
# Título detectado

Corpo do documento preservado integralmente...
```

**Garantias do arquivo gerado:**

- Frontmatter delimitado por `---` no início e `---` no fim
- YAML sintaticamente válido (verificável com `pyyaml`)
- Corpo do Markdown original preservado sem alteração
- Encoding: UTF-8
- Campo `created_by_skill` sempre presente

### Saída auxiliar — `frontmatter_report.md` (se `--report`)

```markdown
# Relatório de Frontmatter — md-frontmatter-yaml

- **Arquivo de entrada:** documento.md
- **Arquivo de saída:** documento_final.md
- **Título detectado:** "Título" (método: h1)
- **Data detectada:** "2024-03-15" (método: regex dd/mm/yyyy)
- **Autor detectado:** "Nome" (método: regex "Responsável:")
- **Campos preenchidos:** 8
- **Campos nulos:** 2 (title, document_date)
- **Data/hora:** 2025-06-10T14:22:01
- **Status:** ok
```

---

## Critérios mínimos de validade

| Critério                                              | Obrigatório |
|-------------------------------------------------------|-------------|
| Arquivo de saída criado                               | ✅          |
| Começa com `---\n`                                    | ✅          |
| Contém bloco de fechamento `---\n`                    | ✅          |
| YAML entre os delimitadores é sintaticamente válido   | ✅          |
| Campo `created_by_skill` presente                     | ✅          |
| Campo `source_file` presente e não vazio              | ✅          |
| Corpo do documento preservado após o frontmatter      | ✅          |
| Encoding UTF-8                                        | ✅          |
| Exit code 0 para execução bem-sucedida                | ✅          |

---

## Exit codes

| Código | Significado                                            |
|--------|--------------------------------------------------------|
| `0`    | Sucesso — arquivo com frontmatter gerado               |
| `1`    | Erro de entrada — arquivo não encontrado ou ilegível   |
| `2`    | Erro — arquivo já possui frontmatter YAML              |
| `3`    | Erro de processamento — falha na geração do YAML       |
| `4`    | Erro de escrita — falha ao gravar o arquivo de saída   |

---

## Localização operacional padrão

| Papel               | Caminho padrão                                                    |
|---------------------|-------------------------------------------------------------------|
| Input de teste      | `~/devops/juridico-cli/var/input/md-frontmatter-yaml/`            |
| Output de teste     | `~/devops/juridico-cli/var/output/md-frontmatter-yaml/`           |
| Artefato empacotado | `~/devops/juridico-cli/var/artifacts/skills/md-frontmatter-yaml.zip`|
