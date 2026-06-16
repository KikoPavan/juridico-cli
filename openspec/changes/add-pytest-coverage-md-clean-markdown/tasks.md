## 1. Testes unitários de regras de limpeza

- [x] 1.1 Adicionar testes para `_fix_heading_space`: sem espaço após `#`, excesso de espaços, heading já correto (sem alteração)
- [x] 1.2 Adicionar testes para `_fix_bullet`: `*` → `-`, `+` → `-`, `-` inalterado, `*palavra*` não tratado como bullet
- [x] 1.3 Adicionar testes para `_fix_horizontal_rule`: `***`, `___`, `===`, `- - - -` normalizados para `---`; linha com texto não normalizada
- [x] 1.4 Adicionar testes para `_remove_decorative_line`: `....` removido, `====` removido, linha normal preservada

## 2. Testes de isolamento de blocos de código

- [x] 2.1 Adicionar teste para `_extract_code_blocks`: bloco com ` ``` ` substituído por placeholder `__CODE_BLOCK_0__`, conteúdo salvo no dict
- [x] 2.2 Adicionar teste para `_restore_code_blocks`: placeholder restaurado ao conteúdo original exato
- [x] 2.3 Adicionar teste de integração: trailing whitespace dentro de bloco de código preservado após extract → `clean_lines` → restore

## 3. Testes de pipeline com parâmetros opcionais

- [x] 3.1 Adicionar teste para `clean_lines` com `max_blank=1`: sequência de 3 linhas em branco colapsada para 1
- [x] 3.2 Adicionar teste para `clean_lines` com `preserve_markers=False`: marcador `[[Pág. N]]` tratado como texto comum (não bypassa regras, linha presente na saída)

## 4. Teste CLI ponta a ponta

- [x] 4.1 Adicionar teste E2E via `subprocess.run` usando o fixture `pdf_to_md_sample.md` como entrada e `tmp_path` do pytest como saída: exit code 0, arquivo gerado não vazio

## 5. Teste de validação de saída

- [x] 5.1 Adicionar teste que importa `validate_output.run_validation` e executa sobre o output gerado pelo E2E (task 4.1): retorno 0, sem erros

## 6. Verificação final

- [x] 6.1 Executar `uv run pytest platform/skills/md-clean-markdown/ -q` e confirmar que todos os testes passam (mínimo 14 existentes + novos)
- [x] 6.2 Executar `uv run pytest -q` e confirmar que a suíte global passa sem regressões
- [x] 6.3 Executar `openspec validate add-pytest-coverage-md-clean-markdown --strict` e confirmar 0 erros
- [x] 6.4 Executar `openspec validate --all --strict` e confirmar 0 erros
