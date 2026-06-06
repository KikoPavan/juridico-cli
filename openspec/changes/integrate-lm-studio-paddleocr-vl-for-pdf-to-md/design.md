# Design: Integrar PaddleOCR-VL via LM Studio ao pdf-to-md

## Decisão Arquitetural

LM Studio serve PaddleOCR-VL via protocolo OpenAI-compatible (vision). O `pdf-to-md` envia a imagem renderizada da página como PNG base64 via `POST /v1/chat/completions` e recebe o texto extraído. O PaddleOCR local é removido como backend de OCR.

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `LM_STUDIO_BASE_URL` | Endpoint base da API (ex: `http://172.26.64.1:1234/v1`) |
| `LM_STUDIO_OCR_MODEL` | ID do modelo (ex: `paddlepaddle/paddleocr-vl-1.5-gguf/paddleocr-vl-1.5.gguf`) |

Nenhum IP hardcoded no código. Se as variáveis não estiverem definidas → `LmStudioUnavailableError` → `[ocr_backend_unavailable]`.

## Protocolo de Chamada

```json
POST {LM_STUDIO_BASE_URL}/chat/completions
Content-Type: application/json

{
  "model": "{LM_STUDIO_OCR_MODEL}",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,{base64_png}"}},
      {"type": "text", "text": "Extract all text from this document page. Return verbatim, preserving line breaks. No explanations."}
    ]
  }],
  "max_tokens": 4096,
  "temperature": 0
}
```

Dependência de rede: `urllib.request` (stdlib). Sem dependências externas adicionais.

## Fluxo de Decisão

```
Página extraída
  └─ _needs_ocr?
        ├─ Não → status=ok
        └─ Sim
              ├─ _render_page_image → _preprocess_image
              ├─ _run_lm_studio_ocr(img_bytes)
              │      ├─ Sucesso → _ocr_post_quality_score(text)
              │      │      ├─ score ≥ MIN_OCR_POST_QUALITY → status=ok, ocr_mode=lm_studio_ocr
              │      │      └─ score < MIN_OCR_POST_QUALITY → [low_ocr_quality]
              │      └─ LmStudioUnavailableError → [ocr_backend_unavailable]
              └─ Exception genérica → status=scanned_no_ocr
```

## Mudanças por Arquivo

- `convert_pdf_to_md.py`: remover `_paddle_ocr_instance`, `_get_paddle_ocr`, `_run_paddle_ocr`; adicionar `LmStudioUnavailableError`, `_run_lm_studio_ocr`; atualizar `_extract_pymupdf`, `build_markdown`, `build_report`.
- `llm_registry.yaml`: adicionar modelo `paddleocr-vl-1.5` na classe `lm_studio_local` e perfil `ocr_local`.
- `test_ocr_quality_output.py`: adicionar testes para `LmStudioUnavailableError` (env vars ausentes) e token `[ocr_backend_unavailable]`.
- `test_quality_detection.py`: sem mudanças (testa apenas _needs_ocr / _text_quality_score).
