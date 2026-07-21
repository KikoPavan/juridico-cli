## Context

O teste operacional de `Processo.pdf` revelou que, mesmo com a absorção de `separador_de_evento` funcionando, a consolidação ainda depende dos descritores do LLM que variam entre execuções:

1. Fragmentos contíguos com mesma identidade forte não são unidos — `_merge_partial_pieces` só une peças sobrepostas (overlap de janelas), não peças contíguas.
2. `nao_classificado` gerado por `_fill_uncovered_pages` entre fragmentos do mesmo evento não é absorvido pela peça específica adjacente.
3. Tipos da família de decisão (`despacho`, `despacho_decisao`, `decisao_interlocutoria`) variam entre janelas e não são normalizados para um valor estável.
4. A página 3 pode aparecer em três representações parciais diferentes, embora o Markdown original a identifique invariavelmente como separador estrutural do evento 1 antes de `INIC1`.

## Goals / Non-Goals

**Goals:**
- Coalescer fragmentos contíguos com mesma identidade forte (process_number, event, document_code).
- Absorver `nao_classificado` adjacente `à` peça específica com mesma identidade de locator.
- Normalizar tipo documental da família de decisão usando routing_map e schema.
- Três execuções de `Processo.pdf` produzem deterministicamente 7 peças com cobertura 1-35 integral, tipos canônicos, sem lacunas ou duplicação. O event separator da página 3 (evento 1) é absorvido na peça `peticao_inicial` (evento 1), conforme design do sistema. Páginas 19-21 (órfãs, sem `process_number` no locator) são preservadas como `nao_classificado` autônomo.

**Non-Goals:**
- Não alterar schemas, DOC_TYPE_MAP, timeout Gemini, extração por blocos.

## Decisions

### 1. Etapa de coalescência após overlap merge e `_fill_uncovered_pages`

A ordem da consolidação passa a ser:

```
traduzir páginas locais (já existe)
→ absorver separadores (já existe)
→ reconciliar overlap (já existe)
→ fill_uncovered_pages (já existe)
→ canonicalizar separadores estruturais pela origem (NOVO)
→ coalescer fragmentos de mesma identidade forte (NOVO)
→ gerar IDs finais (já existe)
```

A coalescência é pós-processamento determinístico sobre o resultado do merge. Não interfere com a lógica de overlap.

### 1.1. Canonicalização independente do rótulo do LLM

Após reunir as respostas parciais, o estágio indexa o trecho original de cada `judicial_locator`. Uma página ou intervalo é evidência de separador quando possui `kind=event_separator` ou cabeçalho estrutural de página de separação no Markdown. O intervalo é incorporado à peça específica seguinte somente quando:

- o locator do separador possui `process_number` confiável;
- separador e documento seguinte possuem o mesmo processo e evento;
- o locator seguinte possui `document_code` válido e ele coincide com a identidade da peça específica;
- eventual código específico do separador não conflita;
- existe exatamente uma peça específica candidata no limite.

A operação remove qualquer representação autônoma do separador, estende o início da peça seguinte e produz anchors estruturais estáveis. Se o LLM já incluiu a página na peça seguinte, a mesma canonicalização é idempotente. Por isso `separador_de_evento`, `nao_classificado` e inclusão direta convergem para o mesmo intervalo 3-18 sem depender desses rótulos.

Grupos contíguos completos de locators com processo, evento e código fortes também fixam os limites da peça documental e consolidam fragmentos parciais de identidade idêntica. Fragmentos `nao_classificado` totalmente contidos nesses grupos são removidos; páginas fora de um grupo forte não são afetadas. Isso estabiliza, no caso real, os eventos 20 (29-32) e 32 (33-35) mesmo quando uma janela parcial desloca a fronteira.

Páginas órfãs 19-21 não satisfazem a primeira condição: seus locators não possuem `process_number`. Elas permanecem como `nao_classificado` autônomo.

### 2. Critérios de coalescência

Dois fragmentos A (à esquerda) e B (à direita) são coalescidos quando TODAS as condições são satisfeitas:

**Condição de adjacência:** `A.pages_end + 1 == B.pages_start`

**Condição de identidade (uma das):**
- (a) B é `nao_classificado` E A tem identidade forte E locators de B são compatíveis com A
- (b) Mesmo event, mesmo document_code, mesmo process_number (todos não-None e iguais)
- (c) Mesmo tipo normalizado E mesmo event E mesmo document_code (para variantes como `despacho`/`despacho_decisao`)

### 3. Normalização de tipo na família de decisão

`despacho_decisao` não existe no schema do output nem no routing_map. Tipos da família de decisão (`despacho`, `decisao`, `decisao_interlocutoria`, `despacho_decisao`) são consolidados para o valor mais específico dentre os fragmentos coalescidos que seja aceito pelo schema, priorizando a classificação que consta em mais páginas ou que o código documental sugere.

### 4. `nao_classificado` absorvível

`nao_classificado` gerado por `_fill_uncovered_pages` ou pelo LLM é absorvido pela peça adjacente à esquerda quando:
- É contíguo (`A.pages_end + 1 == B.pages_start`)
- A tem identidade forte (event, document_code, process_number não-None)
- Cada página de B tem locator compatível com a identidade de A (mesmo event; mesmo document_code quando presente)

## Risks / Trade-offs

- **Fusão excessiva de fragmentos**: Mitigado pela exigência de forte identidade — só coalesce quando event, code e process são idênticos OU B é `nao_classificado` com locator compatível.
- **Perda de peças genuinamente distintas**: Eventos diferentes ou códigos diferentes nunca coalescem. Cabeçalhos incompatíveis também bloqueiam a fusão.
- **Determinismo vs LLM**: A coalescência é determinística para os mesmos descritores de entrada. Variação na geração LLM entre eventos adjacentes ainda pode produzir diferenças na fronteira entre eventos.
- **Falso separador textual**: Mitigado pela exigência conjunta de identidade judicial original e peça específica seguinte única; texto estrutural isolado não autoriza absorção.
