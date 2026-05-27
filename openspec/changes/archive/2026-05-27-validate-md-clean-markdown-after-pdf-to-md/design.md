## Context

`md-clean-markdown` é a segunda etapa do pipeline: `pdf-to-md → md-clean-markdown → md-frontmatter-yaml → extração`.

O change anterior (2026-05-09) corrigiu o `PAGE_MARKER_RE` para reconhecer `[[Pág. N]]`, e a documentação da skill já reflete ambos os formatos. No entanto:

- `references/exemplo_entrada.md` usa conteúdo fictício em bloco de código, não o output real de `pdf-to-md`
- `references/exemplo_saida.md` é desalinhado do exemplo de entrada real
- `test_clean_markdown.py` testa apenas `_fix_trailing_whitespace` e preservação simples de marcadores, sem exercitar características reais (OCR artifacts, headings por linha curta, texto jurídico)
- `arquivo_escaneado_limpo.md` em `var/output/` está idêntico ao de entrada (copiado, não processado)
- `run_example.sh` gera seu próprio conteúdo sintético, não usuando output real de pdf-to-md

O risco é que a skill pode estar funcional para `[[Pág. N]]` mas não validada contra o caso de uso real que vai enfrentar em produção.

## Goals / Non-Goals

**Goals:**
- Substituir `exemplo_entrada.md` e `exemplo_saida.md` por conteúdo real de `var/output/pdf-to-md/arquivo_escaneado.md`
- Adicionar fixture de teste `tests/fixtures/pdf_to_md_sample.md` com recorte representativo de 2-3 páginas
- Adicionar teste E2E que executa `clean_markdown.py` + `validate_output.py --strict --source` contra a fixture
- Atualizar `test_clean_markdown.py` com casos que exercitem características reais (headings por linha, OCR artifacts, `fls.` boilerplate, texto jurídico)
- Regenerar `var/output/md-clean-markdown/arquivo_escaneado_limpo.md`
- Verificar `run_example.sh` com os novos exemplos

**Non-Goals:**
- Alterar `clean_markdown.py` — regex e lógica já foram corrigidos
- Alterar `pdf-to-md` ou seu formato de saída
- Alterar `md-frontmatter-yaml`
- Adicionar novas regras de limpeza
- Alterar `normalization_map.yaml` ou `cleaning_rules.md`

## Decisions

### Decisão 1 — Fixture inline vs arquivo separado

**Escolha:** Criar fixture como arquivo separado em `scripts/tests/fixtures/pdf_to_md_sample.md`.

Os testes atuais estão em `test_clean_markdown.py` (script autocontido). Adicionar uma fixture separada:
- Mantém o arquivo de teste focado em lógica, não em dados
- Permite que a fixture seja usada tanto por `test_clean_markdown.py` quanto por scripts de validação manual
- Segue o padrão de projeto (scripts têm seus próprios dados de teste)

### Decisão 2 — Recorte da fixture vs documento completo

**Escolha:** Usar recorte de 2 páginas do documento real com adaptação mínima.

O documento `arquivo_escaneado.md` tem 3 páginas e 188 linhas. Um recorte de 2 páginas é suficiente para exercitar:
- Marcadores `[[Pág. N]]` no início e no meio do documento
- OCR artifacts (`MARIAALVES DA SILVACONTRUCCI`, caracteres especiais)
- Headings gerados por heurística de linha curta (`# MARIAALVES...`)
- Texto jurídico real (matrícula de imóvel, qualificação de partes, averbações)
- Ruído tipográfico (linhas quebradas, espaços inconsistentes)

### Decisão 3 — Regenerar arquivos de output

**Escolha:** Executar `clean_markdown.py` contra a entrada real para regenerar `arquivo_escaneado_limpo.md`.

O arquivo atual em `var/output/` é cópia do original. Para que `validate_output.py --source` funcione e os exemplos sejam coerentes, é necessário regenerá-lo.

### Decisão 4 — Teste E2E como script separado ou integrado

**Escolha:** Adicionar função específica em `test_clean_markdown.py` que carrega a fixture, executa `clean_lines` e valida marcadores.

Isso mantém o teste rápido (sem spawn de processo) e focado no contrato de preservação. O teste E2E completo com processo separado fica para `run_example.sh`.

## Risks / Trade-offs

- **[Risco] Fixture pode ficar desatualizada se pdf-to-md mudar o formato de saída** → Mitigação: fixture é recorte explícito, documentado com origem. A atualização é manual e pontual.
- **[Risco] Testes podem falhar se conteúdo da fixture tiver caracteres especiais não-UTF-8** → Mitigação: fixture é UTF-8 validado; `clean_markdown.py` lê com `errors="replace"`.
- **[Risco] `run_example.sh` pode quebrar com exemplos maiores** → Mitigação: o script já usa `fpdf2` para gerar PDF sintético; manter exemplos de referência como documentação, não como única validação.
