## 1. Boilerplate Detection

- [x] 1.1 Definir `BOILERPLATE_PATTERNS: list[re.Pattern]` em `convert_pdf_to_md.py` com padrões regex para cabeçalhos institucionais, numeração "Fls. N" / "fl. N", e rodapés recorrentes em documentos jurídicos brasileiros
- [x] 1.2 Implementar `_strip_boilerplate(text: str) -> str` que remove linhas que correspondem a qualquer padrão em `BOILERPLATE_PATTERNS` e retorna o texto residual

## 2. Atualização do Heurístico de OCR

- [x] 2.1 Modificar `_needs_ocr(text: str) -> bool` para chamar `_strip_boilerplate(text)` e avaliar o limiar `MIN_CHARS_FOR_TEXT` e `MIN_PRINTABLE_RATIO` sobre o texto residual (não sobre o texto bruto)
- [x] 2.2 Ajustar `_assess(text: str) -> str` caso o status de resultado precise refletir a detecção via boilerplate stripping (verificar se o status `"scanned_no_ocr"` ainda é adequado ou se um novo status é necessário)

## 3. Testes Unitários

- [x] 3.1 Adicionar testes unitários para `_strip_boilerplate`: verificar que linhas boilerplate conhecidas são removidas e que texto de corpo de petição é preservado intacto
- [x] 3.2 Adicionar testes para `_needs_ocr` com entrada boilerplate-only: confirmar que a função retorna `True` após strip
- [x] 3.3 Adicionar teste para página mista (boilerplate + corpo): confirmar que corpo suficiente retorna `_needs_ocr = False`

## 4. Validação

- [x] 4.1 Executar `test_ocr_path.py` e confirmar que o caminho OCR existente ainda passa (regressão)
- [x] 4.2 Executar os novos testes unitários e confirmar que todos passam com exit code 0

## 5. Correção do caso real ESAJ

- [x] Reproduzir o erro com `var/input/pdf-to-md/arquivo_escaneado.pdf`.
- [x] Confirmar que o output atual contém apenas boilerplate ESAJ.
- [x] Ajustar `_strip_boilerplate()` para remover integralmente:
  - "Para conferir o original..."
  - "Este documento é cópia do original..."
  - "fls. N"
- [x] Ajustar `_needs_ocr()` para acionar OCR quando o texto residual pós-boilerplate for vazio ou insuficiente.
- [x] Reexecutar `arquivo_escaneado.pdf`.
- [x] Confirmar no log que PaddleOCR foi acionado com `[ocr]`.
- [x] Confirmar que o Markdown final contém texto OCR além do boilerplate ESAJ.

**Critério de conclusão**: o PDF real `arquivo_escaneado.pdf` deve gerar Markdown com conteúdo extraído por OCR, não apenas rodapé ESAJ.
