## 1. Substituir _convert_one_hybrid por delegação à skill

- [x] 1.1 Em `apps/data-processing/src/data_processing/orchestrator/stage_router.py`, adicionar função `_convert_via_skill(pdf_path: Path, out_md: Path) -> None` que invoca `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` via `subprocess.run` com `sys.executable`, passando `--input` e `--output`
- [x] 1.2 Resolver o caminho do script dinamicamente a partir de `Path(__file__)` navegando até a raiz do projeto (sem hard-code absoluto)
- [x] 1.3 Tratar exit code != 0 do subprocess levantando exceção com mensagem descritiva (incluindo stderr capturado)
- [x] 1.4 Substituir a chamada `engine.run_batch(_convert_one_hybrid)` por `engine.run_batch(_convert_via_skill)` em `stage_router.py`
- [x] 1.5 Remover a função `_convert_one_hybrid` e todos os imports relacionados (`fitz` no path de conversão, `pdf2image` no path de conversão, `gemini_ocr.page_ocr`) de `stage_router.py`

## 2. Remover subpacote converters/gemini_ocr

- [x] 2.1 Confirmar via grep que não há outras referências a `converters/gemini_ocr` fora de `stage_router.py` no módulo `data-processing`
- [x] 2.2 Remover o diretório `apps/data-processing/src/data_processing/converters/gemini_ocr/` inteiro

## 3. Validação

- [x] 3.1 Executar `grep -r "gemini_ocr\|_convert_one_hybrid\|GEMINI_API_KEY" apps/data-processing/src/` e confirmar ausência de resultados no path de conversão
- [x] 3.2 Executar o pipeline de conversão com um PDF de teste em `var/input/pdf/` e confirmar que o `.md` é gerado corretamente em `var/input/md/`
- [x] 3.3 Executar os testes existentes do módulo: `uv run pytest apps/data-processing/tests/ -v` e confirmar que todos passam
