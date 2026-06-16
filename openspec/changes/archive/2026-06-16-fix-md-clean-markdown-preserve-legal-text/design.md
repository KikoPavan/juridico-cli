## Context

A skill `md-clean-markdown` opera exclusivamente em `platform/skills/md-clean-markdown/scripts/clean_markdown.py`. Ela recebe arquivos `.md` gerados por `pdf-to-md` (que pode produzir line endings `\r\n` em PDFs gerados em Windows) e aplica limpeza de formatação Markdown.

Dois bugs confirmados no output real:

**Bug 1 — Corrupção de acentos** (`ÃO` → `ÁO`):
A função `_fix_trailing_whitespace` remove apenas o `\n` final da linha (`body = line[:-1]`), deixando o `\r` no corpo quando o input usa `\r\n`. O `\r` residual permanece na string processada e é gravado no arquivo de saída. Quando esse arquivo é lido por ferramentas subsequentes (ou pelo próprio Python em modo texto sem `newline` explícito), o `\r` pode provocar comportamento de carriage-return no terminal — mas o mecanismo mais provável de corrupção de acentos é diferente: se o arquivo fonte usa codificação Latin-1/CP1252 (produzida por OCR em PDFs antigos) e é lido com `errors="replace"`, os bytes `0xC3` de `Ã` em Latin-1 podem ser confundidos com o início de uma sequência UTF-8 multi-byte, levando à substituição. A investigação obrigatória na Task 1 determinará qual hipótese se confirma.

**Bug 2 — Heading colado à linha anterior** (`texto# HEADING`):
Quando o `pdf-to-md` gera linhas com `\r\n`, o `\r` residual na saída do cleaner causa que, em terminais que interpretam `\r` como retorno de cursor, a linha seguinte (o heading) sobrescreva visualmente o fim da linha anterior — produzindo `DE CERQUEIRA CÉSAR – SP# DECLARATÓRIA` na visualização. Alternativamente, o `pdf-to-md` pode ter emitido o heading embutido no meio da linha (sem `\n` antes do `#`), e o cleaner não detecta nem corrige esse padrão.

## Goals / Non-Goals

**Goals:**
- Normalizar `\r\n` → `\n` na entrada antes de qualquer processamento de linha.
- Garantir que caracteres Unicode internos (acentos, cedilha, etc.) não sejam alterados por nenhuma operação do pipeline.
- Detectar e separar headings Markdown (`# ...`) embutidos no meio de linhas (padrão `texto# HEADING`), inserindo `\n` antes do `#`.
- Adicionar testes de regressão cobrindo todos os padrões reais corrompidos documentados nesta change.
- Atualizar `cleaning_rules.md` e `output_contract.md` com as proibições absolutas e novos critérios.

**Non-Goals:**
- Não alterar lógica de pdf-to-md, md-frontmatter-yaml, stage_router.py, RAG, schemas jurídicos.
- Não alterar llm_registry.yaml, skill_registry.yaml, CLAUDE.md ou pyproject.toml.
- Não normalizar Unicode (NFC/NFD) — preservar a forma original do texto do PDF.
- Não reescrever conteúdo textual por critério semântico.

## Decisions

**D1 — Normalizar line endings na entrada (não no output)**
Converter `\r\n` → `\n` e `\r` isolado → `\n` imediatamente após `raw_text = input_path.read_text(...)`, antes de `splitlines(keepends=True)`. Alternativa descartada: normalizar por linha dentro de `_fix_trailing_whitespace` — exigiria refatoração maior e misturaria responsabilidades.

**D2 — `_fix_embedded_headings`: nova função pré-pipeline**
Antes das regras de limpeza por linha, aplicar uma passagem que detecta padrões `\S# ` (não-whitespace seguido de `# `) dentro de linhas e os divide em duas linhas. Isso garante que headings embutidos virem linhas independentes antes das demais regras serem aplicadas. Aplicar após `_extract_code_blocks` (blocos de código ficam protegidos).

**D3 — Nenhum Unicode normalization**
O pipeline não aplicará `unicodedata.normalize()` em nenhuma hipótese. A forma original (NFC ou NFD) do texto é preservada integralmente. A causa raiz da troca de acentos deve ser isolada e corrigida cirurgicamente — se for encoding de leitura, ajustar apenas o `errors` parameter; se for outro componente do CLI de data-processing, isolar ali.

**D4 — Testes de regressão como fixtures de texto literal**
Os testes novos usarão strings literais com os exemplos reais, não arquivos de fixture do disco — para que o teste seja autossuficiente e detecte regressões independentemente dos arquivos `var/`.

## Risks / Trade-offs

- [Risco] A causa raiz da corrupção de acentos pode estar no CLI de `apps/data-processing`, fora do escopo desta change → Mitigação: a Task 1 inclui investigação isolada com `clean_markdown.py` direto (não via CLI) para confirmar se o bug se reproduz ali.
- [Risco] Inserir `\n` antes de `#` embutido pode cortar texto que usa `#` como caractere não-Markdown (ex.: referência legal `Art. #5`) → Mitigação: a heurística de detecção requer que o `#` seja seguido de espaço e texto (`# [A-Z]`), não qualquer `#`.
- [Risco] Normalização de `\r\n` pode afetar arquivos que deliberadamente usam CRLF → Aceitável: o output_contract especifica UTF-8 com `\n` — CRLF no output seria uma violação do contrato.
