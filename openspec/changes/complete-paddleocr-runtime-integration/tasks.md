## 1. Declarar dependência PaddleOCR

- [ ] 1.1 Adicionar grupo `[dependency-groups] ocr` em `pyproject.toml` com `paddleocr>=2.7` e `paddlepaddle` CPU (versão: A definir após validação)
- [ ] 1.2 Instalar o grupo com `uv sync --group ocr` e confirmar que `import paddleocr` não gera erros
- [ ] 1.3 Capturar e registrar a versão real instalada do PaddleOCR e do paddlepaddle (ex: `uv run python -c "import paddleocr; print(paddleocr.__version__)"`)

## 2. Registrar versões na matriz de versões

- [ ] 2.1 Atualizar `docs/reference/project_version_matrix.md`: substituir `A definir` pela versão real do PaddleOCR
- [ ] 2.2 Atualizar `docs/reference/project_version_matrix.md`: substituir `A definir` pela versão da skill `pdf-to-md` (usar `1.0.0` — já declarada em `SKILL.md`)

## 3. Criar teste E2E do caminho OCR

- [ ] 3.1 Criar `platform/skills/pdf-to-md/scripts/test_ocr_path.py` que gera um PNG sintético com texto legível via Pillow, executa `_run_paddle_ocr()` e verifica que o texto retornado contém a string esperada; exit 0 se ok, exit 1 se falhar
- [ ] 3.2 Executar `test_ocr_path.py` com sucesso e confirmar que o texto esperado é encontrado no resultado OCR

## 4. Atualizar documentação operacional

- [ ] 4.1 Remover a nota de limitação "PaddleOCR versão pendente de validação em `docs/reference/project_version_matrix.md`" de `platform/skills/pdf-to-md/SKILL.md`
- [ ] 4.2 Marcar o checkbox `- [ ] A skill pdf-to-md preserva PaddleOCR como OCR canônico.` como `- [x]` em `docs/runbooks/runbook_operacional_minimo.md`
