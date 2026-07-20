## 1. Caracterização e testes do gate de despacho

- [x] 1.1 Revisar os contratos atuais de `run_collect_stage()`, `DataExtractorApp`, `SkillDispatcher`, registro de skills e testes relacionados, confirmando os pontos mínimos de injeção para fake dispatcher e fake LLM client.
- [x] 1.2 Adicionar testes determinísticos para Markdown `ready/approved` com skill registrada e para os descartes `needs_review`, `unroutable` e `REVISAR_MANUAL`, verificando chamadas e ausência de chamadas ao LLM.
- [x] 1.3 Adicionar testes que comprovem que `skill_key` ausente não é derivado de `document_type`, que identificadores sem `extr-` não são corrigidos e que skill não registrada é rejeitada de forma controlada.

## 2. Despacho seguro da nova esteira

- [x] 2.1 Implementar em `run_collect_stage()` o parse defensivo e o gate estrito `status == ready`, `review_status == approved` e `skill_key` explícito iniciado por `extr-`.
- [x] 2.2 Remover do caminho da nova esteira a resolução por `routing.map`, a derivação por `document_type` e a prefixação automática, preservando o comportamento legado fora desse caminho.
- [x] 2.3 Encaminhar o identificador literal ao runtime canônico e tratar falhas esperadas de skill/arquivo por item, com log auditável e continuidade do lote sem chamada ao LLM.

## 3. Caminho explícito e compatibilidade legada

- [x] 3.1 Adicionar a `run_extraction()` um parâmetro opcional por palavra-chave para o caminho real de entrada, usando-o diretamente quando fornecido e preservando a busca atual por `input_filename` quando ausente.
- [x] 3.2 Alterar `run_collect_stage()` para passar o caminho exato do Markdown encontrado no staging junto aos argumentos legados compatíveis.
- [x] 3.3 Adicionar testes com arquivos homônimos que comprovem a precedência do caminho explícito e testes para `run_extraction(bundle_id, input_filename)` sem o novo argumento.

## 4. Validação e persistência segura do resultado

- [x] 4.1 Validar localmente o payload retornado por `generate_structured()` contra o schema carregado do `schema_ref` retornado pelo dispatcher, antes de abrir o destino para escrita.
- [x] 4.2 Implementar falha controlada para payload inválido, registrando erros de schema, não persistindo/truncando resultado válido e não emitindo conclusão bem-sucedida.
- [x] 4.3 Adicionar testes com fake LLM para resposta válida persistida, resposta inválida não persistida e preservação de resultado anterior diante de validação inválida.

## 5. Verificação final

- [x] 5.1 Executar `openspec validate add-safe-normalized-markdown-extraction-dispatch --strict` e corrigir qualquer inconsistência dos artefatos.
- [x] 5.2 Executar `openspec validate --all --strict` e confirmar que todas as specs do repositório permanecem válidas.
- [x] 5.3 Executar `pytest -q apps/data-processing/tests` sem chamadas reais ao Gemini e corrigir regressões relacionadas ao change.
- [x] 5.4 Executar `git diff --check` e `git status -sb`, documentando alterações e riscos restantes sem criar commit ou fazer push.
