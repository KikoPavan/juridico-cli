## Context

`platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` usa `_needs_ocr(text)` para decidir se uma página precisa de OCR. O critério atual é:

1. `len(text) < 50` → OCR
2. `_printable_ratio(text) < 0.6` → OCR
3. Caso contrário → texto nativo suficiente, sem OCR

Documentos jurídicos brasileiros frequentemente contêm cabeçalhos institucionais repetidos em todas as páginas ("TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO", "Foro Regional VII - Itaquera"), numeração de folhas ("Fls. 42", "fl. 15") e rodapés que são extraíveis como texto nativo. Essas strings podem ultrapassar o limiar de 50 chars mesmo em páginas cujo conteúdo real está integralmente escaneado, impedindo o OCR de ser acionado.

O problema afeta apenas `convert_pdf_to_md.py` (caminho PaddleOCR). O caminho Gemini em `stage_router.py` usa threshold diferente (`_SCANNED_THRESHOLD = 150`) e está fora do escopo desta change.

## Goals / Non-Goals

**Goals:**
- Adicionar `_is_boilerplate(text)` que identifica padrões de boilerplate recorrentes em documentos jurídicos brasileiros.
- Modificar `_needs_ocr(text)` para calcular o volume de texto efetivo descontando boilerplate antes de aplicar o limiar de caracteres.
- Garantir que o comportamento existente seja preservado para texto genuinamente rico (não-boilerplate).
- Adicionar testes unitários cobrindo os novos casos.

**Non-Goals:**
- Não alterar o motor de OCR (PaddleOCR) nem os parâmetros de renderização.
- Não alterar `stage_router.py` nem o caminho Gemini.
- Não implementar detecção de boilerplate por cross-page similarity (heurística apenas por padrão de texto por página).
- Não refatorar o pipeline como um todo.

## Decisions

**D1 — Detecção por regex estático, não por frequência entre páginas**

A detecção de boilerplate por frequência (contar quantas vezes uma linha aparece em outras páginas) exigiria acesso a todas as páginas já processadas — incompatível com o processamento sequencial página a página do pipeline atual. A alternativa de regex estático com padrões conhecidos do contexto jurídico brasileiro é suficiente, determinística e testável.

Alternativa rejeitada: cross-page frequency analysis → custo de memória O(N páginas × M linhas) e acoplamento entre páginas que o design atual não possui.

**D2 — Descontar boilerplate do texto efetivo, não ignorar a página**

`_is_boilerplate(text)` não retorna um booleano para a página inteira. Em vez disso, uma função auxiliar `_strip_boilerplate(text)` remove linhas identificadas como boilerplate e retorna o texto residual. `_needs_ocr` passa então o texto residual para avaliação de suficiência.

Isso preserva o comportamento correto para páginas mistas (boilerplate + conteúdo nativo real).

**D3 — Padrões de boilerplate como constante de módulo**

Os padrões regex ficam em `BOILERPLATE_PATTERNS: list[re.Pattern]` no topo do módulo, separados da lógica, para facilitar manutenção e extensão futura sem alterar o fluxo.

## Risks / Trade-offs

- **[Risco] Falso positivo no strip de boilerplate** — um padrão regex muito amplo pode remover conteúdo relevante que coincide com a forma de um cabeçalho. Mitigação: padrões ancorados (`^`, `$`) e curtos; revisão manual dos primeiros PDFs processados pós-deploy.
- **[Risco] Padrões incompletos no lançamento** — o conjunto inicial de padrões cobre os casos observados nos PDFs de homologação; novos tribunais/formatos podem exigir adições. Mitigação: os padrões são uma constante editável; ampliação não exige mudança arquitetural.
- **[Trade-off] Maior custo de OCR em alguns casos** — páginas que antes passavam com boilerplate agora podem acionar OCR. O impacto é esperado e desejável: o objetivo é recuperar conteúdo que estava sendo perdido.

## Migration Plan

Mudança interna a `convert_pdf_to_md.py`; não há migration de dados ou API pública. Basta substituir as funções afetadas e validar com os testes.
