# Dicionário de Variáveis — md-clean-markdown

Versão: 1.0.0

Glossário de todas as variáveis, parâmetros e constantes usados nos
scripts e na documentação da skill. Agnóstico de domínio.

---

## Variáveis de entrada (CLI / API)

| Variável           | Tipo    | Descrição                                                          |
|--------------------|---------|--------------------------------------------------------------------|
| `input_md_path`    | `str`   | Caminho absoluto ou relativo do arquivo `.md` bruto de entrada     |
| `output_md_path`   | `str`   | Caminho do arquivo `.md` limpo a ser gerado                        |
| `source_filename`  | `str`   | Nome do arquivo de entrada (sem caminho), para logs e relatório    |
| `preserve_page_markers` | `bool` | Se `True`, mantém `<!-- page N -->` e variantes intocados   |
| `emit_report`      | `bool`  | Se `True`, gera `cleaning_report.md` no diretório de saída         |
| `verbose`          | `bool`  | Se `True`, exibe log de operações no stderr                        |
| `max_blank_lines`  | `int`   | Máximo de linhas em branco consecutivas permitidas (padrão: `2`)   |

---

## Variáveis de estado interno (durante processamento)

| Variável              | Tipo    | Descrição                                                       |
|-----------------------|---------|-----------------------------------------------------------------|
| `inside_code_block`   | `bool`  | Flag que indica se o parser está dentro de um bloco de código  |
| `blank_line_count`    | `int`   | Contador de linhas em branco consecutivas na posição atual      |
| `code_block_fence`    | `str`   | Delimitador ativo do bloco de código (`\`\`\`` ou `~~~`)       |
| `lines_in`            | `int`   | Total de linhas no arquivo de entrada                           |
| `lines_out`           | `int`   | Total de linhas no arquivo de saída                             |

---

## Variáveis do relatório (`cleaning_report.md`)

| Campo                    | Tipo    | Descrição                                                    |
|--------------------------|---------|--------------------------------------------------------------|
| `source_filename`        | `str`   | Nome do arquivo `.md` de entrada                             |
| `output_filename`        | `str`   | Nome do arquivo `.md` de saída                               |
| `lines_in`               | `int`   | Total de linhas no arquivo de entrada                        |
| `lines_out`              | `int`   | Total de linhas no arquivo de saída                          |
| `lines_removed`          | `int`   | Total de linhas removidas (diferença bruta)                  |
| `trailing_ws_fixed`      | `int`   | Linhas com trailing whitespace corrigido                     |
| `blank_collapsed`        | `int`   | Ocorrências de colapso de linhas em branco                   |
| `bullets_normalized`     | `int`   | Itens de lista com bullet normalizado                        |
| `separators_normalized`  | `int`   | Separadores horizontais normalizados                         |
| `headings_fixed`         | `int`   | Headings com espaço corrigido                                |
| `cleaning_status`        | `str`   | Status geral: `"ok"`, `"warnings"` ou `"error"`              |
| `timestamp`              | `str`   | Data/hora ISO 8601 da execução                               |
| `exit_code`              | `int`   | Código de saída do processo                                  |

---

## Exit codes

| Código | Constante            | Significado                                    |
|--------|----------------------|------------------------------------------------|
| `0`    | `EXIT_OK`            | Limpeza concluída com sucesso                  |
| `1`    | `EXIT_INPUT_ERROR`   | Arquivo de entrada não encontrado ou ilegível  |
| `2`    | `EXIT_PROCESS_ERROR` | Erro inesperado durante o processamento        |
| `3`    | `EXIT_WRITE_ERROR`   | Falha ao escrever o arquivo de saída           |

---

## Caminhos operacionais padrão

| Variável        | Valor padrão                                                        |
|-----------------|---------------------------------------------------------------------|
| `DIR_INPUT`     | `~/devops/juridico-cli/var/input/md-clean-markdown/`                |
| `DIR_OUTPUT`    | `~/devops/juridico-cli/var/output/md-clean-markdown/`               |
| `DIR_ARTIFACTS` | `~/devops/juridico-cli/var/artifacts/skills/`                       |
| `SKILL_ZIP`     | `~/devops/juridico-cli/var/artifacts/skills/md-clean-markdown.zip`  |
