# Dicionário de Variáveis — pdf-to-md

Versão: 1.0.0  
Escopo: agnóstico de domínio

Glossário de todas as variáveis, parâmetros e constantes usados
nos scripts e na documentação da skill.

---

## Variáveis de entrada (CLI / API)

| Variável             | Tipo    | Descrição                                                      |
|----------------------|---------|----------------------------------------------------------------|
| `input_pdf_path`     | `str`   | Caminho completo do arquivo PDF de entrada                     |
| `output_md_path`     | `str`   | Caminho completo do arquivo `.md` a ser gerado                 |
| `source_filename`    | `str`   | Nome do arquivo PDF (sem caminho) — usado em logs e relatório  |
| `preserve_page_markers` | `bool` | Se `True`, insere `<!-- page N -->` antes de cada página    |
| `emit_report`        | `bool`  | Se `True`, gera `conversion_report.md` no diretório de saída   |
| `verbose`            | `bool`  | Se `True`, exibe log detalhado por página no stderr            |
| `engine`             | `str`   | Motor de extração: `"auto"`, `"pdfminer"` ou `"pymupdf"`       |

---

## Constantes internas do conversor

| Constante              | Valor padrão                                    | Descrição                                      |
|------------------------|-------------------------------------------------|------------------------------------------------|
| `DEFAULT_ENGINE`       | `"auto"`                                        | Motor padrão de extração                       |
| `PAGE_MARKER_TPL`      | `"<!-- page {n} -->"`                           | Template de marcador de página                 |
| `EMPTY_PAGE_MARKER`    | `"<!-- page {n}: empty -->"`                    | Marcador para página em branco                 |
| `FAILED_PAGE_MARKER`   | `"<!-- page {n}: extraction_failed -->"`        | Marcador para falha de extração                |
| `SCANNED_PAGE_MARKER`  | `"<!-- page {n}: scanned_no_ocr -->"`           | Marcador para página escaneada sem OCR         |
| `OUTPUT_ENCODING`      | `"utf-8"`                                       | Encoding do arquivo de saída                   |
| `REPLACEMENT_CHAR`     | `"\uFFFD"`                                      | Substituto para caracteres não mapeáveis       |

---

## Variáveis do `conversion_report.md`

| Campo                   | Tipo    | Descrição                                                   |
|-------------------------|---------|-------------------------------------------------------------|
| `source_filename`       | `str`   | Nome do arquivo PDF processado                              |
| `total_pages`           | `int`   | Total de páginas no PDF                                     |
| `pages_ok`              | `int`   | Páginas extraídas com sucesso                               |
| `pages_failed`          | `list`  | Índices das páginas com falha de extração                   |
| `pages_empty`           | `list`  | Índices das páginas em branco                               |
| `pages_scanned`         | `list`  | Índices das páginas identificadas como imagem sem OCR       |
| `engine_used`           | `str`   | Motor que realizou a extração efetiva                       |
| `conversion_status`     | `str`   | `"success"`, `"partial"` ou `"failed"`                      |
| `timestamp`             | `str`   | Data/hora ISO 8601 da conversão                             |
| `warnings`              | `list`  | Avisos emitidos durante o processamento                     |
| `exit_code`             | `int`   | Código de saída do processo                                 |

---

## Exit codes

| Código | Constante            | Significado                              |
|--------|----------------------|------------------------------------------|
| `0`    | `EXIT_OK`            | Conversão concluída com sucesso          |
| `1`    | `EXIT_INPUT_ERROR`   | Arquivo PDF não encontrado ou inválido   |
| `2`    | `EXIT_EXTRACT_ERROR` | Falha total na extração do conteúdo      |
| `3`    | `EXIT_WRITE_ERROR`   | Erro ao escrever o arquivo de saída      |

---

## Caminhos operacionais padrão

| Variável de path   | Valor padrão                                                  |
|--------------------|---------------------------------------------------------------|
| `DIR_INPUT`        | `~/devops/juridico-cli/var/input/pdf-to-md/`                  |
| `DIR_OUTPUT`       | `~/devops/juridico-cli/var/output/pdf-to-md/`                 |
| `DIR_ARTIFACTS`    | `~/devops/juridico-cli/var/artifacts/skills/`                 |
| `SKILL_ZIP`        | `~/devops/juridico-cli/var/artifacts/skills/pdf-to-md.zip`    |
