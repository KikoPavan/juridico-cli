## Context

`extr-peticao-processo` extrai dados via `GeminiLLMClient.generate_structured` (`packages/shared-llm/gemini_client.py`), compartilhado com `extr-contestacao-processo` e `extr-decisao-processo` (ambas funcionando bem hoje). O fluxo tem três camadas:

1. Chamada estruturada com `response_json_schema` (schema completo, sanitizado por `_normalize_schema`).
2. Fallback sem `response_schema` (schema completo, embutido no prompt).
3. Fallback por blocos (`_execute_extraction_in_blocks`), **hardcoded para os campos de `peticao_processo.schema.json`** (blocos `A`-`E5`), usado apenas por esta skill.

Evidência coletada em `var/artifacts/gemini-debug/` do run real de 2026-07-18 (`Petição Inicial_evento_1.md`, processo `4000153-37.2026.8.26.0136/SP`):

- A chamada 1 falhou com 400 `INVALID_ARGUMENT` (mensagem completa não persistida em disco — só logada via `logger.warning`, não capturada em arquivo).
- O fallback consolidado (camada 2) truncou em ~689 caracteres (`Expecting ',' delimiter... char 689`), apesar de `max_output_tokens=8192`.
- O bloco `E1` (camada 3) truncou em ~1107 caracteres (`Unterminated string... char 1107`), mesmo com `tokens_to_use=8192` explicitamente "garantido" para E1/E2 (linha 397 de `gemini_client.py` — na prática, idêntico ao default, não um aumento real).
- O bloco `E1`/`E2` usa recorte de páginas fixo `[13, 14, 15]` e instruções de prompt com "MINIMUM MANDATORY ITEMS" citando literalmente "Banco do Brasil" e o processo `0003453-81.2003.8.26.0136` — conteúdo de um caso real anterior, não uma instrução genérica de localização da seção "DOS PEDIDOS".
- O fallback determinístico local (`_apply_deterministic_fallback_e1_e2`) tem, como último recurso absoluto (quando a regex não encontra nenhuma linha "Requer-se/Protesta-se/Atribui-se"), um valor fixo hardcoded citando "nulidade da escritura pública de confissão de dívida" — texto de um caso real, não um indicador neutro de ausência de dados.

Truncamento severo em respostas pequenas (700-1100 caracteres, quando o conteúdo esperado de "pedidos" desta petição tem +3000 caracteres) com um orçamento de 8192 tokens é o padrão característico de modelos "thinking" do Gemini (`gemini-3-flash-preview`) quando `thinking_config` não é definido: o texto de raciocínio interno concorre pelo mesmo orçamento de `max_output_tokens` que a saída visível, podendo consumi-lo quase todo antes do JSON começar a ser escrito.

Adicionalmente, `GeminiLLMClient._normalize_schema._sanitize` recursa explicitamente em `properties` e `items`, mas devolve o conteúdo de `anyOf` **sem sanitização recursiva** (apenas copia a lista de subschemas resolvidos, não sanitizados). Isso é inconsistente com o resto da função e é candidato direto à causa do 400 na chamada 1: uma chave não suportada (ex.: `pattern`, `minLength`, `maxLength` vindas de defs compartilhadas como CPF/CNPJ) pode vazar para o Gemini de dentro de um branch `anyOf`, sem ser barrada pelo `_scan_deep` (que só bloqueia uma lista fixa de chaves estruturais, não essas).

## Goals / Non-Goals

**Goals:**
- Garantir que os blocos `E1` e `E2` de `extr-peticao-processo` completem sem truncamento para o caso real testado, sem ressalvas.
- Corrigir a sanitização de `anyOf` em `_normalize_schema` para eliminar uma causa concreta de incompatibilidade de schema com o Gemini.
- Tornar a localização da seção de pedidos/tutela genérica (busca por marcador estrutural do documento, não por número de página fixo) para que a skill não dependa de um caso específico.
- Eliminar conteúdo de caso real hardcoded do fallback determinístico de última instância.
- Preservar 100% do comportamento hoje funcional de `extr-contestacao-processo` e `extr-decisao-processo` (mesma `generate_structured`).

**Non-Goals:**
- Não alterar `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml`, OCR.
- Não alterar o comportamento ou specs de `extr-contestacao-processo`/`extr-decisao-processo` — apenas garantir ausência de regressão via testes existentes.
- Não redesenhar a arquitetura geral do pipeline de extração nem criar um mecanismo de blocos genérico reutilizável por outras skills (fora de escopo desta correção pontual).
- Não migrar de `gemini-3-flash-preview` para outro modelo.

## Decisions

1. **Configurar `thinking_config` (orçamento de raciocínio explicitamente capado) e um teto real de `max_output_tokens` nas chamadas de bloco de `_execute_extraction_in_blocks`.**
   Alternativa considerada: apenas aumentar `max_output_tokens` sem tocar em `thinking_config`. Rejeitada como solução isolada porque, se o consumo de tokens de "thinking" for proporcional/ilimitado, aumentar o teto não impede que o "thinking" continue consumindo a maior parte do orçamento antes da saída. A correção capa explicitamente o orçamento de raciocínio (`thinking_budget=4096`) E aumenta o teto de saída visível (`max(max_tokens, 16384)`), corrigindo também o bug de no-op que existia para E1/E2 (que "aumentavam" para um valor idêntico ao default).
   **Achado durante a implementação**: ao capar o orçamento de "thinking" apenas para E1/E2 mantendo o teto de tokens default para os demais blocos, os blocos `E3`/`E4` (que antes funcionavam) passaram a truncar pelo mesmo motivo. A correção foi generalizada para todos os blocos de `_execute_extraction_in_blocks` (não só E1/E2), já que a causa raiz (orçamento de saída insuficiente para um modelo "thinking") é genérica ao mecanismo de blocos, não específica de um bloco. Confirmado por execução real: após a generalização, nenhum bloco (A-E5) trunca para o caso `Petição Inicial_evento_1.md`.
   Este ajuste está confinado a `_execute_extraction_in_blocks`, que já é efetivamente exclusivo de `extr-peticao-processo` (blocos com nomes de campo hardcoded desta skill) — não altera o caminho de `generate_structured` usado pela chamada única (camadas 1-2), preservando o comportamento de `extr-contestacao-processo`/`extr-decisao-processo`.

2. **Corrigir `_sanitize` para recursar em cada subschema de `anyOf` (e `oneOf` antes de ser removido/bloqueado), igual a `properties`/`items`.**
   Alternativa: remover `anyOf` do schema da petição inteiramente. Rejeitada — `anyOf` é uma construção legítima e já suportada nominalmente (está em `allowed_keys` e a spec `gemini-schema-alignment` já exige preservá-la); o bug é a falta de sanitização recursiva do conteúdo, não a presença da chave.

3. **Substituir o recorte de páginas fixo `[13, 14, 15]` por uma busca estrutural no Markdown** (ex.: pelo cabeçalho `# DOS PEDIDOS`/`DO PEDIDO`/`DOS REQUERIMENTOS` e marcadores de página ao redor), com fallback para o documento inteiro se a seção não for localizada — em vez de assumir que "pedidos" sempre estão nas páginas 13-15.
   Alternativa: manter os números de página fixos, mas documentá-los como suposição. Rejeitada porque viola diretamente o requisito do usuário de que E1/E2 não dependam de um caso específico.

4. **Remover o texto hardcoded de "Banco do Brasil"/processo `0003453-81.2003.8.26.0136` das instruções de prompt de E1/E2/E3 e do fallback determinístico de última instância**, substituindo por instruções genéricas de granularidade (ex.: "extraia cada pedido individualizado como item separado, sem agrupar") e, no fallback determinístico, por uma lista vazia (respeitando a Diretriz 2 do `SKILL.md`: omitir em vez de inventar) em vez de um texto de caso real.

## Risks / Trade-offs

- [Risco] Ajustar `thinking_config`/`max_output_tokens` no caminho compartilhado de `generate_structured` pode alterar timing/custo de chamadas de `extr-contestacao-processo`/`extr-decisao-processo` → Mitigação: rodar os testes existentes dessas skills antes/depois da mudança como checagem de regressão (sem alterar seus arquivos), e escolher valores apenas mais permissivos, nunca mais restritivos, que os atuais.
- [Risco] A causa exata do 400 `INVALID_ARGUMENT` na chamada 1 não foi confirmada empiricamente (mensagem de erro completa do Gemini não foi persistida) — a hipótese do bug de sanitização de `anyOf` é a mais provável, mas pode não ser a única causa → Mitigação: persistir a mensagem de erro completa em debug (arquivo, não só logger) como parte da implementação, para confirmar/refutar antes de declarar a correção concluída.
- [Risco] Buscar a seção "DOS PEDIDOS" por cabeçalho estrutural pode falhar em petições com formatação distinta → Mitigação: manter fallback para o documento inteiro (comportamento mais seguro que assumir páginas fixas erradas).
- [Trade-off] Remover o texto "mínimo obrigatório" específico do prompt pode reduzir a taxa de acerto pontual neste caso específico se o modelo se beneficiava do exemplo — aceito conscientemente, pois a robustez genérica é o objetivo explícito do usuário, sobrepondo-se à otimização para um único caso.

## Open Questions

- O texto completo do erro 400 do Gemini na chamada 1 (schema completo) precisa ser capturado para confirmar definitivamente se a causa é a falta de sanitização recursiva de `anyOf` ou outra construção do schema. Isso será resolvido durante a implementação (tasks.md inclui captura de debug antes de aplicar a correção).
