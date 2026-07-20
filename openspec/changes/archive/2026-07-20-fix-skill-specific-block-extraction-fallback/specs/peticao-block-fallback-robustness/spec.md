## MODIFIED Requirements

### Requirement: No Premature Truncation in E1/E2 Blocks
O fallback por blocos de `extr-peticao-processo`, agora exposto como `PeticaoBlockStrategy` e selecionado explicitamente por `bundle_id="extr-peticao-processo"` através do mecanismo de seleção de estratégias, SHALL completar as chamadas dos blocos `E1` (`pedidos`) e `E2` (`pedidos_individualizados`) sem retornar JSON truncado, para o caso real `Petição Inicial_evento_1.md` (processo `4000153-37.2026.8.26.0136/SP`).

#### Scenario: E1 completes without truncation
- **WHEN** o bloco `E1` é processado para `Petição Inicial_evento_1.md` através de `PeticaoBlockStrategy`
- **THEN** a resposta bruta do Gemini para o bloco é um JSON completo e parseável (sem erro `Unterminated string` ou `Expecting ',' delimiter` por corte de token)

#### Scenario: E2 completes without truncation
- **WHEN** o bloco `E2` é processado para `Petição Inicial_evento_1.md` através de `PeticaoBlockStrategy`
- **THEN** a resposta bruta do Gemini para o bloco é um JSON completo e parseável

### Requirement: Extraction Completes Without Reservations for the Real Case
A extração completa de `extr-peticao-processo` para `Petição Inicial_evento_1.md`, executada via `PeticaoBlockStrategy` selecionada por `bundle_id`, SHALL ser concluída sem blocos em `_failed_blocks` (sem a chave `_failed_blocks` no JSON final, ou com lista vazia).

#### Scenario: Final result has no failed blocks
- **WHEN** a extração completa roda para `Petição Inicial_evento_1.md` com `bundle_id="extr-peticao-processo"`
- **THEN** o JSON final não contém `_failed_blocks`, ou `_failed_blocks` é uma lista vazia

### Requirement: Generic Location of the Pedidos Section
O recorte de conteúdo para os blocos `E1`-`E4` de `PeticaoBlockStrategy` SHALL localizar a seção de pedidos/tutela de urgência do Markdown por marcador estrutural do documento (ex.: cabeçalho `DOS PEDIDOS`/`DO PEDIDO`/`DOS REQUERIMENTOS`), e não por números de página fixos codificados no sistema.

#### Scenario: Section located by structural heading
- **WHEN** o Markdown contém um cabeçalho equivalente a "DOS PEDIDOS" em qualquer página
- **THEN** o recorte de conteúdo enviado ao Gemini para os blocos `E1`-`E4` inclui o texto a partir dessa seção, independentemente do número de página em que ela ocorre

#### Scenario: Fallback to full document when section not found
- **WHEN** nenhum marcador estrutural de pedidos é encontrado no Markdown
- **THEN** o sistema usa o documento completo como conteúdo de entrada para os blocos `E1`-`E4`, em vez de um recorte de páginas fixo que pode não conter a seção relevante

### Requirement: No Case-Specific Hardcoded Content in Fallback
As instruções de prompt dos blocos `E1`, `E2` e `E3` de `PeticaoBlockStrategy`, bem como o fallback determinístico local `_apply_deterministic_fallback_e1_e2`, SHALL NOT conter texto, nomes de partes ou números de processo de um caso real específico como exemplo de "itens mínimos obrigatórios" ou como valor padrão de último recurso.

#### Scenario: Deterministic fallback returns empty instead of another case's content
- **WHEN** o fallback determinístico local não encontra nenhuma linha correspondente aos prefixos de pedido no Markdown
- **THEN** o sistema retorna uma lista vazia de pedidos (respeitando a diretriz de omitir dados ausentes) em vez de um texto fixo de um caso real anterior

#### Scenario: Prompt instructions are generic
- **WHEN** as instruções de prompt dos blocos `E1`/`E2`/`E3` são inspecionadas
- **THEN** elas não citam nomes de partes, números de processo ou fatos específicos de nenhum caso real — apenas orientações genéricas de granularidade e formato

### Requirement: Strategy Extraction Preserves Observable Behavior
A extração da lógica de blocos de petição para `PeticaoBlockStrategy`, dentro do mecanismo de seleção de estratégias por `bundle_id`, SHALL preservar o comportamento observável já validado (blocos `A`–`E5`, prompts, corte estrutural de pedidos, fallback determinístico E1/E2, validação final contra o schema completo) sem alterar resultados para os casos já cobertos por teste.

#### Scenario: Existing petição tests pass unchanged after refactor
- **WHEN** a suíte de testes existente para blocos de `extr-peticao-processo` é executada após a introdução de `PeticaoBlockStrategy` e do mecanismo de seleção
- **THEN** todos os testes previamente aprovados continuam aprovados sem alteração de asserts
