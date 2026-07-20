## Context

`GeminiLLMClient.generate_structured` (`packages/shared-llm/gemini_client.py`) tenta, nessa ordem, para `extr-peticao-processo`: (1) chamada estruturada com `response_json_schema`; (2) fallback "livre" com o schema embutido no prompt, incluindo um retry de reparo; (3) `_execute_extraction_in_blocks`, que fragmenta o schema em blocos menores (`A, B, C, D, E1-E5`).

Evidência real em `var/artifacts/gemini-debug/` (execução de 2026-07-20, processo `4000153-37.2026.8.26.0136/SP`) mostra a etapa (1) falhando com `400 INVALID_ARGUMENT`. A inspeção de `peticao_processo.response_schema.sanitized.json` confirma a causa: o nó raiz do schema sanitizado contém

```json
"anyOf": [
  { "required": ["pedidos"] },
  { "required": ["pedidos_individualizados"] },
  { "required": ["fatos"] },
  { "required": ["fundamentos"] },
  { "required": ["valor_da_causa"] },
  { "required": ["parties"] }
]
```

— um idioma "ao menos um destes campos" do schema canônico (`platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json:149-156`). Cada branch é apenas `{"required": [...]}`, sem `type`. `_sanitize()` (`gemini_client.py:796-874`) só infere `type` para um nó quando ele tem `properties`/`items`, ou quando consegue extrair um `type` único a partir de subschemas de combinadores — não cobre o caso de um branch que só tem `required`. Todos os outros usos de `anyOf` no projeto (`packages/shared-schemas/defs/common.schema.json:20,179,219`) já têm `type` em cada branch, então esse é um caso isolado.

Isso força toda extração real desse caso pelo caminho (2), que é uma chamada única com o schema inteiro embutido no prompt — cara e sujeita a truncamento em documentos grandes (`fallback_parse_error.txt` mostra `JSONDecodeError: Unterminated string`). A etapa (3) só é acionada depois de duas tentativas mal-sucedidas em (2), tornando a escalada lenta e reativa em vez de previsível.

O requisito "Recursively Sanitize anyOf Branches" (`openspec/specs/gemini-schema-alignment/spec.md`), de uma correção anterior, já cobre a sanitização de chaves *dentro* de branches de `anyOf`, mas não resolve branches sem `type`. O próprio design daquela mudança registra que a hipótese de causa raiz nunca foi confirmada empiricamente — esta mudança confirma a causa com evidência de execução real e a corrige.

**Atualização pós-implementação (rodada 2, mesmo dia)**: a Decisão 1 abaixo (remover branches `anyOf` só com `required`) foi implementada e coberta por teste unitário, mas o teste operacional real com `extr-peticao-processo` **continuou reproduzindo `400 INVALID_ARGUMENT`** na chamada estruturada inicial. Isso confirma o risco já registrado na seção Risks/Trade-offs desta mesma versão do design ("pode existir uma segunda causa... não confirmada"): o schema completo real tem alguma outra incompatibilidade ou limite de complexidade com `response_schema` além do `anyOf` já corrigido. Sem acesso interativo à API para isolar a causa exata (não há `GEMINI_API_KEY` neste ambiente), a Decisão 3 abaixo resolve o problema no nível operacional exigido — eliminar o `400` de forma determinística — sem depender de identificar essa causa residual.

## Goals / Non-Goals

**Goals:**
- Eliminar o `400 INVALID_ARGUMENT` causado por branches de combinador (`anyOf`/`oneOf`/`allOf`) sem `type` no schema enviado ao Gemini.
- Fazer isso sem alterar o schema canônico da skill (`platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json`) nem enfraquecer a validação local pós-geração.
- Reduzir o tempo até a extração por blocos ser acionada quando o risco de truncamento da tentativa livre é alto, tornando a escalada determinística em vez de puramente reativa.
- Manter o caminho atual (chamada estruturada → fallback livre com retry → blocos) para os casos de baixo risco, sem regressão no comportamento já coberto por `peticao-block-fallback-robustness`.

**Non-Goals:**
- Não redesenhar a extração por blocos (`_execute_extraction_in_blocks`) em si — já coberta por `peticao-block-fallback-robustness`.
- Não alterar o schema canônico de nenhuma skill.
- Não introduzir uma nova ferramenta de geração estruturada (ex.: Outlines) — isso é escopo de outra mudança em andamento (`adopt-outlines-for-structured-schema-generation`).
- Não construir um estimador preciso de tokens de saída; a avaliação de risco é heurística e determinística, não um modelo de previsão.

## Decisions

### Decisão 1 — Remover branches "somente required" em vez de inventar `type`

Quando, após a sanitização recursiva, um branch de `anyOf`/`oneOf`/`allOf` resultar em um dicionário cuja única chave permitida presente é `required` (sem `type`, `properties`, `items`, `enum` ou `format`), esse branch é removido do schema enviado ao Gemini. Se todos os branches de um combinador forem removidos por esse motivo, a chave do combinador (`anyOf`/`oneOf`/`allOf`) é removida do nó pai.

**Alternativa considerada e rejeitada**: atribuir `type: "object"` automaticamente a esses branches (mesma lógica já usada para nós com `properties`/`items`). Foi descartada porque não há confirmação de que o dialeto de schema estruturado do Gemini aceita um branch de `anyOf` que declara `type: "object"` e `required`, mas nenhuma `properties` própria — o precedente já registrado no design da correção anterior (`openspec/changes/archive/.../design.md`) documenta que a hipótese do `anyOf` nunca foi validada empiricamente contra a API real, e forçar um `type` sem confirmação repete esse risco.

**Por que remover é seguro**: a validação local pós-geração (`_validate_offline`, usando `local_resolver.load_validator` contra o schema rico completo, chamada em `generate_structured` e em `DataExtractorApp.run_extraction`) já valida a resposta do Gemini contra o schema canônico completo — incluindo esse `anyOf` — antes de qualquer persistência. Remover o combinador apenas do schema *enviado* ao Gemini não remove a regra de negócio "ao menos um destes campos"; ela continua sendo aplicada depois, com o benefício adicional de que uma violação passa a gerar um erro de validação claro em vez de um `400 INVALID_ARGUMENT` opaco.

### Decisão 2 — Avaliação de risco de truncamento antes do fallback livre

Antes de executar a primeira chamada do fallback livre (`_try_single_fallback_call` inicial, `generate_structured` linha ~252), calcular um sinal determinístico de risco de truncamento a partir de dados já disponíveis no momento da chamada:
- tamanho em caracteres do Markdown de entrada (mesmo conteúdo usado para `_locate_pedidos_section`/recorte por blocos);
- quantidade de propriedades top-level requisitadas no schema (`top_properties_count`, já calculado em `generate_structured` linha 111) — um schema com muitas propriedades top-level tende a gerar uma resposta mais longa.

Se o risco for classificado como alto (limiares configuráveis, iniciando com os mesmos valores empíricos já usados no código, ex. o limiar de 12000 caracteres usado hoje em `is_truncated`), pular a tentativa livre inicial e o retry de reparo, e chamar `_execute_extraction_in_blocks` diretamente. Se o risco for baixo, manter o caminho atual sem alterações.

**Alternativa considerada e rejeitada**: manter a decisão reativa atual (só escalar para blocos depois de duas tentativas livres falharem). Rejeitada porque, para casos já conhecidos como grandes (o caso real documentado em `peticao-block-fallback-robustness`), isso desperdiça duas chamadas caras e lentas ao Gemini antes de chegar ao caminho que de fato funciona.

**Alternativa considerada e rejeitada**: estimar tokens de saída esperados via contagem de tokens do modelo. Rejeitada por complexidade desnecessária nesta correção — o objetivo é reduzir round-trips desperdiçados, não prever o resultado com precisão.

### Decisão 3 — Preflight de compatibilidade com response_schema antes de qualquer chamada

Adicionado após a confirmação operacional (rodada 2) de que a Decisão 1 sozinha não elimina o `400 INVALID_ARGUMENT` para o schema completo real. Em vez de continuar tentando identificar e corrigir, um a um, cada construção de schema que o dialeto de `response_schema` do Gemini rejeita — processo reativo e sem acesso à API para validar empiricamente cada hipótese —, `generate_structured` passa a executar um preflight determinístico **antes de tentar a chamada estruturada inicial**, avaliado unicamente a partir do schema sanitizado (`_assess_response_schema_compatibility`, `packages/shared-llm/gemini_client.py`):

- tamanho em bytes do schema sanitizado (JSON serializado);
- quantidade de propriedades top-level;
- quantidade total de nós de objeto na árvore do schema (`_count_schema_nodes`).

Os limiares (`_SCHEMA_PREFLIGHT_SIZE_BYTES_THRESHOLD = 10000`, `_SCHEMA_PREFLIGHT_TOP_PROPERTIES_THRESHOLD = 10`, `_SCHEMA_PREFLIGHT_NODE_COUNT_THRESHOLD = 120`) foram calibrados medindo os dois grupos conhecidos operacionalmente: o schema completo sanitizado real (34.531 bytes, 25 propriedades, 370 nós — conhecido por falhar) e os nove schemas por bloco de `_execute_extraction_in_blocks` (no máximo 6.806 bytes, 6 propriedades, 75 nós — conhecidos por serem aceitos, por já produzirem extração operacional válida). Os limiares ficam entre os dois grupos, com margem para ambos os lados.

Quando o preflight considera o schema incompatível, `generate_structured` **pula tanto a chamada estruturada inicial quanto o fallback livre** e chama `_execute_extraction_in_blocks` diretamente, registrando um log que deixa explícito que a decisão foi tomada em preflight (por complexidade), e não por um erro retornado pela API — diferenciando esse caminho do log de erro reativo (`structured_call_error.txt`) que só é gravado quando uma chamada de fato falha.

**Alternativa considerada e rejeitada**: continuar investigando e corrigindo construções específicas incompatíveis (como a Decisão 1 fez para os branches `anyOf`), uma de cada vez, até o `400` desaparecer. Rejeitada porque, sem `GEMINI_API_KEY` neste ambiente para testar empiricamente cada hipótese contra a API real, esse processo é lento e não tem critério de parada claro; o preflight por complexidade resolve o critério operacional exigido (nenhum `400` no schema completo) imediatamente, com um custo aceitável (alguns schemas grandes, mas hipoteticamente compatíveis, podem ser desviados para blocos sem necessidade — ver Risks/Trade-offs).

**Alternativa considerada e rejeitada**: manter apenas a Decisão 2 (avaliação de risco de truncamento), que já teria o efeito colateral de pular o fallback livre para o schema completo — mas ela só age *depois* que a chamada estruturada inicial falha, então o `400 INVALID_ARGUMENT` ainda apareceria nos logs a cada execução, violando o critério operacional explícito de não exibir esse erro.

## Risks / Trade-offs

- [Risco] Remover o combinador `anyOf` do schema enviado ao Gemini pode, em teoria, reduzir a probabilidade de o próprio Gemini "respeitar" a regra "ao menos um campo" durante a geração (já que ela deixa de aparecer no schema estrutural). → Mitigação: a regra continua no prompt/schema completo usado no fallback livre (que embute o `schema` original, não o sanitizado) e é sempre validada localmente antes da persistência; uma violação vira falha controlada, não dado incorreto persistido.
- [Risco] O limiar de risco de truncamento é heurístico e pode classificar incorretamente um caso pequeno como "alto risco" (escalando para blocos desnecessariamente) ou um caso grande como "baixo risco" (mantendo o caminho lento). → Mitigação: reutilizar os mesmos limiares empíricos já validados no código existente (12000 caracteres) como ponto de partida, e manter o caminho de fallback livre com retry para todos os outros casos, evitando gerar uma via nova sem histórico de uso.
- [Risco] Empiricamente, pode existir uma segunda causa para o `400 INVALID_ARGUMENT` além dos branches de combinador sem `type` (o design da correção anterior já registra essa incerteza). → **Confirmado** no teste operacional da rodada 2: a Decisão 1 sozinha não eliminou o `400` para o schema completo real. → Mitigação aplicada: a Decisão 3 (preflight de compatibilidade) evita a chamada estruturada inicial para esse schema por completo, então o `400` nunca é exibido, independentemente de qual seja a causa residual exata. Identificar essa causa exata continua sendo valioso para eventualmente reabilitar `response_schema` no caminho principal, mas não é mais bloqueante para este change; `tests/test_gemini_schema_sanitizer.py::test_gemini_live_schema` (opt-in, requer `GEMINI_API_KEY`) permanece disponível para essa investigação futura.
- [Risco] Os limiares de preflight (tamanho/propriedades/nós) são heurísticos: um schema hipoteticamente compatível, mas grande, pode ser desviado para blocos sem necessidade (custo: mais chamadas, potencialmente mais lento); um schema pequeno mas com alguma outra construção incompatível ainda não modelada pode passar no preflight e falhar reativamente. → Mitigação: os limiares foram calibrados com margem folgada entre os dois grupos medidos (schema completo vs. blocos), e o caminho reativo (Decisão 2 + fallback livre → blocos) permanece como rede de segurança para schemas que passam no preflight mas falham na prática.

## Migration Plan

Mudança restrita a `packages/shared-llm/gemini_client.py`; não há dado persistido nem schema canônico migrado. Deploy é a atualização normal do pacote. Rollback é reverter o commit, já que não há estado externo dependente do novo comportamento.

## Open Questions

- Os limiares numéricos de risco de truncamento (tamanho de Markdown, contagem de propriedades) devem ficar hardcoded como hoje ou migrar para `platform/skill-runtime/llm_registry.yaml`? Esta mudança mantém os valores hardcoded, alinhados aos já existentes no arquivo, para não expandir escopo; a extração de configuração pode ser proposta separadamente se necessário.
