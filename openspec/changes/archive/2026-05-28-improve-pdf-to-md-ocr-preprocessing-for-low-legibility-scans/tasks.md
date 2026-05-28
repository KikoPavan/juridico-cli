## 1. Constante e função de pré-processamento de imagem

- [x] 1.1 Em `convert_pdf_to_md.py`, adicionar constante `MIN_OCR_POST_QUALITY` com o mesmo valor inicial de `MIN_TEXT_QUALITY`.
- [x] 1.2 Implementar `_preprocess_image(img_bytes: bytes) -> bytes` usando apenas Pillow: converter para escala de cinza (`convert("L")`), aplicar `ImageOps.autocontrast`, aplicar limiar de binarização (`point(lambda x: 255 if x > 128 else 0, "1")`), retornar como PNG bytes.
- [x] 1.3 Garantir que `_preprocess_image` captura qualquer exceção, registra erro em stderr e retorna os `img_bytes` originais sem propagar a exceção.

## 2. Integração do pré-processamento no caminho OCR

- [x] 2.1 Em `_extract_pymupdf`, antes de chamar `_run_paddle_ocr`, invocar `_preprocess_image(img_bytes)` para obter `preprocessed_bytes`. Registrar o resultado como `preprocessed_ok` (True se não houve fallback).
- [x] 2.2 Passar `preprocessed_bytes` (ou `img_bytes` em caso de fallback) para `_run_paddle_ocr`.
- [x] 2.3 Após o OCR, avaliar `_text_quality_score(ocr_text)`. Se o resultado for `< MIN_OCR_POST_QUALITY`, definir `raw` como `"[low_ocr_quality]"` e `status` como `"low_ocr_quality"`.

## 3. Logging de modo por página

- [x] 3.1 Substituir o label de log `ocr/{reason}` pelo modo preciso: `ocr_preprocessed` quando pré-processamento foi aplicado e OCR passou na qualidade; `ocr_raw` quando `_preprocess_image` fez fallback; `low_ocr_quality` quando a qualidade pós-OCR ficou abaixo de `MIN_OCR_POST_QUALITY`.
- [x] 3.2 Garantir que a linha de log exiba o modo como primeiro token (ex.: `[ocr_preprocessed] p.2: ok (342 chars)`).

## 4. Flag `--compare-ocr`

- [x] 4.1 Adicionar argumento `--compare-ocr` ao parser de linha de comando de `convert_pdf_to_md.py`.
- [x] 4.2 Suportar também a variável de ambiente `PDF_TO_MD_COMPARE_OCR=1` como alternativa à flag.
- [x] 4.3 Quando `--compare-ocr` estiver ativo, executar também `_run_paddle_ocr(img_bytes, ocr_engine)` (raw, sem pré-processamento) e registrar resultado em stderr com token `ocr_raw`. Não alterar o output Markdown final.

## 5. Preservação dos marcadores `[[Pág. N]]`

- [x] 5.1 Verificar que, para páginas com status `low_ocr_quality`, o marcador `[[Pág. N]]` ainda é emitido antes do placeholder `[low_ocr_quality]` no Markdown gerado.
- [x] 5.2 Verificar que o sumário de extração (bloco de metadados no topo do Markdown) lista corretamente páginas `low_ocr_quality` como categoria distinta.

## 6. Teste automatizado para o caminho `low_ocr_quality`

- [x] 6.1 Criar `test_ocr_quality_output.py` em `platform/skills/pdf-to-md/scripts/` com fixture sintética de texto OCR corrompido (score abaixo de `MIN_OCR_POST_QUALITY`).
- [x] 6.2 Implementar teste `test_low_ocr_quality_score_below_threshold`: verificar que `_text_quality_score(CORRUPTED_OCR_FIXTURE) < MIN_OCR_POST_QUALITY`.
- [x] 6.3 Implementar teste `test_preprocess_image_returns_bytes`: verificar que `_preprocess_image` retorna bytes não-vazios para uma imagem PNG sintética gerada com Pillow (sem PaddleOCR).
- [x] 6.4 Implementar teste `test_preprocess_image_fallback_on_error`: verificar que `_preprocess_image` retorna os bytes originais quando recebe entrada inválida (ex.: `b"not-a-png"`).
- [x] 6.5 Garantir que todos os testes passam sem PaddleOCR instalado (nenhum import de `paddleocr` no arquivo de teste).

## 7. Validação final

- [x] 7.1 Executar `uv run python platform/skills/pdf-to-md/scripts/test_ocr_quality_output.py` e confirmar saída `N/N tests passed.` com código de saída 0.
- [x] 7.2 Executar `uv run python platform/skills/pdf-to-md/scripts/test_quality_detection.py` e confirmar que todos os testes existentes continuam passando.
- [x] 7.3 Executar `openspec validate improve-pdf-to-md-ocr-preprocessing-for-low-legibility-scans --strict` e confirmar que passa sem erros.
