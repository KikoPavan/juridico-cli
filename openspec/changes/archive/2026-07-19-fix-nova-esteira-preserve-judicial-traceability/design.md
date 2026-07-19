## Context

A execução real com Gemini produziu envelopes válidos nas etapas de segmentação e curadoria, mas expôs uma quebra de contrato entre nomes alternativos retornados pelo modelo (`page_number_start`/`page_number_end`) e os nomes canônicos consumidos pelo normalizador (`pages_start`/`pages_end`). A mesma passagem descarta metadados processuais e marcadores `[[judicial_locator: ...]]` que já estavam no Markdown limpo. Como o problema atravessa três skills canônicas, a correção deve estabelecer um contrato de propagação explícito sem alterar conversão, limpeza, extração específica ou provider.

O estado operacional e a arquitetura-alvo devem ser conferidos em `docs/runbooks/runbook_operacional_minimo.md` e `docs/architecture/juridico_cli_documento_mestre.md`. Não há escolha de nova ferramenta, runtime ou versão; se isso mudar durante a implementação, `docs/reference/project_version_matrix.md` deve ser consultado antes.

## Goals / Non-Goals

**Goals:**

- Canonicalizar paginação no primeiro limite confiável da nova esteira e propagá-la sem perda.
- Preservar identidade judicial no envelope, frontmatter, anchors e corpo Markdown final.
- Tornar conservador o fallback curatorial para tipos documentais centrais protegidos.
- Cobrir o fluxo com uma regressão representativa da Petição Inicial do evento 1 e testes unitários do normalizador.

**Non-Goals:**

- Alterar `pdf-to-md`, `md-clean-markdown`, `extr-peticao-processo` ou o provider Gemini.
- Preencher por inferência nova `title`, `parties_normalized`, `court` ou `judge`; esses campos continuam dependendo de informação confiável disponível.
- Criar novo módulo, serviço, runtime ou dependência externa.
- Reprocessar ou migrar automaticamente artefatos históricos já gerados.

## Decisions

### 1. Canonicalizar aliases de paginação antes de consumir a peça

Cada peça usará `pages_start = pages_start ?? page_number_start` e `pages_end = pages_end ?? page_number_end`, preservando valores canônicos não nulos. A canonicalização deve ocorrer na fronteira de entrada/saída do segmentador ou no adaptador imediato do pipeline, e o curador e o normalizador devem aceitar e propagar o resultado canônico.

Isso concentra compatibilidade de schema na borda e evita espalhar decisões divergentes. A alternativa de corrigir apenas o frontmatter foi rejeitada porque os envelopes intermediários e as regras do curador continuariam sem paginação.

### 2. Tratar rastreabilidade como dados transportados, não como nova extração semântica

O pipeline preservará os valores já disponíveis com precedência explícita: atributos da peça; metadados do envelope; atributos encontrados nos `judicial_locator` do texto. `process_number` é a chave final preferida, com `processo_id` aceito como fonte compatível; `event_id` será serializado como `event`; `document_code` manterá o mesmo nome.

O corpo entregue ao `yaml-normalizador-juridico` continuará sendo a fonte do corpo final. Marcadores existentes devem ser transportados literalmente. Isso evita reconstrução potencialmente divergente. A alternativa de regenerar todos os localizadores a partir das páginas foi rejeitada porque poderia perder atributos e alterar evidência de origem.

### 3. Enriquecer somente anchors gerados

Quando uma etapa criar um anchor, ela incluirá `page`, `process_number`, `event` e `document_code` para cada valor conhecido. Anchors existentes não terão valores confiáveis substituídos por nulos ou inferências menos específicas.

Essa decisão mantém compatibilidade progressiva: consumidores podem continuar aceitando anchors mínimos, enquanto novos anchors carregam contexto suficiente para auditoria.

### 4. Aplicar fallback curatorial conservador a tipos protegidos

Para `peticao_inicial`, `contestacao`, `decisao`, `sentenca` e `recurso`, ausência de classificação confiável não poderá resultar no default `irrelevante`; o fallback mínimo será `relevante`, sem enfraquecer regras que promovam a peça a `nuclear`. A proteção deve ocorrer no curador e ser defendida no normalizador para que um campo ausente não volte a cair no default genérico.

A alternativa de apenas impedir remoção foi rejeitada porque ainda deixaria metadado contraditório (`manter` com impacto `irrelevante`) e poderia afetar consumidores posteriores.

### 5. Testar a fronteira ponta a ponta e a renderização final

A regressão usará a fixture real da Petição Inicial quando ela puder ser versionada sem dados sensíveis; caso contrário, usará fixture mínima equivalente com o mesmo locator, aliases de paginação e tipo documental. O teste focado atravessará segmentação/adaptação, curadoria e normalização; testes específicos do `yaml-normalizador-juridico` verificarão o frontmatter e a preservação literal do corpo.

## Risks / Trade-offs

- [Schemas intermediários rejeitarem novos campos] → Atualizar schemas de entrada/saída e validadores em conjunto, mantendo compatibilidade com campos canônicos existentes.
- [Duas fontes fornecerem identificadores conflitantes] → Aplicar precedência determinística e nunca substituir valor explícito não nulo por fallback; registrar cobertura de conflito em teste unitário.
- [Fixture real conter dados sensíveis ou ser grande] → Preferir fixture mínima sanitizada que conserve exatamente a estrutura necessária à regressão.
- [Normalização atual do corpo alterar whitespace] → Limitar a garantia aos marcadores literais e testar o corpo final; evitar ampliar esta mudança para as skills de limpeza protegidas.
- [Tipos documentais variarem em nomenclatura] → Cobrir os nomes canônicos enumerados no requisito e mapear aliases somente se já reconhecidos pelos contratos atuais.

## Migration Plan

1. Atualizar contratos e canonicalização do segmentador/adaptador, mantendo leitura dos campos anteriores.
2. Propagar metadados e aplicar a proteção curatorial.
3. Atualizar o normalizador e seu validador para renderizar os campos judiciais e preservar os marcadores.
4. Executar os testes focados da nova esteira, a suíte do normalizador e `openspec validate --all --strict`.
5. Liberar sem migração de dados; artefatos novos passam a obedecer ao contrato. Em rollback, reverter conjuntamente as três skills e seus schemas/testes.

## Open Questions

- Confirmar durante a implementação se `decisao` chega sempre com esse nome ou se também deve ser representada pelo tipo canônico já existente `decisao_interlocutoria`, sem ampliar a lista normativa solicitada.

