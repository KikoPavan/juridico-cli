## MODIFIED Requirements

### Requirement: Resposta do LLM é validada pelo schema da skill

Antes de qualquer persistência, a extração MUST validar localmente o payload de resultado contra o schema carregado do `schema_ref` retornado pelo `SkillDispatcher`. Essa validação MUST resolver localmente qualquer `$ref` compartilhado presente no schema (ex.: `defs/common.schema.json`), sem realizar nenhuma tentativa de acesso à rede, usando a resolução centralizada de referências de schema. O payload persistido MUST ser o payload que passou pela validação.

#### Scenario: Resposta válida é persistida
- **WHEN** o LLM falso retorna um objeto válido segundo o schema da skill
- **THEN** o resultado é persistido como JSON válido e a extração pode ser marcada como concluída com sucesso

#### Scenario: Validação usa o schema da skill despachada
- **WHEN** o dispatcher retorna um `schema_ref` para o bundle selecionado
- **THEN** a validação pré-persistência usa esse schema e não um schema inferido de `document_type` ou do nome do arquivo

#### Scenario: Schema com $ref compartilhado é validado sem acesso à rede
- **WHEN** o schema apontado por `schema_ref` contém `$ref` relativo ou absoluto para `defs/common.schema.json`
- **THEN** a validação resolve essa referência localmente e conclui com base apenas no conteúdo do payload, sem depender de conectividade de rede
