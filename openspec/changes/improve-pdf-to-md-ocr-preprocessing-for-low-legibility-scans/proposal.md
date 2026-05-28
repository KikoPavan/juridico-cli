## Why

PDFs escaneados de baixa legibilidade (ex.: `procuração_Monica.pdf`) acionam o PaddleOCR mas produzem texto inutilizável — palavras corrompidas, caracteres quebrados, títulos artificiais — sem qualquer indicação no output de que o resultado é de baixa qualidade. O pipeline atual não pré-processa a imagem antes do OCR nem distingue entre OCR bem-sucedido e OCR degradado.

## What Changes

- Antes de invocar o PaddleOCR, cada página renderizada como imagem deve passar por pré-processamento (escala de cinza, binarização adaptativa, deskew quando aplicável).
- O modo de OCR de cada página deve ser registrado em log: `ocr_raw`, `ocr_preprocessed` ou `low_ocr_quality`.
- Páginas cujo resultado de OCR permaneça abaixo do limiar de qualidade após o pré-processamento devem ser marcadas como `low_ocr_quality` no output, em vez de emitir texto corrompido sem aviso.
- A skill deve permitir observar a diferença entre OCR sem pré-processamento e com pré-processamento para fins de diagnóstico.
- Os marcadores `[[Pág. N]]` devem ser preservados em todos os modos.
- Deve existir teste automatizado cobrindo o caminho `low_ocr_quality`.

## Capabilities

### New Capabilities

- `ocr-image-preprocessing`: Pipeline de pré-processamento de imagem (grayscale, binarização adaptativa, deskew) aplicado à página renderizada antes de invocar o PaddleOCR.
- `ocr-quality-logging`: Registro por página do modo de OCR utilizado (`ocr_raw`, `ocr_preprocessed`, `low_ocr_quality`) e emissão de marcador `low_ocr_quality` quando o resultado permanece abaixo do limiar após pré-processamento.

### Modified Capabilities

- `pdf-to-md`: O requisito de uso do PaddleOCR passa a incluir etapa obrigatória de pré-processamento de imagem antes da chamada OCR, e o comportamento em caso de OCR de baixa qualidade agora é definido (marcar como `low_ocr_quality`, sem emitir texto corrompido sem aviso).

## Impact

- `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` — adição das funções de pré-processamento e da lógica de avaliação de qualidade pós-OCR.
- Testes da skill `pdf-to-md` — novo teste para o caminho `low_ocr_quality`.
- Fixtures de teste — fixture sintética pequena representando página escaneada de baixa legibilidade.
- Dependências Python — possível adição de `opencv-python-headless` ou `Pillow` para pré-processamento; verificar `docs/reference/project_version_matrix.md` antes de adicionar.
- `openspec/specs/pdf-to-md/spec.md` — delta de requisitos para os comportamentos novos.
- Nenhuma alteração em `md-clean-markdown`, `md-frontmatter-yaml`, `platform/skill-runtime` ou qualquer módulo jurídico.
