# Contrato Operacional — pdf-to-md

Versão: 1.0.0  
Escopo: agnóstico de domínio

---

## Entrada

### Parâmetros obrigatórios

| Parâmetro    | Tipo  | CLI flag  | Descrição                                  |
|--------------|-------|-----------|--------------------------------------------|
| `input_pdf`  | `str` | `--input` | Caminho do arquivo PDF de entrada          |
| `output_md`  | `str` | `--output`| Caminho do arquivo `.md` a ser gerado      |

### Parâmetros opcionais

| Parâmetro      | Tipo   | CLI flag       | Padrão   | Descrição                                             |
|----------------|--------|----------------|----------|-------------------------------------------------------|
| `page_markers` | `bool` | `--no-markers` | `true`   | Inserir `[[Pág. N]]` antes de cada página             |
| `verbose`      | `bool` | `--verbose`    | `false`  | Exibir log de extração página a página                |
| `report`       | `bool` | `--report`     | `false`  | Gerar `conversion_report.md` junto ao output          |
| `engine`       | `str`  | `--engine`     | `"auto"` | Motor de extração: `auto`, `pdfminer`, `pymupdf`      |

### Restrições de entrada

- Apenas 1 arquivo PDF por execução
- O arquivo PDF deve existir e ser legível
- PDFs protegidos por senha não são suportados
- Tamanho máximo recomendado: 200 MB

---

## Saída

### Saída principal — `<output_md>`

Arquivo Markdown com a estrutura abaixo:

```markdown
[[Pág. 1]]

# Título principal detectado

Parágrafo preservado literalmente conforme extraído do PDF.

- item de lista detectado
- outro item

[[Pág. 2]]

## Subtítulo detectado

Conteúdo da segunda página...

[[Pág. 3]]
```

**Garantias mínimas do arquivo gerado:**

| Garantia                                         | Status    |
|--------------------------------------------------|-----------|
| Um anchor `[[Pág. N]]` por página                | Obrigação |
| Headings `#`/`##`/`###` para títulos detectados | Melhor esforço |
| Texto preservado literalmente                    | Obrigação |
| Sem YAML frontmatter                             | Obrigação |
| Sem dados inferidos ou completados               | Obrigação |
| Encoding UTF-8                                   | Obrigação |
| Nenhuma página silenciosamente omitida           | Obrigação |

### Saída auxiliar — `conversion_report.md` (se `--report`)

Gerado no mesmo diretório de `output_md`:

```markdown
# Relatório de Conversão

- **Arquivo:** relatorio_anual.pdf
- **Total de páginas:** 18
- **Páginas extraídas com sucesso:** 17
- **Páginas com falha:** 1 (página 11)
- **Motor utilizado:** pdfminer
- **Data/hora:** 2025-06-10T09:15:42
- **Warnings:** página 11 retornou texto vazio
```

---

## Critérios mínimos de qualidade da conversão

1. O arquivo `.md` deve ser criado e não estar vazio
2. Deve conter pelo menos 1 anchor `[[Pág. N]]`
3. Não deve começar com `---` (YAML proibido)
4. Deve estar em UTF-8
5. Nenhuma página deve ser silenciosamente omitida

---

## Códigos de saída

| Código | Significado                                    |
|--------|------------------------------------------------|
| `0`    | Sucesso — arquivo `.md` gerado                 |
| `1`    | Erro de entrada — PDF não encontrado ou inválido |
| `2`    | Erro de extração — falha total na conversão    |
| `3`    | Erro de escrita — não foi possível salvar saída |

---

## Caminhos operacionais padrão

| Papel               | Caminho                                                      |
|---------------------|--------------------------------------------------------------|
| Input de teste      | `~/devops/juridico-cli/var/input/pdf-to-md/`                 |
| Output de teste     | `~/devops/juridico-cli/var/output/pdf-to-md/`                |
| Artefato empacotado | `~/devops/juridico-cli/var/artifacts/skills/pdf-to-md.zip`   |
