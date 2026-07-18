## Context

O pipeline atual converte PDF → Markdown via `pdf-to-md`, depois limpa via `md-clean-markdown`, enriquece com frontmatter, e envia ao LLM para extração JSON. A exploração identificou 4 lacunas principais: (1) ligaduras tipográficas não são expandidas, (2) linhas quebradas por OCR/PDF não são recompostas, (3) páginas de separação eproc/TJSP não são estruturadas como metadados, (4) não há validação de conteúdo útil no documento completo antes da extração JSON. A OCR fallback existe mas a detecção de páginas escaneadas e a decisão de qualidade pós-OCR podem ser refinadas.

## Goals / Non-Goals

**Goals:**
- Expandir ligaduras tipográficas (ﬁ, ﬂ, ﬀ, ﬃ, ﬄ, etc.) no pipeline de limpeza
- Recompor linhas quebradas por hifenização e fragmentação de OCR/PDF
- Extrair e estruturar metadados completos de páginas de separação eproc/TJSP
- Validar conteúdo útil do documento completo antes da extração JSON
- Melhorar detecção e fallback OCR para páginas escaneadas

**Non-Goals:**
- Não criar nova skill ou módulo — as mudanças são incrementais nas skills existentes
- Não adicionar nova dependência externa (PaddleOCR já está)
- Não modificar o formato de saída JSON do extrator
- Não alterar o pipeline de segmentação jurídica (curador-relevancia)
- Não introduzir novo runtime ou motor de extração

## Decisions

1. **Ligaduras: normalização via tabela de substituição no cleaner, não no pdf-to-md**
   - As ligaduras são artefatos de encoding/fonte, não de extração PDF
   - Colocar em `LegalDocCleaner` (já existente em `clean_legal_docs.py`) como método `fix_typographic_ligatures()`, chamado antes de `fix_encoding()`
   - Alternativa rejeitada: fazer no pdf-to-md — misturaria responsabilidades de extração e limpeza

2. **Recomposição de linhas: novo estágio no md-clean-markdown, não no pdf-to-md**
   - A recomposição opera no Markdown já extraído, não na página PDF
   - Deve ocorrer antes da limpeza estrutural (headings, bullets) para não interferir
   - Heurísticas: linhas terminadas com hífen + quebra → unir sem hífen; linhas curtas sem pontuação final + linha seguinte começa com minúscula → unir
   - Alternativa rejeitada: fazer no pdf-to-md — misturaria extração com pós-processamento

3. **Estruturação eproc/TJSP: estender judicial_locator.py, não criar novo módulo**
   - O padrão TJSP eletrônico já é detectado, mas apenas extrai processo, evento, código e página
   - Estender para capturar: título do evento, data, usuário, papel do usuário, sequência
   - Formato de saída: `[[judicial_locator: process_number="...", event="...", event_title="...", date="...", user="...", user_role="...", sequence="..."]]`
   - Alternativa rejeitada: criar parser separado — o locator já é o ponto de integração

4. **Validação de documento completo: novo estágio opcional no pipeline, não no pdf-to-md**
   - Após a montagem do Markdown completo (pós frontmatter), verificar se o conteúdo útil excede threshold
   - Implementar como função `check_document_has_content()` em `output_checks.py`
   - Critério: remover todos os `[[judicial_locator: ...]]` e boilerplate, verificar se restam ≥ N caracteres úteis
   - Se falhar, marcar documento como `rejected: no_meaningful_content` em vez de enviar ao LLM
   - Alternativa rejeitada: fazer no pdf-to-md — a validação deve ocorrer após todo o pipeline de limpeza

5. **OCR fallback: refinar thresholds e adicionar fallback explícito para scanned_no_ocr**
   - Reduzir `MIN_CHARS_FOR_TEXT` de 50 para 30 para páginas anexas (scanned attachments)
   - Adicionar tentativa de OCR mesmo quando `_needs_ocr()` retorna False mas a página tem alta densidade de boilerplate
   - Melhorar `_ocr_post_quality_score()` com penalidade para linhas contendo apenas localizadores judiciais

## Risks / Trade-offs

- **[Performance]** Recomposição de linhas e normalização de ligaduras adicionam overhead de processamento. → Mitigação: operações O(n) com regex compiladas, impacto desprezível.
- **[Falso positivo]** Validação de conteúdo útil pode rejeitar documentos curtos mas legítimos (ex: despacho de 2 linhas). → Mitigação: threshold configurável, documentar valor default.
- **[Regressão]** Recomposição de linhas pode unir linhas que deveriam permanecer separadas (ex: endereços, listas). → Mitigação: heurísticas conservadoras (só unir quando linha termina com hífen + linha seguinte começa com minúscula, ou linha curta sem pontuação final + linha seguinte minúscula).
- **[OCR falso positivo]** Melhorar detecção de escaneados pode aumentar falsos positivos para PDFs com texto nativo de baixa densidade. → Mitigação: manter thresholds atuais como fallback, adicionar nova camada apenas para anexos identificados.

## Open Questions

- Qual o threshold mínimo de caracteres úteis para rejeitar um documento completo? Proposta inicial: 50 caracteres após remoção de locators e boilerplate.
- A recomposição de linhas deve ser configurável por tipo de documento? Inicialmente não — aplicar a todos os documentos.
