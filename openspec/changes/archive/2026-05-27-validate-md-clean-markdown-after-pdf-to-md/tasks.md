## 1. Criar fixture de teste com output real de pdf-to-md

- [x] 1.1 Criar diretório `scripts/tests/fixtures/` em `platform/skills/md-clean-markdown/`
- [x] 1.2 Criar `pdf_to_md_sample.md` com recorte de 2 páginas de `var/output/pdf-to-md/arquivo_escaneado.md` (linhas 1-120), mantendo marcadores `[[Pág. 1]]` e `[[Pág. 2]]`, OCR artifacts, headings e texto jurídico

## 2. Atualizar exemplos de referência

- [x] 2.1 Substituir `references/exemplo_entrada.md`: remover conteúdo fictício em bloco de código e usar o documento real `arquivo_escaneado.md` como conteúdo de exemplo, mantendo a estrutura de documentação (metadados, lista de problemas de formatação)
- [x] 2.2 Executar `clean_markdown.py --input var/output/pdf-to-md/arquivo_escaneado.md --output /tmp/saida_real_limpa.md --verbose` para obter o resultado real
- [x] 2.3 Substituir `references/exemplo_saida.md`: usar o conteúdo gerado em 2.2 como exemplo de saída, atualizando metadados e lista de transformações

## 3. Adicionar testes com fixture real

- [x] 3.1 Adicionar função `test_realfixture_markers_preserved()` em `test_clean_markdown.py` que: carrega `fixtures/pdf_to_md_sample.md`, executa `clean_lines` e verifica que todos `[[Pág. N]]` estão intactos
- [x] 3.2 Adicionar função `test_realfixture_content_integrity()` que verifica que texto jurídico (ex.: trecho de qualificação de partes) não foi truncado ou removido
- [x] 3.3 Executar `python test_clean_markdown.py` e confirmar que todos os testes passam

## 4. Validar E2E com --strict

- [x] 4.1 Executar `python clean_markdown.py --input fixtures/pdf_to_md_sample.md --output /tmp/e2e_test_output.md`
- [x] 4.2 Executar `python validate_output.py --input /tmp/e2e_test_output.md --source fixtures/pdf_to_md_sample.md --strict`
- [x] 4.3 Confirmar exit code 0 e que todas as verificações passam

## 5. Regenerar outputs em var/output/

- [x] 5.1 Executar `clean_markdown.py --input var/output/pdf-to-md/arquivo_escaneado.md --output var/output/md-clean-markdown/arquivo_escaneado_limpo.md --verbose` para regenerar o arquivo limpo
- [x] 5.2 Executar `validate_output.py --input var/output/md-clean-markdown/arquivo_escaneado_limpo.md --source var/output/pdf-to-md/arquivo_escaneado.md --strict`
- [x] 5.3 Confirmar que `run_example.sh` ainda funciona — executar `bash scripts/run_example.sh` sem erros

## 6. Validação final

- [x] 6.1 Re-executar `python test_clean_markdown.py` e confirmar 0 falhas
- [x] 6.2 Verificar que `validate_output.py --strict --source` passa para todos os exemplos em `references/`
- [x] 6.3 Confirmar que `arquivo_escaneado_limpo.md` agora tem diferenças reais em relação ao original (pelo menos trailing whitespace corrigido)
