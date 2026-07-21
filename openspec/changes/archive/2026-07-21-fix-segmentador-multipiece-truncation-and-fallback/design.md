## Context

O fluxo atual coleta `*.md`, mas escolhe `md_files[0]`, envia todo o corpo em uma única chamada `generate_structured()` e trata qualquer `ValueError` com `_single_piece_fallback()`. No caso real de `Processo.pdf`, a resposta compacta ainda foi truncada (`Unterminated string`) para uma entrada de aproximadamente 54.788 caracteres. O cliente evitou corretamente o fallback livre de alto risco e tentou Extração por Blocos; como `segmentador-juridico` não possui — nem deve possuir — estratégia de extrator registrada, a recuperação terminou indisponível. O fallback local também falhou porque exige um único grupo de localizadores.

O diagnóstico do cliente é gravado como `structured_call_error.txt` com modo `w`, sem identidade suficiente de estágio, arquivo, tentativa ou estratégia. O estágio grava nomes globais de envelope e lança a falha do primeiro arquivo, portanto não possui unidade de isolamento para lotes. A solução permanece no baseline `apps/data-processing`, usa o schema e a skill canônicos e não cria um novo extrator, runtime ou serviço.

## Goals / Non-Goals

**Goals:**

- Processar determinística e isoladamente todos os Markdown elegíveis.
- Antecipar risco de truncamento e particionar somente quando necessário.
- Preservar páginas, locators, identidade judicial, origem e ordem em análises parciais e no envelope consolidado.
- Reconhecer uma peça que cruza janelas e consolidá-la exatamente uma vez.
- Recuperar múltiplas peças por regras locais somente com evidência estrutural confiável.
- Validar o contrato compacto consolidado antes da materialização, validar o envelope final canônico antes da promoção e produzir diagnóstico correlacionável.
- Preservar o caminho atual de chamada única para documentos pequenos e unitários.

**Non-Goals:**

- Alterar o schema canônico para tolerar saída incompleta ou inventada.
- Alterar provider/modelo Gemini ou as estratégias de petição, contestação e decisão.
- Registrar o segmentador como extrator ou reutilizar a infraestrutura genérica de Extração por Blocos.
- Executar extração jurídica após segmentar, realizar chamadas reais na suíte ou arquivar antes da regressão operacional com `Processo.pdf`.

## Decisions

### Orquestração por arquivo com resultado de lote

`run_segmentador_stage` enumerará os Markdown elegíveis em ordem estável e delegará cada origem a uma operação interna isolada. Cada operação terá contexto próprio (origem, hash, grupo/processo, diretório/nomes de artefato e tentativas). Exceções serão capturadas no limite do arquivo; os demais arquivos continuarão. Para uma única origem bem-sucedida, o retorno continuará sendo o `Path` do envelope final. Para múltiplas origens, ou quando houver falha isolada, o retorno será o `Path` de `segmentacao_lote.json`, manifesto que lista cada origem com `status` (`success` ou `needs_review`), caminho do envelope quando existente e diagnóstico, sem incorporar peças nem texto. O orquestrador reconhecerá o manifesto e enviará somente cada envelope `success` ao curador e normalizador.

Alternativa considerada: concatenar todos os Markdown e executar uma segmentação global. Rejeitada porque mistura processos, invalida proveniência e amplia o risco de truncamento.

### Preflight determinístico e estratégia interna de janelas

Antes da chamada, o estágio indexará marcadores de página e `judicial_locator`, tamanho em caracteres e sinais estruturais. Entradas abaixo dos limites configurados e sem risco continuarão pela chamada única atual. Entradas de alto risco serão divididas por sequências reais de páginas; nunca no meio de um marcador ou por corte cego de caracteres. Se marcadores forem insuficientes, o estágio usará blocos estruturais completos apenas quando os limites forem verificáveis; caso contrário, falhará para revisão.

Cada janela conterá identificador, intervalo posicional e de páginas, origem e uma sobreposição mínima configurada. A sobreposição será ativada apenas em fronteiras nas quais a continuidade de uma peça precise ser reconhecida. O schema de decisão parcial continuará compacto e não solicitará texto integral.

Alternativa considerada: aumentar `max_output_tokens` ou sempre fragmentar. A primeira apenas desloca o limite e a segunda aumenta custo/complexidade para documentos pequenos.

### Consolidação determinística orientada por evidência

Descritores parciais serão normalizados e ordenados pela posição real na origem. Dois descritores sobrepostos serão unidos somente se as evidências concordarem: mesma origem e processo, intervalos contíguos/sobrepostos na zona de overlap e identidade documental compatível (`document_type`, evento, código, título/cabeçalho e continuidade textual observável no Markdown). A união calculará o intervalo pela origem e manterá um único descritor; não concatenará texto produzido pelo modelo.

Descritores adjacentes com mudança confiável de evento, código, tipo ou cabeçalho permanecerão separados. Conflitos, lacunas, sobreposições fora da região controlada, páginas inexistentes ou identidades incompatíveis invalidarão a consolidação. A coleção compacta consolidada será validada pelo contrato intermediário e por invariantes de cobertura/ordem antes de qualquer recorte. Somente então a materialização recortará o Markdown original; o envelope materializado será validado pelo schema canônico antes da promoção.

Alternativa considerada: deduplicar somente por tipo e página. Rejeitada porque pode unir peças juridicamente distintas do mesmo tipo ou duplicar uma peça que cruza janelas.

### Fallback multiparte próprio e conservador

O fallback do segmentador analisará sequências de locators e cabeçalhos. Uma nova fronteira somente será criada por evidências confiáveis como mudança de evento/código, cabeçalho judicial ou início reconhecível de petição, contestação, decisão, procuração ou equivalente, sempre ancorado em página/posição real. O fallback poderá produzir várias peças e preservará intervalos contíguos; quando tipo ou limite não puder ser sustentado, o arquivo será marcado para revisão sem envelope final.

Essa estratégia é interna ao estágio e não entra em `BLOCK_STRATEGIES`. `BlockExtractionStrategyUnavailableError` não será convertido em uso implícito de `PeticaoBlockStrategy`, `ContestacaoBlockStrategy` ou `DecisaoBlockStrategy`.

### Diagnóstico correlacionável e não sobrescrito

Cada tentativa emitirá logs estruturados com arquivo, páginas, caracteres, decisão de particionamento, janela, contagem parcial, consolidação, validação e fallback. Artefatos em `var/artifacts/gemini-debug/` usarão nome exclusivo sanitizado ou subdiretório por execução/origem e incluirão metadados de estágio, estratégia, tentativa, timestamp e erro. A escrita será atômica e nunca reutilizará silenciosamente `structured_call_error.txt` de outra origem.

Alternativa considerada: manter um arquivo global e anexar texto. Rejeitada porque dificulta correlação e concorrência/reprodução de uma tentativa específica.

## Risks / Trade-offs

- [Marcadores ausentes ou inconsistentes impedem janelas seguras] → não cortar por caracteres; encaminhar a origem para revisão com inventário de evidências.
- [Sobreposição pode duplicar ou unir peças distintas] → restringir overlap, manter posições absolutas e exigir identidade/continuidade compatíveis para merge.
- [Limiares de risco podem ficar descalibrados] → centralizar configuração, registrar a decisão e cobrir ambos os caminhos com fake client.
- [Múltiplas chamadas aumentam custo e latência] → preservar chamada única para entradas pequenas e usar janelas somente após preflight.
- [Mudança do retorno do estágio pode afetar curador/orquestrador] → preservar compatibilidade no caso unitário e adaptar o chamador explicitamente para iterar resultados de lote.
- [Diagnósticos contêm dados jurídicos sensíveis] → registrar metadados e erros mínimos, manter artefatos no armazenamento operacional autorizado e não copiar texto integral desnecessariamente.

## Migration Plan

1. Extrair o processamento unitário sem mudar seu comportamento para documentos pequenos.
2. Introduzir resultado/isolamento de lote e adaptar o chamador da nova esteira.
3. Adicionar preflight, janelas e consolidação determinística com fake client.
4. Ampliar fallback multiparte e diagnóstico por tentativa.
5. Executar suítes, lint, `git diff --check` e `openspec validate --all --strict`.
6. Preparar e executar separadamente a regressão operacional real com `Processo.pdf`; somente após esse aceite a mudança poderá ser considerada para arquivamento.

Rollback: desativar o caminho particionado e restaurar o processamento unitário anterior; não há migração persistente de schema ou dados.

## Open Questions

- Nenhuma decisão bloqueante. Os limiares iniciais e o overlap serão constantes internas explícitas, cobertas por testes e ajustáveis sem alterar provider, modelo ou schema canônico.
