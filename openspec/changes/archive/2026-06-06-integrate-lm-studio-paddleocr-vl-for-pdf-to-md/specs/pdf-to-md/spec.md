# Spec: pdf-to-md — LM Studio/PaddleOCR-VL como backend OCR

## ADDED Requirements

### Requirement: LM Studio/PaddleOCR-VL como backend primário de OCR

Quando uma página exigir OCR (`_needs_ocr` retornar `True`), o sistema SHALL chamar `_run_lm_studio_ocr` com a imagem renderizada da página. O endpoint e o modelo são lidos exclusivamente das variáveis de ambiente `LM_STUDIO_BASE_URL` e `LM_STUDIO_OCR_MODEL`. Nenhum valor de IP ou model ID pode ser hardcoded no código. O log deve registrar `[lm_studio_ocr]` para páginas processadas por OCR.

#### Scenario: página escaneada com LM Studio disponível

- **GIVEN** uma página cujo texto nativo falha em `_needs_ocr`
- **AND** `LM_STUDIO_BASE_URL` e `LM_STUDIO_OCR_MODEL` estão definidos no ambiente
- **WHEN** o sistema processa a página
- **THEN** a imagem renderizada é enviada para LM Studio via `POST /chat/completions`
- **AND** o log verbose indica `[lm_studio_ocr] p.N`
- **AND** o texto retornado pelo modelo é inserido no Markdown de saída

#### Scenario: variáveis de ambiente ausentes — sem rede necessária

- **GIVEN** `LM_STUDIO_BASE_URL` não está definida no ambiente
- **WHEN** `_run_lm_studio_ocr` é chamada
- **THEN** `LmStudioUnavailableError` é levantada imediatamente, sem tentativa de conexão

---

### Requirement: Backend indisponível gera token `[ocr_backend_unavailable]`

Se a chamada a `_run_lm_studio_ocr` levantar `LmStudioUnavailableError` (variáveis ausentes ou falha HTTP), o sistema SHALL:
- Marcar a página com status `ocr_backend_unavailable`
- Inserir o token literal `[ocr_backend_unavailable]` no Markdown de saída
- Registrar no stderr o token `[ocr_backend_unavailable]` com o número da página
- Preservar a âncora `[[Pág. N]]` antes do token

#### Scenario: backend indisponível — output e log

- **GIVEN** uma página que requer OCR
- **AND** `LM_STUDIO_BASE_URL` não está definida
- **WHEN** o Markdown é gerado
- **THEN** o output contém `[[Pág. N]]` seguido de `[ocr_backend_unavailable]`
- **AND** o stderr contém `[ocr_backend_unavailable] p.N`

#### Scenario: âncora preservada com backend indisponível

- **GIVEN** uma página marcada como `ocr_backend_unavailable`
- **WHEN** `build_markdown` é chamada
- **THEN** `[[Pág. N]]` aparece antes de `[ocr_backend_unavailable]` no output

---

### Requirement: Qualidade pós-OCR preservada com `[low_ocr_quality]`

Após OCR bem-sucedido, o sistema SHALL aplicar `_ocr_post_quality_score` ao texto retornado. Se o score for menor que `MIN_OCR_POST_QUALITY`, o sistema SHALL substituir o texto pelo token `[low_ocr_quality]`.

#### Scenario: OCR retorna texto corrompido

- **GIVEN** LM Studio retorna texto com case-chaos ou glued words
- **WHEN** `_ocr_post_quality_score` avalia o resultado
- **AND** o score está abaixo de `MIN_OCR_POST_QUALITY`
- **THEN** o output contém `[low_ocr_quality]` para essa página
- **AND** o texto corrompido não aparece no output

---

### Requirement: Modelo PaddleOCR-VL registrado no `llm_registry.yaml`

O modelo `paddlepaddle/paddleocr-vl-1.5-gguf/paddleocr-vl-1.5.gguf` SHALL constar na classe `lm_studio_local` do `llm_registry.yaml`. Um perfil `ocr_local` SHALL referenciar esse modelo.

#### Scenario: perfil ocr_local presente no registry

- **GIVEN** `llm_registry.yaml` contém a entrada do modelo em `lm_studio_local`
- **WHEN** o perfil `ocr_local` é consultado
- **THEN** ele resolve para o modelo `paddlepaddle/paddleocr-vl-1.5-gguf/paddleocr-vl-1.5.gguf`
