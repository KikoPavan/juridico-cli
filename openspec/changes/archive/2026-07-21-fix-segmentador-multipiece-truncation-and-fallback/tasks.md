## 1. Baseline e contrato interno

- [x] 1.1 Registrar testes de caracterização do caminho curto atual e confirmar, com fake client, o contrato unitário de `run_segmentador_stage` antes da refatoração.
- [x] 1.2 Extrair uma operação interna de segmentação por arquivo que mantenha frontmatter, hash, origem, `process_group_id`, locators e nomes de artefato isolados.
- [x] 1.3 Implementar `segmentacao_lote.json` para múltiplas origens ou falhas isoladas, preservar o retorno unitário bem-sucedido e adaptar o chamador para consumir somente envelopes `success` sem misturar processos.

## 2. Preflight e particionamento do segmentador

- [x] 2.1 Implementar inventário determinístico de caracteres, páginas, marcadores e sinais estruturais, com limiares configuráveis de alto risco de truncamento.
- [x] 2.2 Implementar janelas baseadas em páginas/marcadores reais, posições absolutas e sobreposição mínima controlada, rejeitando cortes quando a origem não fornecer limites verificáveis.
- [x] 2.3 Manter chamada estruturada única para documentos pequenos e rotear documentos de alto risco somente para a estratégia interna de janelas.
- [x] 2.4 Garantir por teste que o segmentador não resolve nem executa `PeticaoBlockStrategy`, `ContestacaoBlockStrategy` ou `DecisaoBlockStrategy` e não é registrado como extrator.

## 3. Análise parcial e consolidação

- [x] 3.1 Executar chamadas compactas por janela com fake-client-friendly context contendo origem, intervalo e identidade judicial disponível.
- [x] 3.2 Normalizar e ordenar descritores parciais por posições reais, preservando processo, evento, código, locators, páginas e arquivo de origem.
- [x] 3.3 Implementar consolidação determinística de uma peça que cruza janelas, exigindo compatibilidade de intervalo, identidade documental e continuidade textual.
- [x] 3.4 Impedir merge de peças adjacentes distintas e rejeitar lacunas, sobreposições indevidas, páginas inexistentes ou conflitos de identidade.
- [x] 3.5 Validar contrato compacto e invariantes antes do recorte, materializar texto somente do Markdown original e validar o envelope canônico antes de promover qualquer saída final.

## 4. Fallback e falha segura

- [x] 4.1 Ampliar o fallback determinístico do segmentador para reconhecer múltiplas peças por mudança confiável de evento/código, cabeçalho ou início documental ancorado.
- [x] 4.2 Produzir estado controlado `needs_review` sem envelope final quando janelas, fronteiras, tipo ou consolidação não tiverem evidência suficiente.
- [x] 4.3 Isolar exceções no limite de cada arquivo para que falhas de chamada, parsing, fallback, materialização ou schema não interrompam os demais Markdown.

## 5. Diagnóstico operacional

- [x] 5.1 Substituir o diagnóstico global sobrescrevível por artefatos correlacionáveis em `var/artifacts/gemini-debug/`, com estágio, arquivo, tentativa, estratégia, timestamp e erro.
- [x] 5.2 Adicionar logs estruturados de páginas, caracteres, preflight, janelas, peças parciais, consolidação, validação e fallbacks sem registrar texto jurídico integral desnecessário.
- [x] 5.3 Testar que falhas de dois arquivos e múltiplas tentativas preservam diagnósticos distintos, incluindo erro de parsing `Unterminated string`.

## 6. Regressões automatizadas

- [x] 6.1 Cobrir diretório com três arquivos, consideração de todos eles e continuidade dos arquivos válidos quando um falha.
- [x] 6.2 Cobrir caminho curto, acionamento do caminho longo e ausência total de chamadas reais ao Gemini usando fake client.
- [x] 6.3 Cobrir documento multiparte, peça atravessando duas janelas, peças adjacentes distintas e intervalos sem lacunas/sobreposições indevidas.
- [x] 6.4 Cobrir preservação de `judicial_locator`, identidade/origem e rejeição de `page_marker` vazio, `"[]"` ou página inventada.
- [x] 6.5 Cobrir saída consolidada inválida sem materialização, fallback multiparte com evidência e revisão controlada sem evidência.
- [x] 6.6 Confirmar que todos os testes atuais de segmentação permanecem passando.

## 7. Validação e regressão operacional

- [x] 7.1 Executar `uv run pytest -q apps/data-processing/tests`.
- [x] 7.2 Executar `uv run pytest -q tests`.
- [x] 7.3 Executar `uv run ruff check apps platform packages tests` e `git diff --check`.
- [x] 7.4 Executar `openspec validate --all --strict`.
- [x] 7.5 Preparar fixture/procedimento separado para a regressão real com `Processo.pdf`, sem incluí-lo em testes unitários automáticos.
- [x] 7.6 Executar e registrar o teste operacional real com `Processo.pdf` antes de solicitar arquivamento; não arquivar, fazer commit ou push nesta mudança sem autorização posterior.
