## 1. Constant and Quality Score Function

- [x] 1.1 Add constant `MIN_TEXT_QUALITY = 0.45` ao topo de `convert_pdf_to_md.py`, ao lado de `MIN_CHARS_FOR_TEXT` e `MIN_PRINTABLE_RATIO`
- [x] 1.2 Implementar função `_text_quality_score(text: str) -> float` em `convert_pdf_to_md.py`, usando as métricas: proporção de tokens com comprimento > 20 chars (`long_word_ratio`) e densidade de espaços (`chars_per_space = len(text) / (spaces + 1)`); retornar score entre 0.0 e 1.0
- [x] 1.3 Calibrar `MIN_TEXT_QUALITY` executando `_text_quality_score` sobre texto corrompido extraído de `28_30_certidão.pdf` (via PyMuPDF direto) e sobre um PDF digital limpo; ajustar constante se o valor 0.45 não separar corretamente os dois casos

## 2. Integration with `_needs_ocr`

- [x] 2.1 Modificar `_needs_ocr(text: str)` para retornar `tuple[bool, str]` — `(True, "low_quality")` quando `_text_quality_score` retornar abaixo de `MIN_TEXT_QUALITY`; `(True, "low_chars")` para contagem insuficiente; `(True, "low_printable")` para printable ratio; `(False, "ok")` caso contrário
- [x] 2.2 Atualizar todos os chamadores de `_needs_ocr` no arquivo (`_assess`, `_extract_pymupdf`) para desempacotar a tupla corretamente
- [x] 2.3 Atualizar o log verbose em `_extract_pymupdf` para exibir o motivo do roteamento (ex.: `[ocr/low_quality] p.3: ok (820 chars)`)
- [x] 2.4 Atualizar a geração do `conversion_report.md` para incluir coluna `reason` com o valor retornado por `_needs_ocr` por página

## 3. Tests

- [x] 3.1 Adicionar em `test_boilerplate_heuristic.py` (ou novo arquivo `test_quality_detection.py`) testes unitários de `_text_quality_score`: texto com palavras grudadas (ex.: `"oprocessofoiadistribuídoparaavaradesenhores"`) deve retornar score < `MIN_TEXT_QUALITY`
- [x] 3.2 Adicionar teste de `_text_quality_score` com texto português limpo (ex.: `"O processo foi distribuído para a vara de senhores."`) deve retornar score >= `MIN_TEXT_QUALITY`
- [x] 3.3 Adicionar teste de `_needs_ocr` para texto corrompido com quantidade suficiente de caracteres: deve retornar `(True, "low_quality")`
- [x] 3.4 Adicionar teste de `_needs_ocr` para texto limpo com quantidade suficiente de caracteres: deve retornar `(False, "ok")`
- [x] 3.5 Garantir que os testes existentes de `_strip_boilerplate` e `_needs_ocr` continuem passando sem alteração de comportamento para os casos de `low_chars` e `low_printable`

## 4. Fixtures

- [x] 4.1 Criar fixture de texto sintético representando padrão de corrupção do `certidão.pdf`: string com >= 100 caracteres imprimíveis e >= `MIN_CHARS_FOR_TEXT` chars, mas com palavras grudadas e espaçamento mínimo; usar como base nos testes 3.1 e 3.3

## 5. Validation

- [x] 5.1 Executar `uv run python platform/skills/pdf-to-md/scripts/test_boilerplate_heuristic.py` e confirmar que todos os testes passam
- [x] 5.2 Executar os novos testes de qualidade e confirmar exit code 0
- [x] 5.3 Executar `openspec validate improve-pdf-to-md-ocr-fallback-quality-detection --strict` e confirmar aprovação
