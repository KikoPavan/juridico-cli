## 1. Boilerplate Detection

- [ ] 1.1 Definir `BOILERPLATE_PATTERNS: list[re.Pattern]` em `convert_pdf_to_md.py` com padrões regex para cabeçalhos institucionais, numeração "Fls. N" / "fl. N", e rodapés recorrentes em documentos jurídicos brasileiros
- [ ] 1.2 Implementar `_strip_boilerplate(text: str) -> str` que remove linhas que correspondem a qualquer padrão em `BOILERPLATE_PATTERNS` e retorna o texto residual

## 2. Atualização do Heurístico de OCR

- [ ] 2.1 Modificar `_needs_ocr(text: str) -> bool` para chamar `_strip_boilerplate(text)` e avaliar o limiar `MIN_CHARS_FOR_TEXT` e `MIN_PRINTABLE_RATIO` sobre o texto residual (não sobre o texto bruto)
- [ ] 2.2 Ajustar `_assess(text: str) -> str` caso o status de resultado precise refletir a detecção via boilerplate stripping (verificar se o status `"scanned_no_ocr"` ainda é adequado ou se um novo status é necessário)

## 3. Testes Unitários

- [ ] 3.1 Adicionar testes unitários para `_strip_boilerplate`: verificar que linhas boilerplate conhecidas são removidas e que texto de corpo de petição é preservado intacto
- [ ] 3.2 Adicionar testes para `_needs_ocr` com entrada boilerplate-only: confirmar que a função retorna `True` após strip
- [ ] 3.3 Adicionar teste para página mista (boilerplate + corpo): confirmar que corpo suficiente retorna `_needs_ocr = False`

## 4. Validação

- [ ] 4.1 Executar `test_ocr_path.py` e confirmar que o caminho OCR existente ainda passa (regressão)
- [ ] 4.2 Executar os novos testes unitários e confirmar que todos passam com exit code 0
