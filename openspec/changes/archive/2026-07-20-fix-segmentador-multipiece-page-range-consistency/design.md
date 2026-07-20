## Context

As mudanças anteriores permitem materializar documentos multipiece e aceitar `capa_processo`, mas o teste real revelou uma ambiguidade adicional: números de página podem se repetir em vários eventos/localizadores. A estratégia atual encontra uma ocorrência inicial e usa a última ocorrência compatível da página final, o que pode atravessar peças intermediárias. Em paralelo, metadados globais são derivados do primeiro localizador, mesmo quando o arquivo agregado não possui um único `document_code`, e `total_pages` pode refletir apenas o maior localizador reconhecido por uma heurística parcial.

O problema atravessa o segmentador, a curadoria e o normalizador. A fonte textual continua sendo o Markdown limpo; nenhuma correção será deslocada para conversão, limpeza, extratores ou provider.

## Goals / Non-Goals

**Goals:**

- Garantir que o texto de uma peça contenha somente localizadores pertencentes ao intervalo reconciliado.
- Desambiguar páginas repetidas por posição, identidade judicial e fronteiras das peças vizinhas.
- Tornar `total_pages` monotônico em relação aos localizadores e às peças materializadas.
- Separar identidade global confiável de identidade específica por peça.
- Registrar ajustes determinísticos feitos sobre limites/identidade propostos pelo LLM.
- Impedir impacto nuclear e status `ready` quando não existe rota de extração reconhecida.
- Validar o fluxo real até envelopes e Markdown normalizado.

**Non-Goals:**

- Criar enum novo para `PED HABILIT1` sem evidência suficiente de taxonomia canônica.
- Alterar conteúdo do Markdown fonte ou sintetizar texto ausente.
- Alterar `pdf-to-md`, `md-clean-markdown`, qualquer `extr-*` ou Gemini.
- Redefinir a política administrativa de `capa_processo` já estabelecida.

## Decisions

### Recorte estrito por sequência contígua de localizadores

O índice posicional continuará sendo a base do recorte, mas um intervalo não será formado pela primeira ocorrência de `pages_start` até a última ocorrência global de `pages_end`. A resolução escolherá o início compatível com a identidade/ordem da peça e percorrerá localizadores contíguos, encerrando antes do primeiro marcador que esteja fora do intervalo permitido ou pertença inequivocamente à próxima peça. Repetições das páginas permitidas dentro dessa sequência permanecem; ocorrências posteriores, separadas por outra peça, não são anexadas.

Um `event_separator` somente poderá ser incluído se estiver posicionalmente dentro da sequência da peça e possuir página dentro do intervalo, ou se uma regra explícita o associar à fronteira e registrar essa inclusão. O teste validará as páginas de todos os marcadores, não apenas o tamanho do texto.

Alternativa considerada: remover localizadores fora da faixa após um recorte amplo. Rejeitada porque deixaria o texto associado ao marcador indevidamente incorporado e quebraria rastreabilidade.

### Reconciliação local antes do enriquecimento

Depois do recorte, o segmentador calculará páginas e identidade a partir dos localizadores efetivamente materializados. `pages_start/pages_end`, `event` e `document_code` da peça serão reconciliados com essa evidência. Se os valores propostos diferirem, os valores reais prevalecerão e uma entrada em `audit_trail` (ou campo de ajuste equivalente aceito pelo contrato) registrará valores propostos, valores aplicados e motivo.

Alternativa considerada: manter os limites do LLM e apenas emitir warning. Rejeitada porque perpetua envelope internamente inconsistente.

### Metadados globais exigem consenso

`processo_id/process_number` pode ser global quando houver consenso dos localizadores. `document_code` e `event` somente serão globais quando todos os localizadores substanciais concordarem; arquivos agregados com múltiplos valores usarão `null`. Tokens malformados ou fragmentos sem padrão confiável não serão promovidos. Cada peça continuará recebendo o código derivado de seus próprios localizadores.

Alternativa considerada: usar o primeiro valor não nulo. Rejeitada porque a ordem do documento não transforma um código de peça em código do agregado.

### `total_pages` é o máximo das evidências disponíveis

O valor final será o máximo entre: maior página numérica de todos os `judicial_locator`, maior `pages_end` reconciliado e total de páginas confiável já presente no frontmatter. Assim, nunca será menor que uma peça persistida. Valores ausentes não serão inventados.

### Segurança de peças não roteáveis em duas camadas

O curador identificará tipos sem mapeamento de extrator (incluindo `nao_classificado`) e não permitirá que relevância estimada alta os transforme automaticamente em `nuclear`; por padrão usará impacto no máximo acessório e ação `revisar` ou `resumir`, com `encaminhamento: null`. O normalizador continuará resolvendo `REVISAR_MANUAL` e forçará `review_status: unroutable` e `status: needs_review`, independentemente da ação recebida, nunca `ready`.

Alternativa considerada: mapear `PED HABILIT1` diretamente a petição. Rejeitada porque `document_code` não é prova suficiente do subtipo jurídico e não existe enum específico consolidado.

## Risks / Trade-offs

- [Páginas repetidas e identidade incompleta ainda podem ser ambíguas] → usar ordem das peças e início da próxima como limites; falhar com diagnóstico se não houver sequência inequívoca.
- [Reconciliação pode alterar limites fornecidos pelo LLM] → registrar cada ajuste e preservar o envelope debug pré-materialização.
- [Separadores podem ficar fora de todas as peças] → aceitar essa exclusão quando não houver associação inequívoca; não anexá-los arbitrariamente.
- [Peça não classificada pode ser juridicamente importante] → enviar para revisão segura, sem remover nem promover automaticamente à extração profunda.
- [Teste online depende do Gemini] → executar a tentativa real e complementar com replay do envelope debug real quando houver instabilidade externa, registrando ambos os resultados.

## Migration Plan

1. Corrigir recorte contíguo e reconciliação por peça, preservando o artefato debug.
2. Corrigir cálculo de metadados globais e `total_pages`.
3. Aplicar política de não roteáveis no curador e confirmar defesa do normalizador.
4. Ampliar fixture/testes e executar o fluxo real de `Processo.md`.
5. Em rollback, restaurar as estratégias anteriores; não há migração de dados persistentes.

## Open Questions

- Nenhuma para implementação: `PED HABILIT1` permanecerá `nao_classificado` nesta mudança e seguirá para revisão segura.

