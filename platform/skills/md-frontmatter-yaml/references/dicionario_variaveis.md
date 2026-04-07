# Dicionário de Variáveis — md-frontmatter-yaml

Versão: 1.0.0

Glossário de todas as variáveis, parâmetros e constantes usados nos
scripts e na documentação da skill. Agnóstico de domínio.

---

## Variáveis de entrada (CLI / API)

| Variável        | Tipo    | Descrição                                                          |
|-----------------|---------|--------------------------------------------------------------------|
| `input_md_path` | `str`   | Caminho absoluto ou relativo do `.md` limpo de entrada             |
| `output_md_path`| `str`   | Caminho do `.md` com frontmatter de saída                          |
| `source_filename`| `str`  | Nome do arquivo de entrada (sem caminho), para logs e relatório    |
| `title`         | `str`   | Título explícito (sobrescreve detecção automática)                 |
| `document_type` | `str`   | Tipo do documento (padrão: `"document"`)                           |
| `author`        | `str`   | Autor explícito (sobrescreve detecção automática)                  |
| `date`          | `str`   | Data explícita em ISO 8601 (sobrescreve detecção automática)       |
| `language`      | `str`   | Idioma em formato IETF BCP 47 (padrão: `"pt-BR"`)                 |
| `tags`          | `str`   | Tags separadas por vírgula (CLI) → convertidas para `list[str]`   |
| `status`        | `str`   | Status do documento (padrão: `"raw"`)                             |
| `verbose`       | `bool`  | Se `True`, exibe log detalhado no stderr                          |
| `emit_report`   | `bool`  | Se `True`, gera `frontmatter_report.md` no diretório de saída     |

---

## Variáveis de estado interno (durante processamento)

| Variável          | Tipo    | Descrição                                                        |
|-------------------|---------|------------------------------------------------------------------|
| `detected_title`  | `str`   | Título inferido do primeiro H1 do corpo                          |
| `detected_date`   | `str`   | Data inferida por regex (formato ISO 8601 ou parcial)            |
| `detected_author` | `str`   | Autor inferido por padrões de texto explícitos                   |
| `detection_method_title` | `str` | Método usado: `"cli"`, `"h1"`, `"null"`                 |
| `detection_method_date`  | `str` | Método usado: `"cli"`, `"regex_dmy"`, `"regex_iso"`, `"null"` |
| `detection_method_author`| `str` | Método usado: `"cli"`, `"regex_label"`, `"null"`        |
| `body_text`       | `str`   | Conteúdo original do arquivo de entrada (corpo preservado)       |
| `frontmatter_dict`| `dict`  | Dicionário Python com todos os campos do frontmatter             |
| `yaml_block`      | `str`   | String YAML gerada (sem os delimitadores `---`)                  |

---

## Campos do relatório (`frontmatter_report.md`)

| Campo                | Tipo    | Descrição                                                    |
|----------------------|---------|--------------------------------------------------------------|
| `source_filename`    | `str`   | Nome do arquivo de entrada                                   |
| `output_filename`    | `str`   | Nome do arquivo de saída                                     |
| `detected_title`     | `str`   | Valor do título e método de detecção                         |
| `detected_date`      | `str`   | Valor da data e método de detecção                           |
| `detected_author`    | `str`   | Valor do autor e método de detecção                          |
| `fields_filled`      | `int`   | Número de campos com valor não-nulo                          |
| `fields_null`        | `int`   | Número de campos com valor `null`                            |
| `frontmatter_status` | `str`   | Status geral: `"ok"`, `"warnings"` ou `"error"`              |
| `timestamp`          | `str`   | Data/hora ISO 8601 da execução                               |
| `exit_code`          | `int`   | Código de saída do processo                                  |

---

## Exit codes

| Código | Constante             | Significado                                       |
|--------|-----------------------|---------------------------------------------------|
| `0`    | `EXIT_OK`             | Frontmatter gerado e inserido com sucesso         |
| `1`    | `EXIT_INPUT_ERROR`    | Arquivo não encontrado ou ilegível                |
| `2`    | `EXIT_ALREADY_HAS_FM` | Arquivo já possui frontmatter YAML                |
| `3`    | `EXIT_YAML_ERROR`     | Falha na geração ou validação do YAML             |
| `4`    | `EXIT_WRITE_ERROR`    | Falha ao gravar o arquivo de saída                |

---

## Caminhos operacionais padrão

| Variável        | Valor padrão                                                       |
|-----------------|--------------------------------------------------------------------|
| `DIR_INPUT`     | `~/devops/juridico-cli/var/input/md-frontmatter-yaml/`             |
| `DIR_OUTPUT`    | `~/devops/juridico-cli/var/output/md-frontmatter-yaml/`            |
| `DIR_ARTIFACTS` | `~/devops/juridico-cli/var/artifacts/skills/`                      |
| `SKILL_ZIP`     | `~/devops/juridico-cli/var/artifacts/skills/md-frontmatter-yaml.zip`|
