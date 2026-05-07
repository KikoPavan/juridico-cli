## Why

O heurístico `_needs_ocr()` em `convert_pdf_to_md.py` decide se uma página precisa de OCR baseando-se apenas em contagem de caracteres e taxa de imprimíveis — sem considerar que o texto extraído pode ser inteiramente boilerplate (cabeçalhos institucionais, rodapés, numeração "Fls. N"). Isso faz com que páginas cujo conteúdo real está escaneado sejam incorretamente classificadas como "texto nativo disponível", pulando o OCR e gerando Markdown vazio ou incompleto.

## What Changes

- Adicionar função `_is_boilerplate(text)` em `convert_pdf_to_md.py` que identifica padrões recorrentes de boilerplate em documentos jurídicos brasileiros (cabeçalho de tribunal, numeração de fls., rodapé institucional).
- Modificar `_needs_ocr(text)` para descontar o texto boilerplate antes de avaliar se o volume de texto nativo é suficiente para dispensar OCR.
- Adicionar testes unitários para `_is_boilerplate` e o comportamento atualizado de `_needs_ocr`.

## Capabilities

### New Capabilities

*(nenhuma nova capability)*

### Modified Capabilities

- `pdf-to-md`: O requisito de detecção de páginas escaneadas é ampliado — além de contagem de caracteres e taxa de imprimíveis, o sistema DEVE descartar texto boilerplate antes de decidir pelo OCR. A spec existente em `openspec/specs/pdf-to-md/spec.md` precisará de um requisito delta para a heurística de boilerplate.

## Impact

- `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` — funções `_needs_ocr`, `_assess`, nova `_is_boilerplate`.
- `platform/skills/pdf-to-md/scripts/test_ocr_path.py` ou novo arquivo de teste unitário.
- `openspec/specs/pdf-to-md/spec.md` — delta de requisito para heurística de boilerplate.
