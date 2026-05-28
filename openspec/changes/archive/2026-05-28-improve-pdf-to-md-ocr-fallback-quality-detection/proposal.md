## Why

O PyMuPDF pode extrair texto de PDFs que possuem camada textual, mas essa camada pode estar corrompida — palavras grudadas, espaçamento perdido, caracteres distorcidos — mesmo quando a contagem de caracteres ultrapassa o limiar mínimo. A lógica atual de `_needs_ocr` só verifica quantidade de caracteres, não qualidade textual, fazendo com que PDFs como `28_30_certidão.pdf` gerem Markdown ilegível sem acionar o PaddleOCR.

## What Changes

- Introdução de uma função de pontuação de qualidade textual (`_text_quality_score`) que analisa indicadores como proporção de palavras com espaçamento válido, densidade de caracteres especiais e coerência de distribuição de tokens.
- Modificação de `_needs_ocr` para disparar OCR também quando a qualidade textual extraída por PyMuPDF for abaixo do limiar, independentemente da contagem de caracteres.
- Adição de log por página indicando a origem do texto (`pymupdf` ou `ocr`) e o motivo do roteamento (baixa contagem, baixa qualidade ou OCR bem-sucedido).
- Testes automatizados cobrindo especificamente o caso de texto suficiente em quantidade mas corrompido em qualidade.

## Capabilities

### New Capabilities

- `text-quality-detection`: Avaliação da qualidade do texto extraído por PyMuPDF, determinando se o conteúdo é confiável para uso direto ou deve ser descartado em favor de OCR.

### Modified Capabilities

- `pdf-to-md`: Adição de cenário de detecção de texto corrompido — a lógica de roteamento para OCR passa a considerar qualidade além de quantidade.

## Impact

- `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py`: função `_needs_ocr` e nova função `_text_quality_score`.
- Testes da skill `pdf-to-md`: novo caso de teste para texto corrompido com quantidade suficiente.
- Fixtures de teste: amostra mínima derivada do caso real (`certidão.pdf`) ou sintética equivalente.
- Documentação da skill (`SKILL.md`): atualização se necessário para descrever o critério de qualidade.
- Sem impacto em `md-clean-markdown`, `md-frontmatter-yaml`, `platform/skill-runtime`, RAG, Outlines, Mem0, TurboQuant ou RLM.
