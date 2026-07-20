## Context

O pipeline já reconhece semanticamente `capa_processo` em pontos isolados: a normalização de tipos do orquestrador contém essa variação e o routing map do normalizador a trata como alias de `cabecalho_processo`. Entretanto, o schema final do segmentador não aceita o valor, e o roteamento atual para `extr-cabecalho-processo` conflita com a decisão desta mudança de não executar extração jurídica profunda para uma capa administrativa.

A correção atravessa três skills existentes, sem criar novo runtime: o segmentador aceita e documenta o tipo; o curador aplica uma decisão administrativa determinística; o normalizador mantém uma defesa segura caso receba a peça apesar da remoção esperada. A mudança de materialização multipiece concluída anteriormente é pré-requisito operacional para o teste de `Processo.md`, mas não será redesenhada aqui.

## Goals / Non-Goals

**Goals:**

- Tornar `capa_processo` um valor oficial e validável no envelope do segmentador.
- Preservar a classificação semanticamente correta produzida pelo LLM, sem convertê-la em outro tipo apenas para satisfazer o schema.
- Aplicar curadoria administrativa determinística, com impacto irrelevante, baixa prioridade e nenhum encaminhamento para `extr-*`.
- Garantir comportamento seguro e não bloqueante do normalizador para entradas inesperadas desse tipo.
- Cobrir schema, documentação e fluxo multipiece realista.

**Non-Goals:**

- Criar ou alterar qualquer extrator `extr-*`.
- Extrair profundamente dados da capa ou promover a capa a peça juridicamente relevante.
- Alterar conversão PDF, limpeza Markdown, materialização multipiece ou provider Gemini.
- Introduzir novo dispatcher, skill, dependência ou runtime.

## Decisions

### `capa_processo` permanece um tipo próprio

O valor será acrescentado ao enum canônico, às referências da skill e a qualquer lista manual de validação. Não será normalizado para `cabecalho_processo`, pois a distinção permite aplicar política administrativa explícita e auditar a decisão original do segmentador.

Alternativa considerada: mapear silenciosamente para `cabecalho_processo`. Rejeitada porque altera a semântica observada e pode reativar encaminhamento profundo.

### Curadoria administrativa precede regras genéricas

Uma regra determinística de alta precedência reconhecerá `capa_processo` e produzirá `acao_curatorial: remover`, `impacto_processual: irrelevante`, prioridade baixa e `encaminhamento: null`, com justificativa e audit trail. A opção `remover` usa o comportamento existente pelo qual o normalizador não gera artefato; não significa descarte silencioso, pois a decisão permanece no envelope curado.

Alternativa considerada: `resumir`. Rejeitada como padrão porque ainda poderia gerar um artefato roteável e não há necessidade jurídica profunda definida. Uma evolução futura poderá adotar síntese administrativa mediante requisito próprio.

### Defesa em profundidade no normalizador

O routing map deixará de associar `capa_processo` a `extr-cabecalho-processo`. Caso uma capa chegue com ação diferente de `remover`, ela será marcada com o mecanismo seguro não profundo já existente (`REVISAR_MANUAL`/não roteável), sem invocar `extr-*` nem quebrar a normalização.

Alternativa considerada: remover a entrada do routing map. Rejeitada porque depender apenas do fallback torna a intenção menos explícita e piora a documentação operacional.

### Validação em camadas

Os testes usarão uma fixture multipiece mínima com capa e peças processuais reais, validando o envelope final pelo schema. O teste real de `Processo.md` será executado quando o arquivo estiver disponível no workspace e as credenciais/runtime necessários estiverem configurados; se faltar um desses insumos, a tarefa registrará precisamente o bloqueio sem substituir o teste por conteúdo inventado.

## Risks / Trade-offs

- [Remover a capa pode eliminar metadados úteis] → manter a peça e sua justificativa no envelope curado; somente impedir sua promoção à extração profunda.
- [Chamadores podem depender do alias para `extr-cabecalho-processo`] → restringir a mudança a `capa_processo`; `cabecalho_processo` mantém o roteamento atual.
- [Regra genérica de baixa confiança pode interceptar a capa] → posicionar a regra administrativa antes dos fallbacks de confiança/relevância e cobrir sua precedência por teste.
- [O teste real depende de arquivo e LLM externos] → separar regressão determinística obrigatória do teste operacional real e relatar indisponibilidade de forma auditável.

## Migration Plan

1. Atualizar contrato, validador e documentação do segmentador.
2. Introduzir e documentar a regra administrativa no curador.
3. Tornar o routing map defensivo para `capa_processo` sem modificar extratores.
4. Adicionar regressões e executar o conjunto de validações, incluindo o teste real quando disponível.
5. Em rollback, remover o enum e a regra específica e restaurar somente a entrada anterior do routing map; não há migração de dados persistentes.

## Open Questions

- Nenhuma decisão de implementação permanece aberta; a ação padrão escolhida é `remover`, com rastreabilidade no envelope curado.

