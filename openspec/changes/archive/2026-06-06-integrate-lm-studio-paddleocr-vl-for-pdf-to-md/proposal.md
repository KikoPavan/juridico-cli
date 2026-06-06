# Proposal: Integrar PaddleOCR-VL via LM Studio ao pdf-to-md

## Objetivo

Integrar o modelo PaddleOCR-VL servido pelo LM Studio como backend principal de OCR documental da skill `pdf-to-md`.

## Contexto

O pipeline atual `pdf-to-md` usa PyMuPDF e PaddleOCR local. Esse fluxo detecta texto nativo ruim e marca OCR de baixa qualidade como `[low_ocr_quality]`, mas ainda não utiliza o backend OCR decidido para o projeto: PaddleOCR-VL via LM Studio.

## Mudança proposta

Quando uma página exigir OCR, o `pdf-to-md` deve usar LM Studio com o modelo PaddleOCR-VL, recebendo a imagem renderizada da página e retornando texto/Markdown para validação de qualidade.

## Fora de escopo

- Não alterar `md-clean-markdown`.
- Não alterar `md-frontmatter-yaml`.
- Não iniciar extração jurídica.
- Não iniciar RAG.
- Não alterar schemas jurídicos.
