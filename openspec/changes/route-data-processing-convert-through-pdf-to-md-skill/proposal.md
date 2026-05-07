## Why

O módulo `apps/data-processing` possui uma implementação própria de conversão PDF→Markdown (`_convert_one_hybrid` em `stage_router.py`) que usa Gemini OCR como fallback, divergindo da skill canônica `pdf-to-md` (que usa PaddleOCR conforme `openspec/specs/pdf-to-md/spec.md`). Essa duplicação cria dois caminhos distintos para o mesmo comportamento e faz o módulo funcional ignorar a capacidade reutilizável já validada.

## What Changes

- Remover `_convert_one_hybrid` e qualquer lógica de conversão inline de `stage_router.py`.
- O estágio `convert` em `apps/data-processing` passa a delegar a conversão PDF→Markdown ao script canônico da skill: `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py`.
- O módulo usa a skill via subprocess ou import direto — sem duplicar lógica de OCR, threshold ou boilerplate.
- O CLI de data-processing continua expondo o comando `convert` com a mesma interface externa.

## Capabilities

### New Capabilities

- `data-processing-convert-routing`: Define como o estágio de conversão do módulo `data-processing` delega para a skill `pdf-to-md`. Cobre a interface de chamada, contrato de entrada/saída e tratamento de erros.

### Modified Capabilities

- `pdf-to-md`: Nenhuma mudança nos requisitos da spec — apenas confirmação de que o script da skill é o ponto de entrada canônico para conversão PDF→Markdown em todo o projeto.

## Impact

- `apps/data-processing/src/data_processing/orchestrator/stage_router.py`: remoção de `_convert_one_hybrid` e imports relacionados (Gemini OCR, `pdf2image`, `fitz` no path de conversão).
- `apps/data-processing/src/data_processing/converters/`: avaliar se subpacote `gemini_ocr` permanece necessário após a remoção.
- `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py`: nenhuma alteração — é o destino do roteamento, não o alvo da mudança.
- Nenhuma mudança em `openspec/specs/pdf-to-md/spec.md`.
- Dependência de `GEMINI_API_KEY` no path de conversão é removida; conversão passa a depender de `uv sync --group ocr` (PaddleOCR).
