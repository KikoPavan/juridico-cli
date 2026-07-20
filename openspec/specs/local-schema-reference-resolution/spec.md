# local-schema-reference-resolution Specification

## Purpose

Garantir que a resolução de `$ref` em schemas JSON dos extratores `extr-*` ocorra exclusivamente a partir de arquivos locais do repositório, sem qualquer acesso à rede, com ponto de partida previsível e falha controlada quando a referência não puder ser resolvida, através de um módulo único e reutilizável.

## Requirements

### Requirement: Resolução de `$ref` de schema é exclusivamente local

Qualquer validação de payload contra um schema JSON dos extratores `extr-*` MUST resolver referências (`$ref`) usando apenas arquivos presentes no repositório, tanto na forma relativa (`defs/common.schema.json#/$defs/X`) quanto na forma absoluta pelo `$id` canônico (`https://juridico-cli.local/schemas/defs/common.schema.json#/$defs/X`). A resolução MUST NOT realizar nenhuma chamada de rede, mesmo quando o `$ref` aponta para uma URI `https://`.

#### Scenario: Ref relativo para common.schema.json é resolvido localmente
- **WHEN** um schema principal com `$id` sob `https://juridico-cli.local/schemas/` contém `"$ref": "defs/common.schema.json#/$defs/NonEmptyString"`
- **THEN** a validação resolve essa referência lendo `packages/shared-schemas/defs/common.schema.json` do disco, sem tentar acesso à rede

#### Scenario: URI absoluta juridico-cli.local é mapeada para o arquivo local
- **WHEN** um schema contém `"$ref": "https://juridico-cli.local/schemas/defs/common.schema.json#/$defs/NonEmptyString"`
- **THEN** a validação resolve essa referência para o mesmo arquivo local `packages/shared-schemas/defs/common.schema.json`, sem diferença de comportamento em relação ao `$ref` relativo equivalente

#### Scenario: Validação funciona sem acesso à internet
- **WHEN** a validação de um payload contra um schema com `$ref` compartilhado é executada em um ambiente sem acesso à rede
- **THEN** a validação completa com sucesso ou falha apenas por motivos de conteúdo do payload, nunca por indisponibilidade de rede

### Requirement: Ponto de partida da resolução é o diretório do schema validado

A resolução de `$ref` relativo MUST considerar primeiro o diretório do arquivo de schema principal sendo validado (o mesmo caminho retornado como `schema_ref` pelo `SkillDispatcher`) e, quando o arquivo referenciado não existir ali, MUST cair para o diretório canônico de schemas compartilhados do repositório (`packages/shared-schemas/`).

#### Scenario: Schema principal referencia common.schema.json a partir do seu próprio schema_ref
- **WHEN** a validação recebe o caminho de schema retornado por `SkillDispatcher.dispatch(...)["skill_config"]["schema_ref"]` e esse schema contém `$ref` relativo para `defs/common.schema.json`
- **THEN** a busca do arquivo referenciado parte do diretório desse `schema_ref` antes de recorrer ao diretório canônico compartilhado

### Requirement: Referência não resolvível produz falha controlada

Quando um `$ref` não pode ser resolvido nem no diretório do schema principal nem no diretório canônico de schemas compartilhados, a resolução MUST levantar um erro específico e legível (identificando a URI ou caminho que faltou) em vez de tentar rede, retornar silenciosamente um schema parcial, ou deixar a exceção genérica da biblioteca `jsonschema`/`referencing` propagar sem contexto.

#### Scenario: Ref para arquivo inexistente gera erro controlado
- **WHEN** um schema contém `$ref` para um arquivo que não existe nem localmente nem no diretório compartilhado
- **THEN** a resolução levanta um erro específico contendo a referência não resolvida, e nenhuma exceção de rede ou timeout é produzida

### Requirement: Resolução é centralizada e reutilizável

A lógica de resolução local de `$ref` MUST existir em um único módulo compartilhado, usado tanto pela validação pré-persistência da extração quanto por qualquer validação auxiliar/offline de schema no cliente LLM. Extratores individuais e clientes de LLM MUST NOT reimplementar seu próprio mapeamento de `$id`/`$ref` para arquivos locais.

#### Scenario: Cliente LLM e extração usam a mesma resolução
- **WHEN** tanto a validação offline interna do cliente LLM quanto a validação final pré-persistência da extração processam um schema com `$ref` para `defs/common.schema.json`
- **THEN** ambas resolvem a referência através do mesmo módulo compartilhado de resolução, sem lógica de mapeamento duplicada entre os dois pontos de chamada
