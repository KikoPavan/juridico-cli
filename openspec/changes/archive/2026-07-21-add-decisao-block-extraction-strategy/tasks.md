## 1. Confirmar contratos canônicos

- [x] 1.1 Revisar `platform/skills/extr-decisao-processo/SKILL.md`, os dois schemas em `assets/`, o dicionário de campos e `scripts/validate_output.py`, sem editar arquivos `*.schema.json`.
- [x] 1.2 Confirmar em `routing_map.yaml` e `skill_registry.yaml` que somente `decisao`, `decisao_interlocutoria`, `sentenca` e `despacho` estão no escopo operacional do bundle, mantendo `document_type="decisao_processo"` no payload.
- [x] 1.3 Registrar o baseline dos testes direcionados de seleção, preflight/sanitização e persistência segura antes da alteração.

## 2. Implementar a estratégia de decisão

- [x] 2.1 Adicionar `DecisaoBlockStrategy` em `packages/shared-llm/block_strategies.py` com blocos exclusivos de identificação, relatório, fundamentação, conclusão decisória e cumprimento.
- [x] 2.2 Construir schemas parciais por allowlist das propriedades canônicas, validar cada resposta aplicável e impedir que propriedades de petição ou contestação entrem no merge.
- [x] 2.3 Implementar prompts específicos de decisão que preservem trechos literais, partes e referências no campo permitido pertinente, sem criar propriedades inexistentes no schema.
- [x] 2.4 Implementar fallback determinístico por bloco, com listas vazias/omissão somente quando permitidas, sem inventar fundamentos, dispositivo, determinações, prazos ou obrigações e com log explícito por bloco.
- [x] 2.5 Preservar anchors usando somente `judicial_locator`, marcador de página ou folha real aplicável; rejeitar `"[]"`, vazio, número fictício e locator inválido sem alterar o comportamento legado de petição/contestação.
- [x] 2.6 Consolidar somente chaves de `schema.properties`, validar o JSON completo com resolução local de refs antes do retorno e levantar erro para impedir persistência quando inválido.
- [x] 2.7 Registrar `extr-decisao-processo: DecisaoBlockStrategy` em `BLOCK_STRATEGIES`, sem alterar o preflight Gemini, a forma das chamadas ou os registros existentes.

## 3. Cobrir comportamento com fake client

- [x] 3.1 Testar que decisão seleciona `DecisaoBlockStrategy`, enquanto petição e contestação continuam selecionando suas classes atuais e bundle desconhecido continua falhando de forma controlada antes de chamar Gemini.
- [x] 3.2 Testar os cinco subconjuntos de campos e confirmar que o resultado de decisão não contém campos exclusivos de petição/contestação nem qualquer propriedade fora do schema.
- [x] 3.3 Testar preservação de `judicial_locator`, quotes e `page_marker` real, incluindo rejeição de `"[]"`, vazio e default fictício.
- [x] 3.4 Testar fallback de cada bloco, logs de degradação e ausência de conteúdo jurídico inventado.
- [x] 3.5 Testar que bloco inválido não entra no merge, que consolidação inválida levanta erro e que nenhum JSON inválido é persistido.
- [x] 3.6 Testar com o validador oficial que um payload consolidado válido de decisão é aceito.

## 4. Executar validações obrigatórias

- [x] 4.1 Executar `uv run pytest -q apps/data-processing/tests`.
- [x] 4.2 Executar `uv run pytest -q tests/test_gemini_schema_sanitizer.py`.
- [x] 4.3 Executar `uv run pytest -q tests/test_block_extraction_strategy_selection.py`.
- [x] 4.4 Executar `uv run ruff check apps platform packages tests`.
- [x] 4.5 Executar `git diff --check`.
- [x] 4.6 Executar `openspec validate --all --strict`.

## 5. Preparar e executar validação operacional real

- [x] 5.1 Confirmar que `var/output/processed/DESPACHO-DECISÃO_evento_32.md` continua sendo uma decisão normalizada, com `judicial_locator`, e registrar seu hash antes do teste.
- [x] 5.2 Com `GEMINI_API_KEY` configurada, executar `PYTHONPATH=apps/data-processing/src:packages/shared-llm uv run python -m data_processing.cli extract --bundle extr-decisao-processo --input 'DESPACHO-DECISÃO_evento_32.md'`.
- [x] 5.3 Executar `uv run python platform/skills/extr-decisao-processo/scripts/validate_output.py --input 'var/output/extracted/result_extr-decisao-processo_DESPACHO-DECISÃO_evento_32.json'` e inspecionar a preservação dos locators e trechos literais.
- [x] 5.4 Manter a change não arquivada se o teste operacional real não tiver sido executado e aprovado; não fazer commit nem push.
