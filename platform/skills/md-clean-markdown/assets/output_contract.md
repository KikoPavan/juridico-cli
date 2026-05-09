# Contrato Operacional — md-clean-markdown

Versão: 1.0.0

---

## Entrada

### Parâmetros obrigatórios

| Parâmetro  | Tipo  | CLI flag    | Descrição                                       |
|------------|-------|-------------|-------------------------------------------------|
| `input_md` | `str` | `--input`   | Caminho absoluto ou relativo do `.md` bruto     |
| `output_md`| `str` | `--output`  | Caminho do `.md` limpo a ser gerado             |

### Parâmetros opcionais

| Parâmetro         | Tipo   | CLI flag        | Padrão  | Descrição                                              |
|-------------------|--------|-----------------|---------|--------------------------------------------------------|
| `page_markers`    | `bool` | `--no-markers`  | `true`  | Preservar `[[Pág. N]]` (primário) e `<!-- page N -->` (legado) |
| `verbose`         | `bool` | `--verbose`     | `false` | Exibir log de cada operação no stderr                  |
| `report`          | `bool` | `--report`      | `false` | Gerar `cleaning_report.md` no diretório de saída       |
| `max_blank_lines` | `int`  | `--max-blank N` | `2`     | Máximo de linhas em branco consecutivas permitidas     |

### Restrições de entrada

- Exatamente 1 arquivo Markdown por execução
- Encoding esperado: UTF-8 (outros encodings tentados com fallback `replace`)
- Arquivos `.md` vazios geram aviso e saída vazia com exit code 0
- Não há limite de tamanho — o processamento é linha a linha

---

## Saída

### Saída principal — `<output_md>`

Arquivo Markdown limpo com as seguintes garantias:

- Sem trailing whitespace em nenhuma linha
- Máximo de `max_blank_lines` linhas em branco consecutivas
- Headings com espaço correto após `#`
- Bullets padronizados em `-`
- Separadores normalizados em `---`
- Blocos de código preservados integralmente
- Marcadores `[[Pág. N]]` e `<!-- page N -->` preservados (quando `page_markers=true`)
- Arquivo termina com exatamente `\n`
- Encoding: UTF-8

### Saída auxiliar — `cleaning_report.md` (se `--report`)

Gerado no mesmo diretório de `output_md`.

```markdown
# Relatório de Limpeza — md-clean-markdown

- **Arquivo de entrada:** relatorio_bruto.md
- **Arquivo de saída:** relatorio_limpo.md
- **Linhas de entrada:** 312
- **Linhas de saída:** 287
- **Linhas removidas:** 25
- **Operações aplicadas:**
  - trailing whitespace removido: 18 linhas
  - linhas em branco colapsadas: 4 ocorrências
  - bullets normalizados: 12 itens
  - separadores normalizados: 2 ocorrências
  - headings corrigidos: 3 ocorrências
- **Data/hora:** 2025-06-10T11:23:45
- **Status:** ok
```

---

## Critérios mínimos de qualidade

| Critério                                             | Obrigatório |
|------------------------------------------------------|-------------|
| Arquivo `.md` criado e não vazio (se entrada não vazia) | ✅       |
| Sem YAML frontmatter inserido                        | ✅          |
| Sem trailing whitespace em nenhuma linha             | ✅          |
| Máximo de `max_blank_lines` linhas em branco seguidas| ✅          |
| Blocos de código preservados sem alteração interna   | ✅          |
| Marcadores `[[Pág. N]]` e `<!-- page N -->` preservados | ✅ (se ativo)|
| Encoding UTF-8                                       | ✅          |
| Exit code 0 para limpeza bem-sucedida                | ✅          |

---

## Exit codes

| Código | Significado                                      |
|--------|--------------------------------------------------|
| `0`    | Sucesso — arquivo `.md` limpo gerado             |
| `1`    | Erro de entrada — arquivo não encontrado         |
| `2`    | Erro de processamento — falha inesperada         |
| `3`    | Erro de escrita — diretório de saída inválido    |

---

## Localização operacional padrão

| Papel               | Caminho padrão                                                   |
|---------------------|------------------------------------------------------------------|
| Input de teste      | `~/devops/juridico-cli/var/input/md-clean-markdown/`             |
| Output de teste     | `~/devops/juridico-cli/var/output/md-clean-markdown/`            |
| Artefato empacotado | `~/devops/juridico-cli/var/artifacts/skills/md-clean-markdown.zip`|
