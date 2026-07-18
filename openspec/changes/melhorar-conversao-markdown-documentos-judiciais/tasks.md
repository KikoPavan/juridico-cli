## 1. Normalização de ligaduras

- [ ] 1.1 Implementar em `LegalDocCleaner` a tabela explícita de ligaduras Unicode e o método idempotente `fix_typographic_ligatures()`.
- [ ] 1.2 Integrar a normalização de ligaduras antes de `fix_encoding()` no fluxo de limpeza, preservando os demais caracteres Unicode.
- [ ] 1.3 Adicionar testes unitários para todas as ligaduras requeridas, preservação de Unicode legítimo e idempotência.

## 2. Recomposição de linhas

- [ ] 2.1 Implementar a recomposição de palavras hifenizadas quando a continuação começar com letra minúscula.
- [ ] 2.2 Implementar a recomposição conservadora de linhas fragmentadas de prosa sem atravessar linhas vazias ou estruturas Markdown.
- [ ] 2.3 Integrar a recomposição antes da normalização estrutural em `md-clean-markdown`, isolando marcadores judiciais e blocos de código.
- [ ] 2.4 Adicionar testes unitários para hifenização, fragmentação de OCR, limites estruturais, hifens semânticos e idempotência.

## 3. Estruturação de páginas eproc/TJSP

- [ ] 3.1 Estender a análise de páginas de separação em `packages/shared-llm/judicial_locator.py` para extrair `event_title`, `date`, `user`, `user_role` e `sequence`, além dos campos já suportados.
- [ ] 3.2 Atualizar a serialização e o parsing de `[[judicial_locator: ...]]` para preservar os novos campos, a ordem canônica e o escape de valores.
- [ ] 3.3 Garantir que campos ausentes não sejam inferidos e que o texto exclusivo da página de separação não seja classificado como conteúdo jurídico útil.
- [ ] 3.4 Adicionar testes para páginas completas e parciais, round-trip do marcador, valores que exigem escape e separadores sem corpo jurídico.

## 4. Detecção e fallback OCR

- [ ] 4.1 Ajustar o critério de texto útil de páginas anexas para 30 caracteres após remover boilerplate e localizadores judiciais.
- [ ] 4.2 Implementar fallback OCR explícito para páginas dominadas por boilerplate ou localizadores, inclusive quando a decisão inicial de `_needs_ocr()` não solicitar OCR.
- [ ] 4.3 Incluir penalidade para conteúdo composto apenas ou predominantemente por localizadores na avaliação de qualidade pós-OCR.
- [ ] 4.4 Adicionar testes unitários para o limiar de 30 caracteres, fallback explícito, penalidade de localizadores e manutenção do fallback para imagem sem pré-processamento.
- [ ] 4.5 Executar o teste E2E do caminho PaddleOCR e verificar os modos `ocr_preprocessed`, `ocr_raw` e `low_ocr_quality` sem regressão na conversão de PDFs digitais.

## 5. Validação do documento completo

- [ ] 5.1 Implementar `check_document_has_content()` em `output_checks.py` para contar conteúdo após excluir frontmatter, marcadores judiciais, localizadores textuais e boilerplate, sem modificar o Markdown de entrada.
- [ ] 5.2 Tornar configurável o limiar de conteúdo útil, com valor padrão de 50 caracteres.
- [ ] 5.3 Integrar a validação após limpeza e frontmatter e antes da extração JSON, registrando `rejected: no_meaningful_content` e impedindo a chamada ao LLM quando necessário.
- [ ] 5.4 Adicionar testes para documento válido, vazio, apenas com localizadores, limiar customizado, imutabilidade da entrada e ausência de chamada ao extrator em rejeições.

## 6. Validação integrada e documentação

- [ ] 6.1 Adicionar fixture integrada com ligaduras, linhas fragmentadas, página de separação eproc/TJSP, página escaneada e documento composto apenas por localizadores.
- [ ] 6.2 Executar os testes das skills e do módulo de processamento de dados e corrigir regressões de preservação de marcadores, headings, listas, blocos de código e conteúdo jurídico.
- [ ] 6.3 Atualizar os `SKILL.md` de `pdf-to-md` e `md-clean-markdown` com os novos critérios, a ordem do pipeline, o limiar padrão e os motivos de rejeição.
- [ ] 6.4 Validar o fluxo completo PDF → Markdown limpo → validação de conteúdo e confirmar que somente documentos aceitos chegam à extração JSON.
