## Context

`apps/data-processing/orchestrator/stage_router.py` contém `_convert_one_hybrid`: uma implementação inline de conversão PDF→Markdown que usa Gemini OCR como fallback para páginas escaneadas. Essa função foi escrita antes da skill `pdf-to-md` ser validada e existe em paralelo a ela.

A skill `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` já implementa o mesmo comportamento — com PaddleOCR conforme `openspec/specs/pdf-to-md/spec.md` — e expõe interface CLI estável (`--input`, `--output`, `--engine`, `--no-markers`, `--verbose`, `--report`) com exit codes documentados (`0=ok 1=input_error 2=extract_error 3=write_error`).

O `converters/gemini_ocr/` é usado exclusivamente via `_convert_one_hybrid`; após a remoção, não haverá mais referências ao subpacote no caminho de conversão.

## Goals / Non-Goals

**Goals:**
- O estágio `convert` de `data-processing` delega a conversão PDF→Markdown à skill `pdf-to-md` sem duplicar lógica.
- Remover `_convert_one_hybrid` e a dependência de Gemini OCR no path de conversão.
- Manter a interface externa do CLI (`data-processing convert`) inalterada.

**Non-Goals:**
- Não alterar `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py`.
- Não refatorar o runtime de skills nem usar `skill_dispatcher.py` nesta mudança.
- Não modificar outros estágios do pipeline (`clean`, `analyze`, etc.).
- Não remover `converters/gemini_ocr/` se ainda houver dependências externas ao `stage_router`.

## Decisions

### Decisão: Invocação via subprocess

**Escolha:** `stage_router.py` invoca o script da skill via `subprocess.run(["uv", "run", "python", "<path>/convert_pdf_to_md.py", "--input", ..., "--output", ...])`.

**Rationale:** A skill é tratada como unidade com interface CLI própria. Subprocess:
- Respeita o boundary skill/módulo sem criar acoplamento de import Python entre módulos
- Usa os exit codes já definidos (`0/1/2/3`) para tratamento de erro sem parsing de traceback
- É consistente com como outros scripts de skill já são invocados em `stage_router.py` (ex: `run_segmentador_stage`)

**Alternativa descartada: import direto** — importar `build_markdown` e funções internas do script quebraria o boundary e acoplaria `data-processing` à estrutura interna da skill, tornando refatorações na skill impactantes no módulo funcional.

### Decisão: Caminho do script resolvido por `Path(__file__)`

O caminho para `convert_pdf_to_md.py` é resolvido em runtime a partir de `Path(__file__)` do `stage_router.py`, navegando até a raiz do projeto e então `platform/skills/pdf-to-md/scripts/`. Isso evita hard-coding absoluto e funciona em qualquer ambiente onde o projeto esteja clonado.

### Decisão: Remover `converters/gemini_ocr/` do path de conversão

Após remoção de `_convert_one_hybrid`, o subpacote `converters/gemini_ocr/` fica sem referências no estágio de conversão. Ele deve ser removido junto, evitando código morto. O subpacote `converters/markdown_engine/` (Engine/EngineIO) que coordena a iteração de arquivos permanece — é ele que chama a função de conversão por arquivo.

## Risks / Trade-offs

- **[Risco] Overhead de subprocess por PDF** → O custo de start de processo Python é absorvido pelo tempo de OCR (dominante). Para volumes altos, o impacto é negligível. Mitigação: monitorar em batches grandes; se necessário, extrair função pública do script em mudança futura.
- **[Risco] `uv` não disponível no PATH** → Usar `sys.executable` como fallback (`[sys.executable, "<path>/convert_pdf_to_md.py", ...]`) em vez de `uv run`. Mitigação: validar em `tasks.md`.
- **[Risco] `converters/gemini_ocr/` pode ter dependências não mapeadas** → Grep confirma que só `_convert_one_hybrid` importa o subpacote. Remoção é segura.

## Migration Plan

1. Substituir `_convert_one_hybrid` em `stage_router.py` por função `_convert_via_skill(pdf_path, out_md)` que invoca o script via subprocess.
2. Remover imports de `gemini_ocr` e `fitz`/`pdf2image` no path de conversão.
3. Remover subpacote `converters/gemini_ocr/`.
4. Executar pipeline end-to-end com PDF de teste para validar saída.
5. Rollback: restaurar `_convert_one_hybrid` e imports via git revert.
