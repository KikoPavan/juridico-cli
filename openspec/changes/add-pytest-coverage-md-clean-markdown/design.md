## Context

A skill `md-clean-markdown` possui `clean_markdown.py` com 9 regras de limpeza implementadas e determinísticas. O arquivo `test_clean_markdown.py` cobre trailing whitespace (Regra 2) e marcadores de página (Regra 7), mas as Regras 4, 5, 6, 8 e os mecanismos de isolamento de blocos de código (Regras 1/7) e o CLI E2E não têm cobertura. Não há decisão arquitetural a tomar: os testes ampliam o arquivo existente, sem criar nova infraestrutura.

## Goals / Non-Goals

**Goals:**
- Adicionar testes unitários para as funções `_fix_heading_space`, `_fix_bullet`, `_fix_horizontal_rule`, `_remove_decorative_line`, `_extract_code_blocks`, `_restore_code_blocks`
- Adicionar testes de integração via `clean_lines` para `--max-blank` customizado e `--no-markers`
- Adicionar teste E2E via `subprocess` exercendo o CLI com arquivo temporário
- Adicionar teste de validação usando `validate_output.run_validation`
- Manter tudo em `test_clean_markdown.py` (arquivo existente)

**Non-Goals:**
- Não criar suíte paralela ou fixture adicional (além da já existente `pdf_to_md_sample.md`)
- Não alterar `clean_markdown.py`, `validate_output.py`, `SKILL.md` ou assets
- Não modificar `pyproject.toml` ou configuração de pytest
- Não cobrir `build_report` ou `main()` diretamente (coberto indiretamente pelo E2E)

## Decisions

**Testes unitários diretos sobre funções privadas** — as funções de limpeza são importadas diretamente (`from clean_markdown import _fix_heading_space, ...`), consistente com o padrão já adotado no arquivo para `_fix_trailing_whitespace`. Não há necessidade de refatorar para expor API pública.

**E2E via `subprocess`** — o teste CLI usa `subprocess.run` com arquivo temporário (`tmp_path` do pytest), garantindo que o argparse, leitura e escrita funcionem de ponta a ponta. Não usa mock de I/O.

**Validação com `validate_output.run_validation`** — importar e chamar `run_validation` diretamente (não via subprocess) para verificar que a saída do pipeline passa o validador. Consistente com o fato de que `validate_output.py` já importa sem side-effects em `__main__`.

## Risks / Trade-offs

- [Risco] Testes de funções privadas ficam acoplados à implementação interna → Mitigação: acoplamento é intencional e aceito para skills determinísticas de limpeza textual, onde a interface é o comportamento linha a linha.
- [Risco] Teste E2E com `subprocess` pode ser lento se a fixture for grande → Mitigação: o fixture `pdf_to_md_sample.md` tem ~121 linhas; o E2E é trivialmente rápido.
