## Context

`run_segmentador_stage` já separa a decisão compacta do LLM da materialização local, mas atualmente chama `_materialize_piece` isoladamente e recorta somente por `pages_start/pages_end` ou seus aliases. Em documentos compostos, limites podem estar distribuídos entre campos canônicos, anchors e localizadores do Markdown; uma página separadora também pode aparecer entre peças. A exceção ocorre antes da criação do diretório e da gravação do envelope final, eliminando a evidência necessária para diagnosticar o retorno compacto.

A mudança permanece no baseline operacional `apps/data-processing` e usa os marcadores produzidos anteriormente como dados de origem. Ela não modifica as skills de conversão/limpeza, os extratores ou o provider.

## Goals / Non-Goals

**Goals:**

- Persistir de forma atômica um artefato bruto/debug após validar estruturalmente a resposta compacta e antes de materializar peças.
- Resolver intervalos multipiece com uma ordem determinística e explícita de estratégias.
- Preservar texto e `judicial_locator` exatamente como aparecem no Markdown dentro do intervalo escolhido.
- Usar contexto entre peças para resolver limites sem inventar conteúdo.
- Tornar falhas localizadas auditáveis por meio de mensagem estruturada e artefato já persistido.
- Cobrir o caso mínimo de três peças, incluindo a terceira peça.

**Non-Goals:**

- Alterar `pdf-to-md`, `md-clean-markdown`, extratores, provider Gemini ou schemas de respostas desses componentes.
- Pedir ao LLM texto integral ou aceitar texto materializado por ele.
- Introduzir novo módulo, runtime, dependência ou serviço.
- Recuperar texto quando o Markdown não contém evidência locatável suficiente.

## Decisions

### Persistir o envelope compacto antes de qualquer materialização

Após `_is_compact_segmentation` aceitar a resposta — inclusive quando vier do fallback determinístico permitido — `run_segmentador_stage` criará o diretório de saída e gravará um arquivo debug com nome estável e distinto de `envelope_segmentacao.json`. O conteúdo será uma cópia serializável da segmentação compacta e seus metadados disponíveis naquele ponto. A gravação ocorrerá antes do primeiro recorte.

Alternativa considerada: incluir o debug apenas em logs. Foi rejeitada porque logs podem ser truncados e não preservam o payload estruturado necessário à reprodução.

### Materializar a coleção com contexto, preservando a interface simples

A materialização receberá localizadores previamente indexados e, quando necessário, o descritor da próxima peça. Para cada peça, normalizará limites sem alterar o envelope compacto original de debug e tentará, nesta ordem:

1. `pages_start/pages_end` contra `judicial_locator`;
2. `page_number_start/page_number_end` como aliases;
3. páginas declaradas em `anchors`;
4. intervalo do início da peça atual até o início da próxima peça;
5. fallback por página somente quando o índice de localizadores permitir um intervalo inequívoco.

O recorte será feito por posições dos marcadores no Markdown, do marcador inicial até imediatamente antes do marcador posterior ao limite final (ou fim do corpo). Assim, todos os marcadores e o texto intermediário são preservados. `event_separator` será tratado como conteúdo intermediário, não como falha nem como fonte de texto sintético.

Alternativa considerada: segmentar o corpo por expressões de headings ou pelo `text_excerpt` do LLM. Foi rejeitada por ser menos determinística e poder casar texto semelhante ou produzido pelo modelo.

### Falhar com diagnóstico completo, sem degradação silenciosa

Se todas as estratégias falharem, a exceção incluirá `piece_id`, `document_type`, limites canônicos, aliases resolvidos, anchors e um resumo dos localizadores disponíveis (página e identidade judicial). O pipeline não criará `envelope_segmentacao.json` final inválido, mas o envelope bruto já estará disponível.

Alternativa considerada: pular apenas a peça problemática. Foi rejeitada porque alteraria silenciosamente a composição processual e poderia ocultar documento juridicamente relevante.

### Manter dois contratos de artefato

O artefato debug representa a decisão compacta pré-materialização e pode não validar contra o schema final. `envelope_segmentacao.json` continua sendo gravado somente após materialização, enriquecimento e validação canônica completos. Essa distinção evita promover dados parciais ao handoff normal.

## Risks / Trade-offs

- [Páginas repetidas entre eventos podem tornar um limite ambíguo] → combinar página com identidade disponível em anchors/peça e somente aplicar fallback quando o intervalo for inequívoco.
- [Preservar separadores pode anexá-los a uma das peças] → aceitar a preservação conforme requisito, mantendo ordem e sem impedir o recorte.
- [O artefato debug pode conter dados jurídicos sensíveis] → armazená-lo no mesmo diretório operacional já autorizado para os demais envelopes, sem ampliar logs nem contexto externo.
- [Mensagens com todos os localizadores podem ficar extensas] → incluir inventário compacto e determinístico, suficiente para auditoria.
- [Mudança de assinatura interna pode afetar testes existentes] → manter compatibilidade por argumentos opcionais quando razoável e atualizar somente testes focados da etapa.

## Migration Plan

1. Adicionar persistência pré-materialização sem mudar o caminho do envelope final.
2. Introduzir indexação e resolução determinística dos localizadores, integrando o contexto da próxima peça.
3. Adicionar fixture e regressões multipiece, executar testes focados e validações estáticas.
4. Em rollback, remover o novo artefato debug e restaurar a estratégia anterior; não há migração de dados ou schema persistente.

## Open Questions

- O nome final do artefato será escolhido na implementação de acordo com a convenção existente de outputs, mantendo-o explicitamente identificável como bruto/debug.

