## Context

`run_segmentador_stage` envia o Markdown completo ao modelo usando diretamente o schema final do Envelope de Processo. Como esse schema exige `text`, o modelo é induzido a repetir a íntegra da peça em JSON. Respostas grandes podem truncar; além disso, o fallback interno do cliente Gemini pode produzir o contrato de outra extração, e o reparo textual atual volta a pedir um envelope completo e volumoso.

A fronteira correta é: o LLM decide apenas cortes e classificação; o módulo operacional em Python conserva a fonte de verdade textual, materializa as peças e só então valida o envelope final contra o schema canônico. A mudança permanece no baseline `apps/data-processing` e na skill canônica existente, sem criar novo runtime ou alterar providers.

## Goals / Non-Goals

**Goals:**

- Reduzir a saída solicitada ao LLM a descritores compactos de peças.
- Reconstruir deterministicamente o `text` de cada peça a partir do Markdown original.
- Priorizar `judicial_locator` para limites, identidade judicial e anchors.
- Recuperar documentos inequivocamente unitários sem depender de reparo de JSON volumoso.
- Validar somente o envelope final materializado pelo schema canônico.

**Non-Goals:**

- Alterar o contrato dos extratores, em especial `extr-peticao-processo`.
- Alterar limpeza, frontmatter, OCR ou implementação/configuração do provider Gemini.
- Introduzir segmentação semântica avançada para documentos ambíguos sem localizadores.
- Trocar o schema final consumido pelo curador e normalizador.

## Decisions

### Separar contrato de decisão do LLM do contrato final

O prompt e o schema usados na chamada de segmentação aceitarão apenas uma lista compacta com identidade/índice, tipo e confiança, limites de página, título ou excerpt, relevância, anchors e identificadores judiciais opcionais. `text`/`text_content` integral não fará parte desse contrato intermediário.

Alternativa considerada: continuar usando o schema final e instruir o modelo a deixar `text` vazio. Isso mantém conflito com campos obrigatórios e mistura um contrato incompleto com o artefato validado; portanto, um schema intermediário explícito é mais seguro.

### Materializar intervalos no orquestrador

Após receber descritores válidos, Python mapeará os limites para trechos do Markdown original usando os marcadores de página/localizadores. O texto reconstruído incluirá os próprios `judicial_locator`. Campos canônicos terão precedência sobre aliases, mas localizadores preencherão valores ausentes. Metadados globais e de proveniência continuarão sendo calculados localmente.

Se limites de uma resposta forem inconsistentes, sobrepostos de forma inválida ou impossíveis de resolver, ela não será promovida diretamente a envelope final. A validação Draft 7 será aplicada depois de defaults, aliases, conteúdo e proveniência serem materializados.

Alternativa considerada: pedir offsets de caracteres ao modelo. Offsets são frágeis diante de normalização e não aproveitam a paginação canônica já presente.

### Fallback unitário baseado em evidência determinística

Quando todos os localizadores pertencem a um único grupo judicial, o orquestrador poderá criar uma única peça contendo todo o corpo. `pages_start`/`pages_end` virão do mínimo/máximo das páginas e identidade/anchors dos localizadores. O tipo será inferido somente quando heading, `document_code` ou nome do arquivo fornecer sinal seguro; caso contrário será usado o tipo desconhecido aceito pelo contrato, sem inventar classificação.

Esse fallback poderá ser acionado quando a chamada estruturada falhar ou devolver raiz incompatível. A estrutura genérica de extração por campos nunca será tratada como envelope do segmentador.

Alternativa considerada: corrigir o fallback genérico do cliente Gemini. Isso alteraria o provider compartilhado, está fora do escopo e não elimina a necessidade de reconstrução determinística.

### Conter mudanças nas fronteiras atuais

A lógica reutilizável será implementada como helpers coesos próximos à etapa do segmentador ou no módulo já responsável pela orquestração, evitando um novo serviço ou abstração global. A skill documentará a saída compacta esperada do modelo; o `output-schema.json` continuará sendo a autoridade para o envelope persistido.

## Risks / Trade-offs

- [Limites do modelo não correspondem a páginas existentes] → validar os descritores antes do corte e usar fallback unitário apenas quando houver um único grupo inequívoco.
- [Documentos sem marcadores não permitem corte determinístico por página] → conservar comportamento controlado para respostas resolvíveis por outra evidência e falhar claramente nos casos ambíguos, sem fabricar texto.
- [Inferência de tipo classifica incorretamente] → restringir vocabulário e regras a sinais explícitos testados, com fallback para tipo desconhecido.
- [Schema intermediário diverge do schema final] → testar a materialização completa e validar o JSON persistido com `platform/skills/segmentador-juridico/assets/output-schema.json`.
- [Mudança afeta múltiplas peças no mesmo Markdown] → adicionar testes de unidade dos cortes e preservar a ordem lógica, além da regressão unitária da Petição Inicial.

## Migration Plan

1. Introduzir helpers e contrato compacto mantendo o envelope final inalterado.
2. Atualizar o prompt da skill para proibir conteúdo integral na resposta do modelo.
3. Adicionar testes focados do caminho estruturado, resposta incompatível e fallback unitário.
4. Executar a validação focada e global solicitada antes da adoção.

Rollback: reverter os helpers/prompt e restaurar a chamada anterior; não há migração de dados nem mudança incompatível no envelope persistido.

## Open Questions

Nenhuma decisão bloqueante. Durante a implementação, o vocabulário exato de inferência segura deve ser derivado dos tipos aceitos pelo schema e da convenção já presente na skill.
