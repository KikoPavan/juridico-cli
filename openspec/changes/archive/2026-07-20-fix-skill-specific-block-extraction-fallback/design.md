## Context

`GeminiLLMClient.generate_structured` (`packages/shared-llm/gemini_client.py:136`) chama `_execute_extraction_in_blocks` (linha 465) em quatro pontos: preflight de compatibilidade incompatível (linha 257), erro na chamada estruturada inicial (linha 323), erro/truncamento no fallback livre (linhas 443/449), e detecção reativa de truncamento (linha 460). Em nenhum desses pontos o `bundle_id` da skill está disponível — `generate_structured` só recebe `messages` e `schema`. `_execute_extraction_in_blocks` define um dicionário fixo `blocks = {"A": [...], "B": [...], ..., "E5": [...]}` com nomes de campos de `extr-peticao-processo`, gera prompts específicos de petição (`FOCUS AREA FOR THIS BLOCK` menciona "pedidos", "tutela de urgência" etc.) e aplica `_apply_deterministic_fallback_e1_e2`, também específico de petição.

O chamador real, `DataExtractorApp.run_extraction` (`apps/data-processing/src/data_processing/extractor.py:69`), já resolve `bundle_id` via `SkillDispatcher.dispatch(bundle_id)` (linha 133) e tem esse valor disponível no momento em que chama `client.generate_structured(messages, schema=schema_json)` (linha 172) — falta apenas repassá-lo.

O schema de `extr-contestacao-processo` (`platform/skills/extr-contestacao-processo/assets/contestacao_processo.schema.json`) tem 10 propriedades top-level (`document_type`, `process_number`, `parties`, `representations`, `contestacao_identification`, `preliminares`, `merito`, `provas_e_requerimentos`, `pedidos_finais`, `anchors`) e `unevaluatedProperties: false` — qualquer campo de petição injetado é rejeitado na validação final, e é isso que já aconteceu no teste operacional (proteção funcionando, mas bloqueando toda extração por blocos de contestação).

O `page_marker` de âncora (`packages/shared-schemas/defs/common.schema.json:120`) é apenas `NonEmptyString`, sem `pattern`. Isso significa que um valor como `"[]"` passa na validação de schema mesmo sendo semanticamente inútil — o bug relatado não é pego por nenhuma validação existente, apenas observado manualmente no relatório.

## Goals / Non-Goals

**Goals:**
- Selecionar a estratégia de Extração por Blocos por `bundle_id` (repassado desde `extractor.py`), sem inferir a partir do conteúdo do schema ou de heurísticas implícitas.
- Preservar 100% do comportamento observável de `extr-peticao-processo` (specs já validadas em `peticao-block-fallback-robustness`).
- Implementar `extr-contestacao-processo` como segunda estratégia, gerando somente propriedades do schema de contestação.
- Falhar de forma controlada (exceção específica, sem persistência) para qualquer `bundle_id` sem estratégia registrada.
- Sanitizar `page_marker` de âncoras geradas/consolidadas pelas estratégias de blocos para nunca retornar `"[]"` ou vazio.

**Non-Goals:**
- Não implementar estratégias de blocos para `extr-decisao-processo`, `extr-procuracao`, `extr-mandato-processo`, `extr-cabecalho-processo` ou outros extratores nesta etapa — eles devem falhar de forma controlada.
- Não alterar o preflight de compatibilidade (`_assess_response_schema_compatibility`), o provider/modelo Gemini, nem qualquer arquivo `*.schema.json`.
- Não criar um novo runtime de despacho paralelo ao `SkillDispatcher`/`bundle_loader` — a seleção de estratégia de blocos é uma decisão interna de `packages/shared-llm`, não um mecanismo de roteamento de skills.
- Não resolver a causa-raiz do `page_marker: "[]"` além do escopo de blocos de petição/contestação (não se estende a outros pontos de geração de âncoras fora da extração por blocos).

## Decisions

### 1. Repassar `bundle_id` por parâmetro explícito, não inferir do schema
`generate_structured(self, messages, schema, *, bundle_id=None, **kwargs)` ganha um parâmetro nomeado opcional (mantém compatibilidade com o teste real de petição em `platform/skills/extr-peticao-processo/scripts/test_real_case_extraction.py`, que não passa `bundle_id`). `DataExtractorApp.run_extraction` passa `bundle_id=bundle_id` explicitamente, pois já o possui.

Alternativa descartada: inferir a skill a partir de `schema.get("$id")` ou `schema["properties"]["document_type"]["const"]`. Rejeitada porque o requisito 3 do change pede seleção por `bundle_id` **ou** `schema_ref` resolvido pelo `SkillDispatcher` — usar o `bundle_id` já disponível na chamada é mais direto, não exige acoplar `packages/shared-llm` ao formato interno de `document_type`, e evita ambiguidade se dois bundles compartilharem schema.

### 2. Estratégias como classes com interface comum, registradas em `BLOCK_STRATEGIES`
Extrair a lógica atual de `_execute_extraction_in_blocks` para `PeticaoBlockStrategy.execute(...)` e criar `ContestacaoBlockStrategy.execute(...)`, ambas implementando um método com a mesma assinatura (`client`, `messages`, `schema`, `debug_dir`, `max_tokens`, `base_dir`) e residindo em um novo módulo `packages/shared-llm/block_strategies.py`. `gemini_client.py` importa esse módulo e mantém:

```python
BLOCK_STRATEGIES = {
    "extr-peticao-processo": PeticaoBlockStrategy,
    "extr-contestacao-processo": ContestacaoBlockStrategy,
}
```

`generate_structured` substitui as quatro chamadas diretas a `self._execute_extraction_in_blocks(...)` por uma chamada a `self._dispatch_block_extraction(bundle_id, messages, schema, debug_dir, max_tokens, base_dir)`, que resolve a estratégia em `BLOCK_STRATEGIES` e levanta `BlockExtractionStrategyUnavailableError(bundle_id)` se ausente — **sem** cair em `PeticaoBlockStrategy` como padrão.

Alternativa descartada: `if/elif` direto em `_execute_extraction_in_blocks`. Rejeitada porque não escala de forma legível e dificulta o teste isolado de cada estratégia (o requisito mínimo do change já pede explicitamente o padrão de dicionário/registro).

### 3. `ContestacaoBlockStrategy` com blocos derivados do schema real, não espelhando petição
Blocos propostos para contestação (nomes internos livres, não normativos):
- `IDENT`: `document_type`, `process_number`, `parties`, `representations`, `contestacao_identification`.
- `PRELIMINARES`: `document_type`, `preliminares`.
- `MERITO`: `document_type`, `merito`.
- `PROVAS_PEDIDOS`: `document_type`, `provas_e_requerimentos`, `pedidos_finais`.

Cada bloco usa prompts derivados das seções 3–6 de `SKILL.md` (preliminares, mérito, provas/requerimentos, pedidos finais), sem citar nomes de partes/casos reais (mesma regra já aplicada a petição em `peticao-block-fallback-robustness`). Fallback determinístico local para contestação localiza cabeçalhos estruturais equivalentes (`PRELIMINAR`, `MÉRITO`/`NO MÉRITO`, `DOS PEDIDOS`/`PEDIDOS FINAIS`) e, na ausência de correspondência, retorna listas vazias — nunca conteúdo de petição nem texto fixo de caso real, seguindo o mesmo princípio já estabelecido para petição.

Alternativa descartada: reaproveitar `_apply_deterministic_fallback_e1_e2` genérico ajustando os prefixos de linha. Rejeitada porque a estrutura de contestação (preliminares/mérito/pedidos finais como três grupos distintos com semânticas próprias) não mapeia 1:1 para o modelo "pedidos legado + pedidos individualizados" de petição; forçar o reaproveitamento reintroduziria acoplamento ao formato de petição, exatamente o problema que este change corrige.

### 4. Falha controlada centralizada, sem try/except silencioso
`_dispatch_block_extraction` levanta a exceção **antes** de qualquer chamada ao Gemini. Como `extractor.py:172` (`response = client.generate_structured(...)`) não envolve essa chamada em `try/except`, a exceção propaga naturalmente e aborta antes do `json.dump` (linha 198), preservando a regra "nenhum JSON inválido é persistido" sem necessidade de lógica adicional de guarda em `extractor.py`.

### 5. Sanitização de `page_marker` compartilhada entre estratégias
Criar um helper `_sanitize_anchor_page_marker(anchors, current_page_hint)` reutilizado pelas duas estratégias na etapa de consolidação de cada bloco (mesmo ponto onde `_fix_anchors_and_properties` já roda). Regra: se `page_marker` estiver vazio, for `"[]"`/`"[ ]"` ou não contiver nenhum dígito, substituir pelo melhor marcador de página conhecido no momento da consolidação (mesma lógica de rastreamento de página corrente já usada em `_apply_deterministic_fallback_e1_e2`/`_extract_pages_from_markdown`) ou, na ausência de qualquer referência, por um valor de fallback controlado e auditável (nunca colchetes vazios).

Alternativa descartada: adicionar `pattern` ao `Anchor.page_marker` em `common.schema.json`. Rejeitada explicitamente pela restrição 4 do change ("não alterar schemas canônicos") — a correção fica inteiramente do lado do código de consolidação.

## Risks / Trade-offs

- [Risco] Extrair `PeticaoBlockStrategy` de um método de ~370 linhas pode introduzir regressão sutil de comportamento → Mitigação: refatoração mecânica (mover código, não reescrever lógica), suíte existente de `tests/test_gemini_schema_sanitizer.py` deve passar sem alteração de asserts para os casos de petição.
- [Risco] Fallback determinístico de contestação pode não cobrir todos os formatos reais de cabeçalho (`PRELIMINAR` vs `PRELIMINARES` vs `DAS PRELIMINARES`) → Mitigação: usar correspondência case-insensitive tolerante a variações comuns, e preferir lista vazia (dado ausente) a dado inventado, igual à política já adotada para petição.
- [Risco] Heurística de sanitização de `page_marker` pode mascarar um problema real de rastreamento de página em vez de expor a causa raiz → Mitigação: logar quando a sanitização substitui um valor recebido do LLM, para permitir auditoria posterior sem quebrar a validação.
- [Trade-off] Introduzir `bundle_id` como parâmetro opcional em vez de obrigatório mantém compatibilidade com chamadores legados/scripts de teste, mas significa que uma chamada sem `bundle_id` que precise de blocos também cairá em falha controlada (nenhuma estratégia resolvível) — aceito porque nenhum caminho de produção atual chama `generate_structured` sem meios de fornecer `bundle_id`.

## Migration Plan

Mudança é aditiva e não requer migração de dados. Ordem de implementação: (1) plumbing de `bundle_id`; (2) extração de `PeticaoBlockStrategy` com testes de regressão passando; (3) registro `BLOCK_STRATEGIES` e falha controlada; (4) `ContestacaoBlockStrategy`; (5) sanitização de `page_marker`; (6) validação end-to-end determinística com `validate_output.py`. Rollback trivial: reverter o commit da change, já que nenhum schema ou dado persistido é alterado.

## Open Questions

- Os nomes internos dos blocos de contestação (`IDENT`/`PRELIMINARES`/`MERITO`/`PROVAS_PEDIDOS`) são detalhe de implementação livre nas tasks, não normativo nos specs.
