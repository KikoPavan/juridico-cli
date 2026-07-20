# safe-normalized-extraction-dispatch Specification

## Purpose

Garantir que somente Markdown jurídico normalizado e aprovado seja enviado a extratores registrados, usando o caminho real de staging e persistindo apenas respostas válidas segundo o schema canônico da skill, sem romper chamadas legadas.

## Requirements

### Requirement: Somente Markdown normalizado e aprovado é despachado

A etapa de coleta da nova esteira MUST despachar um Markdown somente quando seu frontmatter contiver simultaneamente `status: ready`, `review_status: approved` e um `skill_key` explícito válido. Qualquer arquivo inelegível MUST ser ignorado com registro auditável do arquivo e do motivo, sem erro global do pipeline e sem chamada ao LLM.

#### Scenario: Arquivo pronto e aprovado segue para despacho
- **WHEN** um Markdown normalizado contém `status: ready`, `review_status: approved` e um `skill_key` registrado iniciado por `extr-`
- **THEN** a etapa despacha exatamente esse `skill_key` para extração

#### Scenario: Arquivo needs_review não chama LLM
- **WHEN** um Markdown contém `status: needs_review`, ainda que declare algum extrator
- **THEN** o arquivo é ignorado com motivo auditável e o cliente LLM não é chamado

#### Scenario: Arquivo unroutable não chama LLM
- **WHEN** um Markdown contém `review_status: unroutable`, ainda que declare algum extrator
- **THEN** o arquivo é ignorado com motivo auditável e o cliente LLM não é chamado

#### Scenario: Revisão não aprovada não chama LLM
- **WHEN** um Markdown contém `review_status` diferente de `approved`
- **THEN** o arquivo é ignorado com motivo auditável e o cliente LLM não é chamado

### Requirement: Revisão manual nunca aciona extração

O sentinela `REVISAR_MANUAL` MUST ser tratado como uma decisão de não despachar e MUST NOT ser convertido, prefixado ou enviado ao dispatcher ou ao LLM.

#### Scenario: Sentinela de revisão manual é ignorado
- **WHEN** o frontmatter declara `skill_key: REVISAR_MANUAL`
- **THEN** a etapa registra o descarte e não chama dispatcher nem LLM

### Requirement: A rota da nova esteira não é inferida

O `skill_key` explícito produzido pelo `yaml-normalizador-juridico` MUST ser a única fonte de rota da nova esteira. Ele MUST começar com `extr-`, MUST ser usado sem transformação e MUST NOT ser derivado de `document_type`, de mapas de collectors ou de substituição entre underscores e hífens.

#### Scenario: Ausência de skill_key não inventa extrator
- **WHEN** um frontmatter aprovado possui `document_type` mas não possui `skill_key`
- **THEN** o arquivo é rejeitado de forma auditável e nenhum nome de extrator é construído

#### Scenario: Skill sem prefixo extr é rejeitada
- **WHEN** um frontmatter aprovado declara um `skill_key` que não começa com `extr-`
- **THEN** o arquivo é rejeitado sem prefixação automática e sem chamada ao LLM

### Requirement: Apenas skills registradas são resolvidas pelo runtime canônico

A nova esteira MUST resolver o `skill_key` por `platform/skill-runtime/skill_dispatcher.py`, cuja configuração canônica provém de `platform/skill-runtime/skill_registry.yaml`. Uma skill não registrada MUST ser rejeitada por arquivo e MUST NOT chegar ao LLM.

#### Scenario: Skill registrada é resolvida pelo dispatcher
- **WHEN** um arquivo elegível declara um `skill_key` presente no registro
- **THEN** o `SkillDispatcher` resolve esse identificador e fornece prompt, perfil e `schema_ref` para a extração

#### Scenario: Skill não registrada é rejeitada
- **WHEN** um arquivo elegível declara `skill_key: extr-inexistente`
- **THEN** a falha de resolução é registrada, o lote pode continuar e o cliente LLM não é chamado para esse arquivo

### Requirement: O caminho explícito do staging é a fonte de entrada

A extração MUST aceitar o caminho explícito do Markdown normalizado encontrado pela etapa de coleta e, quando fornecido, MUST ler exatamente esse arquivo em vez de procurar apenas por nome em diretórios fixos.

#### Scenario: Arquivo do staging é lido pelo caminho recebido
- **WHEN** a etapa encontra um Markdown elegível em um diretório de staging customizado e passa seu caminho explícito
- **THEN** o conteúdo enviado à extração é lido desse caminho, mesmo que exista arquivo homônimo em diretório legado

#### Scenario: Caminho explícito inexistente falha de forma controlada
- **WHEN** a extração recebe um caminho explícito que não identifica arquivo legível
- **THEN** ela registra a falha e não chama o LLM nem marca a extração como concluída

### Requirement: Resposta do LLM é validada pelo schema da skill

Antes de qualquer persistência, a extração MUST validar localmente o payload de resultado contra o schema carregado do `schema_ref` retornado pelo `SkillDispatcher`. O payload persistido MUST ser o payload que passou pela validação.

#### Scenario: Resposta válida é persistida
- **WHEN** o LLM falso retorna um objeto válido segundo o schema da skill
- **THEN** o resultado é persistido como JSON válido e a extração pode ser marcada como concluída com sucesso

#### Scenario: Validação usa o schema da skill despachada
- **WHEN** o dispatcher retorna um `schema_ref` para o bundle selecionado
- **THEN** a validação pré-persistência usa esse schema e não um schema inferido de `document_type` ou do nome do arquivo

### Requirement: Resposta inválida não se torna resultado válido

Quando o payload viola o schema da skill, a extração MUST registrar os erros de validação, MUST NOT criar, substituir ou truncar o arquivo de resultado válido e MUST NOT sinalizar conclusão bem-sucedida. A falha MUST ser controlável pelo pipeline por exceção capturável ou resultado inequívoco.

#### Scenario: Resposta inválida não é persistida
- **WHEN** o LLM falso retorna um objeto que viola um campo obrigatório ou outra restrição do schema
- **THEN** nenhum novo resultado válido é gravado, os erros são registrados e o processamento desse arquivo termina como falha controlada

#### Scenario: Resultado anterior não é truncado por resposta inválida
- **WHEN** já existe um arquivo de resultado e uma nova resposta falha na validação
- **THEN** a validação ocorre antes da abertura para escrita e o arquivo anterior permanece inalterado

### Requirement: Chamadas legadas de extração permanecem compatíveis

`DataExtractorApp.run_extraction(bundle_id, input_filename)` MUST continuar aceitando os dois argumentos legados e, na ausência de caminho explícito, MUST preservar a busca existente por nome nos diretórios configurados.

#### Scenario: Chamada legada encontra arquivo por nome
- **WHEN** um consumidor chama `run_extraction(bundle_id, input_filename)` sem caminho explícito e o arquivo existe em um dos diretórios legados suportados
- **THEN** a extração localiza o arquivo conforme a precedência existente e processa uma resposta válida

#### Scenario: Novo caminho é uma extensão aditiva da API
- **WHEN** consumidores legados usam dois argumentos posicionais e consumidores da nova esteira fornecem adicionalmente o caminho explícito por palavra-chave
- **THEN** ambas as formas são aceitas sem exigir migração imediata dos collectors legados
