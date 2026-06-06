# Tasks: integrate-lm-studio-paddleocr-vl-for-pdf-to-md

## Progresso

17/17 concluídas.

---

## Tarefas

- [x] **T1** — `llm_registry.yaml`: adicionar modelo `paddleocr-vl-1.5` na classe `lm_studio_local` e perfil `ocr_local`
- [x] **T2** — `convert_pdf_to_md.py`: remover `_paddle_ocr_instance`, `_get_paddle_ocr`, `_run_paddle_ocr`; adicionar `LmStudioUnavailableError` e `_run_lm_studio_ocr`
- [x] **T3** — `convert_pdf_to_md.py`: atualizar `_extract_pymupdf` para usar `_run_lm_studio_ocr` como backend primário, com tratamento de `LmStudioUnavailableError`
- [x] **T4** — `convert_pdf_to_md.py`: atualizar `build_markdown` e `build_report` para status `ocr_backend_unavailable`
- [x] **T5** — `test_ocr_quality_output.py`: adicionar testes para `LmStudioUnavailableError` (env vars ausentes) e importação da exceção
- [x] **T6** — Executar testes: `uv run python test_quality_detection.py` e `uv run python test_ocr_quality_output.py` — todos devem passar
- [x] **T7** — `openspec validate --strict` — deve passar sem erros
- [x] **T8** — `convert_pdf_to_md.py`: corrigir timeout configurável via `LM_STUDIO_OCR_TIMEOUT_SECONDS` (default 300s); capturar `TimeoutError` como `ocr_backend_unavailable`; registrar no log timeout configurado, duração por página e se falhou por timeout
- [x] **T9** — `convert_pdf_to_md.py`: adicionar `_sanitize_paddleocr_output(text)` que remove tokens `<|LOC_...|>`, detecta sequências `o-o-o-o`, repetição excessiva de linhas e de números; retorna `(texto_limpo, métricas)`
- [x] **T10** — `convert_pdf_to_md.py`: integrar `_sanitize_paddleocr_output` em `_extract_pymupdf`; registrar no log tokens LOC removidos, repetição detectada, score pós-sanitização e decisão; reprovar via `[low_ocr_quality]` se repetição detectada ou score insuficiente
- [x] **T11** — `test_ocr_quality_output.py`: adicionar testes para `_sanitize_paddleocr_output`: remoção de tokens LOC, detecção de o-o-o-o, repetição de linhas, repetição de números, texto limpo sem falso positivo
- [x] **T12** — Executar `uv run python test_ocr_quality_output.py` e `openspec validate --strict` — todos devem passar
- [x] **T13** — `convert_pdf_to_md.py`: adicionar `_local_paddle_ocr_instance = None`, `_local_paddle_ocr_checked = False`; funções `_get_local_paddle_ocr()` (lazy init + cache, retorna `None` se indisponível) e `_run_local_ocr(img_bytes: bytes) -> str | None` (retorna texto ou `None` se PaddleOCR não instalado ou falhou)
- [x] **T14** — `convert_pdf_to_md.py`: adicionar `_pick_best_ocr(candidates) -> tuple[str, str, str, str, dict]`; sanitiza cada candidato não-nulo via `_sanitize_paddleocr_output`; calcula score via `_ocr_post_quality_score`; retorna `(texto, status, ocr_mode, motivo, scores_por_backend)`; `[ocr_backend_unavailable]` se nenhum texto disponível; `[low_ocr_quality]` se todos abaixo do threshold
- [x] **T15** — `convert_pdf_to_md.py`: refatorar bloco `if needs:` em `_extract_pymupdf` para execução dual: (a) `_run_local_ocr` com timing; (b) `_run_lm_studio_ocr` se configurado com timing; chamar `_pick_best_ocr`; logar `[ocr_selection] p.N: score_local=X score_vl=Y backend=Z motivo=W` no stderr; atualizar verbose block
- [x] **T16** — `test_ocr_quality_output.py`: importar `_run_local_ocr` e `_pick_best_ocr`; adicionar testes: ambos indisponíveis → `ocr_backend_unavailable`; ambos reprovados → `low_ocr_quality`; apenas local aprovado → usa local; apenas VL aprovado → usa VL
- [x] **T17** — Executar `uv run python test_ocr_quality_output.py` e `openspec validate --strict` — todos devem passar

---

## Critérios Gerais

- Nenhum IP hardcoded no código de produção
- `[[Pág. N]]` preservados em todas as páginas
- Log indica `[lm_studio_ocr]` quando OCR via LM Studio é usado
- `[ocr_backend_unavailable]` no output se nenhum backend disponível (nenhum texto foi gerado)
- `[low_ocr_quality]` se ao menos um backend rodou mas nenhum atingiu threshold de qualidade
- Log `[ocr_selection]` por página: `score_local`, `score_vl`, `backend`, `motivo`
