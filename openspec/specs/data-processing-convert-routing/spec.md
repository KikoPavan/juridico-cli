# data-processing-convert-routing Specification

## Purpose
TBD - created by archiving change route-data-processing-convert-through-pdf-to-md-skill. Update Purpose after archive.
## Requirements
### Requirement: Delegar conversão PDF→Markdown à skill pdf-to-md

O estágio de conversão do módulo `data-processing` SHALL delegar toda conversão PDF→Markdown ao script `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py`, invocado via subprocess.

#### Scenario: Conversão bem-sucedida via skill

- **GIVEN** um arquivo PDF válido em `var/input/pdf/`
- **WHEN** o estágio `convert` de `data-processing` processa o arquivo
- **THEN** o sistema DEVE invocar `convert_pdf_to_md.py` via subprocess com `--input` e `--output`
- **AND** o processo DEVE retornar exit code `0`
- **AND** o arquivo `.md` de saída DEVE ser gerado em `var/input/md/`

#### Scenario: Falha de conversão propagada corretamente

- **GIVEN** um arquivo PDF inválido ou inacessível
- **WHEN** o estágio `convert` invoca `convert_pdf_to_md.py`
- **THEN** o processo DEVE retornar exit code diferente de `0`
- **AND** o módulo `data-processing` DEVE registrar o erro e interromper o processamento do arquivo afetado
- **AND** outros arquivos do batch DEVEM continuar sendo processados

#### Scenario: Caminho do script resolvido dinamicamente

- **GIVEN** o projeto clonado em qualquer diretório
- **WHEN** `stage_router.py` constrói o comando de subprocess
- **THEN** o caminho para `convert_pdf_to_md.py` DEVE ser resolvido a partir da raiz do projeto, sem hard-coding absoluto
- **AND** a resolução DEVE usar `Path(__file__)` como âncora

### Requirement: Remover implementação inline de conversão

O módulo `apps/data-processing` MUST NOT conter implementação própria de conversão PDF→Markdown após esta mudança.

#### Scenario: Ausência de _convert_one_hybrid

- **GIVEN** o módulo `apps/data-processing` instalado
- **WHEN** `stage_router.py` é inspecionado
- **THEN** a função `_convert_one_hybrid` NÃO DEVE existir no módulo
- **AND** nenhum import de `data_processing.converters.gemini_ocr` DEVE existir no caminho de conversão

#### Scenario: Ausência do subpacote gemini_ocr

- **GIVEN** o repositório após a aplicação desta change
- **WHEN** `apps/data-processing/src/data_processing/converters/` é inspecionado
- **THEN** o subpacote `gemini_ocr/` NÃO DEVE existir

### Requirement: Dependência de GEMINI_API_KEY removida do path de conversão

O estágio de conversão do módulo `data-processing` MUST NOT depender de `GEMINI_API_KEY` para executar.

#### Scenario: Conversão sem GEMINI_API_KEY definida

- **GIVEN** o ambiente sem a variável `GEMINI_API_KEY` definida
- **WHEN** o estágio `convert` processa um PDF com páginas escaneadas
- **THEN** a conversão DEVE completar usando PaddleOCR (via skill `pdf-to-md`)
- **AND** o sistema NÃO DEVE emitir aviso de "GEMINI_API_KEY não definida"
- **AND** nenhuma página DEVE ser omitida por ausência de Gemini

