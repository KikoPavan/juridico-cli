## Why

A skill `pdf-to-md` foi implementada com o código de integração PaddleOCR presente (`convert_pdf_to_md.py`), mas o PaddleOCR não está instalado no ambiente, sua versão está marcada como `A definir` na matriz de versões e o caminho OCR nunca foi validado E2E. A skill opera em modo degradado — páginas escaneadas são marcadas como `scanned_no_ocr` — tornando o requisito canônico do projeto não operacional.

## What Changes

- Adicionar `paddleocr` (com backend CPU `paddlepaddle`) como grupo de dependência opcional `ocr` em `pyproject.toml`
- Validar compatibilidade com Python 3.12 e registrar versão real do PaddleOCR em `docs/reference/project_version_matrix.md`
- Criar script de teste E2E do caminho OCR (`test_ocr_path.py`) em `platform/skills/pdf-to-md/scripts/`
- Atualizar `SKILL.md` removendo a nota de limitação "PaddleOCR versão pendente de validação"
- Marcar checkbox do runbook: `A skill pdf-to-md preserva PaddleOCR como OCR canônico`

## Capabilities

### New Capabilities

_Nenhuma. A capacidade funcional já está definida na spec existente `pdf-to-md`._

### Modified Capabilities

- `pdf-to-md`: O requisito OCR muda de "usar PaddleOCR quando disponível" para "PaddleOCR DEVE estar instalado e validado; o caminho OCR é obrigatório, não degradado". Isso é uma mudança de spec — deixa de ser best-effort condicional.

## Impact

- `pyproject.toml` — novo grupo de dependência `[dependency-groups] ocr`
- `docs/reference/project_version_matrix.md` — versão do PaddleOCR e `pdf-to-md` registradas
- `platform/skills/pdf-to-md/scripts/test_ocr_path.py` — novo arquivo
- `platform/skills/pdf-to-md/SKILL.md` — remoção de nota de limitação
- `docs/runbooks/runbook_operacional_minimo.md` — checkbox marcado
- `openspec/specs/pdf-to-md/spec.md` — atualização do requisito OCR (de condicional para mandatório)
