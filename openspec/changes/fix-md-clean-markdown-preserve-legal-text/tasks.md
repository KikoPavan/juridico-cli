## 1. Investigação da causa raiz (concluída)

- [x] 1.1 Executar `clean_markdown.py` diretamente (fora do CLI de data-processing) sobre `var/input/md/Petição Declaração de Nulidade.md` — confirmado: nenhuma corrupção. O CLI usa `LegalDocCleaner` de `clean_legal_docs.py`, não `clean_markdown.py`
- [x] 1.2 Inspecionar a codificação real do arquivo de entrada — confirmado: UTF-8 válido; sem `\r` no output corrompido
- [x] 1.3 Causa raiz documentada: (a) `"Ã": "Á"` em `fix_encoding` corrompe todo `Ã` válido → `ÁO`; (b) `\s*` final nos padrões de `patterns_to_remove` consume `\n`, colando headings

## 2. Correção de fix_encoding em clean_legal_docs.py

- [x] 2.1 Remover a entrada `"Ã": "Á"` do dicionário `replacements` em `LegalDocCleaner.fix_encoding` — esta substituição global é incorreta para texto UTF-8 válido

## 3. Correção de patterns_to_remove em clean_legal_docs.py

- [x] 3.1 Substituir todos os quantificadores `\s*` finais nos padrões de `self.patterns_to_remove` por `[ \t]*` — impedir que a remoção de cabeçalhos consuma o `\n` da linha seguinte

## 4. Testes de regressão em test_cleaners.py

- [x] 4.1 Adicionar `test_fix_encoding_does_not_corrupt_acao`: `fix_encoding("AÇÃO DECLARATÓRIA")` deve retornar `"AÇÃO DECLARATÓRIA"` sem alteração
- [x] 4.2 Adicionar `test_fix_encoding_does_not_corrupt_nao`: `fix_encoding("NÃO contém")` deve retornar `"NÃO contém"`
- [x] 4.3 Adicionar `test_fix_encoding_does_not_corrupt_qualificacao`: `fix_encoding("QUALIFICAÇÃO")` preserva `Ã`
- [x] 4.4 Adicionar `test_fix_encoding_does_not_corrupt_procuracao`: `fix_encoding("PROCURAÇÃO")` preserva `Ã`
- [x] 4.5 Adicionar `test_fix_encoding_does_not_corrupt_pretensao`: `fix_encoding("PRETENSÃO")` preserva `Ã`
- [x] 4.6 Adicionar `test_fix_encoding_preserves_page_marker`: `fix_encoding("[[Pág. 3]]")` retorna `"[[Pág. 3]]"` sem alteração
- [x] 4.7 Adicionar `test_remove_headers_footers_does_not_join_heading_after_comarca`: texto com `COMARCA DE CERQUEIRA CÉSAR\n# DECLARATÓRIA` — após `remove_headers_footers`, output NÃO deve conter `SP# DECLARATÓRIA` em linha única
- [x] 4.8 Adicionar `test_remove_headers_footers_does_not_join_heading_after_foro`: texto com `FORO DE CERQUEIRA CÉSAR\n# DA PROCURAÇÃO` — output NÃO deve conter `declaratória.#` em linha única
- [x] 4.9 Adicionar `test_clean_document_preserves_accents_end_to_end`: `clean_document` sobre arquivo com `AÇÃO`, `NÃO`, `QUALIFICAÇÃO`, `PROCURAÇÃO`, `PRETENSÃO` — output deve conter todas sem corrupção

## 5. Validação

- [x] 5.1 Executar `uv run pytest apps/data-processing/tests/test_cleaners.py -q` — todos os testes devem passar
- [x] 5.2 Executar `uv run pytest -q` — suite completa sem regressão
- [x] 5.3 Executar o pipeline via CLI: `PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli clean --input "var/input/md" --output "var/output/processed"`
- [x] 5.4 Verificar ausência de corrupção: `grep -nE "AÇÁO|NÁO|QUALIFICAÇÁO|PROCURAÇÁO|PRETENSÁO|SP#|declaratória\.#" "$CLEAN"` deve retornar vazio
- [x] 5.5 Executar `openspec validate --all --strict` e confirmar que passa
