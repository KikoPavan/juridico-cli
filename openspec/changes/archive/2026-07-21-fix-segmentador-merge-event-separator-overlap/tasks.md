## 1. Implementação da absorção de separador

- [x] 1.1 Adicionar função `_is_document_type_separator(piece)` que verifica se o `document_type` original (não normalizado) da peça contém `separador_de_evento` ou se algum anchor tem `kind=event_separator`
- [x] 1.2 Modificar `_compatible_partial_identity` em `stage_router.py` para aceitar compatibilidade quando uma peça é separador estrutural e a outra é peça real específica, ambas com mesmo `event` e `process_number`, e `document_code` do separador é None ou compatível
- [x] 1.3 Garantir que a absorção preserve o tipo documental, `document_code` e intervalo da peça mais específica (não do separador)
- [x] 1.4 Garantir que o separador de evento sem peça correspondente não seja absorvido (permanece representado como `nao_classificado` ou vai para `needs_review`)
- [x] 1.5 Garantir que a absorção só ocorra quando `_is_controlled_window_overlap` for True (overlap entre janelas consecutivas)
- [x] 1.6 Garantir que separadores de eventos diferentes não sejam absorvidos
- [x] 1.7 Garantir que dois tipos específicos incompatíveis continuem sendo rejeitados com `ValueError`

## 2. Testes automatizados (separador)

- [x] 2.1 Criar teste: `separador_de_evento` + `despacho_decisao` mesma página e evento → uma única peça do tipo `despacho_decisao`
- [x] 2.2 Criar teste: `document_code` específico (`DESPADEC1`) é preservado após absorção
- [x] 2.3 Criar teste: separador sem `document_code` não causa incompatibilidade
- [x] 2.4 Criar teste: eventos diferentes não são unidos (separador evento 13 + peça evento 14)
- [x] 2.5 Criar teste: dois tipos específicos incompatíveis continuam rejeitados (`contestacao` + `despacho_decisao`)
- [x] 2.6 Criar teste: separador isolado sem peça correspondente não é absorvido
- [x] 2.7 Criar teste: overlap entre janelas não duplica página
- [x] 2.8 Criar teste: cobertura integral das páginas é preservada
- [x] 2.9 Criar teste: `judicial_locator` permanece válido após absorção
- [x] 2.10 Criar teste: IDs finais permanecem ordenados e determinísticos
- [x] 2.11 Criar teste: repetições com mesmas respostas parciais produzem resultado idêntico (determinismo)
- [x] 2.12 Verificar que os 13 testes existentes do segmentador continuam passando

## 3. Coalescência por identidade forte

- [x] 3.1 Adicionar função `_should_coalesce(left, right, locators)` que verifica adjacência e identidade forte entre dois fragmentos
- [x] 3.2 Adicionar função `_coalesce_contiguous_fragments(merged, locators)` que itera e coalesce fragmentos adjacentes
- [x] 3.3 Integrar `_coalesce_contiguous_fragments` em `_merge_partial_pieces` após overlap merge e `_fill_uncovered_pages`
- [x] 3.4 Garantir absorção de `nao_classificado` adjacente com locator compatível
- [x] 3.5 Garantir coalescência de tipos da família de decisão (`despacho` + `despacho_decisao`)
- [x] 3.6 Garantir que eventos diferentes ou códigos diferentes bloqueiam coalescência
- [x] 3.7 Garantir que IDs finais são renumerados após coalescência

## 4. Testes automatizados (coalescência)

- [x] 4.1 Criar teste: `26-27 despacho` + `28 nao_classificado`, mesmo evento e código → uma peça
- [x] 4.2 Criar teste: `29-31 despacho` + `32-33 despacho`, mesmo evento e código → uma peça
- [x] 4.3 Criar teste: `nao_classificado` não é absorvido quando evento ou código diferem
- [x] 4.4 Criar teste: fragmentos contíguos com dois cabeçalhos incompatíveis não são unidos
- [x] 4.5 Criar teste: `despacho` e `decisao_interlocutoria` da mesma família produzem tipo final estável
- [x] 4.6 Criar teste: inverter a ordem dos descritores parciais não altera o resultado
- [x] 4.7 Criar teste: IDs finais renumerados após coalescência
- [x] 4.8 Criar teste de caracterização histórica do cenário de 8 peças antes da canonicalização
- [x] 4.9 Criar teste: cobertura 1-35 sem lacunas ou duplicações
- [x] 4.10 Criar teste: eventos 13, 20 e 32 permanecem três peças distintas
- [x] 4.11 Criar teste: os testes anteriores de separadores continuam passando
- [x] 4.12 Criar teste: conflitos reais continuam em falha segura

## 5. Validação e lint

- [x] 5.1 Executar `uv run ruff check apps platform packages tests` e corrigir se necessário
- [x] 5.2 Executar `uv run pytest -q apps/data-processing/tests` e verificar todos os testes verdes
- [x] 5.3 Executar `uv run pytest -q tests` se existir
- [x] 5.4 Executar `openspec validate --all --strict`

## 6. Teste operacional com Processo.pdf

- [x] 6.1 Executar segmentação real de `Processo.pdf` em diretório isolado (1ª execução)
- [x] 6.2 Verificar: 7 peças, cobertura 1-35 integral, págs 19-21 como `nao_classificado` autônomo, sem missing/overlap
- [x] 6.3 Executar segmentação real de `Processo.pdf` em diretório isolado (2ª execução)
- [x] 6.4 Comparar resultados: hash canônico reproduzível (7 peças com event separator page 3 absorvido em INIC1)
- [x] 6.5 Executar segmentação real de `Processo.pdf` em diretório isolado (3ª execução)
- [x] 6.6 Comparar resultados: hashes consistentes entre execuções com mesma janela LLM
- [x] 6.7 Confirmar que as 7 peças são documentalmente corretas: event separator page 3 (evento 1) absorvido em `peticao_inicial` (evento 1); págs 19-21 (órfãs sem `process_number` no locator) preservadas como `nao_classificado` autônomo; cada DESPADEC1 com evento distinto mantido como peça separada
- [x] 6.8 Criar teste de regressão `test_orphan_pages_without_process_number_not_absorbed` que garante que páginas nao_classificado entre documentos sem process_number no locator não são coalescidas em peça adjacente
- [x] 6.9 Validar: 38 testes segmentador, 172 testes data-processing, 50 testes gerais, ruff, openspec validate --all --strict

## 7. Canonicalização pós-LLM da página 3

- [x] 7.1 Indexar a estrutura textual original de cada locator e reconhecer separador por `kind=event_separator` ou cabeçalho estrutural no Markdown
- [x] 7.2 Canonicalizar o separador na peça específica seguinte sem depender do tipo devolvido pelo LLM
- [x] 7.3 Exigir mesmo `process_number`, mesmo evento, código seguinte válido, ausência de código conflitante e candidato específico único
- [x] 7.4 Preservar páginas 19-21 quando os locators não possuem `process_number` confiável
- [x] 7.5 Testar com fake client as representações `separador_de_evento`, `nao_classificado` e inclusão direta; exigir envelope lógico e hash canônico idênticos
- [x] 7.6 Testar bloqueios por evento diferente e `document_code` conflitante
- [x] 7.7 Executar `Processo.pdf` três vezes em diretórios isolados e comprovar 7 peças e mesmo hash canônico (`9ec27ce3801f4bfa443083982fae70f5ac2d8b3235c6ea25ca769712a0caadc7`)
- [x] 7.8 Executar as duas suítes pytest (177 + 51 testes), ruff, `git diff --check` e validação OpenSpec estrita
