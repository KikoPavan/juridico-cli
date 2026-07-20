## ADDED Requirements

### Requirement: Referência interna (`#/$defs/...`) resolve contra o schema efetivamente validado

Ao validar um payload contra um schema JSON, o resolvedor local MUST registrar o próprio documento de schema recebido (em memória) como recurso resolvível sob seu `base_uri` efetivo, de modo que qualquer `$ref` iniciado por `#` (ex.: `#/$defs/PeticaoIdentification`) resolva contra esse documento independentemente de o caminho de schema (`schema_path`) informado pelo chamador apontar corretamente para o diretório real do arquivo em disco.

#### Scenario: Ref interno resolve com schema_path apontando para o diretório correto
- **WHEN** a validação recebe o schema de `extr-peticao-processo` e `schema_path` aponta para o diretório real desse schema
- **THEN** `#/$defs/PeticaoIdentification` resolve com sucesso contra o próprio schema raiz

#### Scenario: Ref interno resolve mesmo com schema_path apontando para outro diretório
- **WHEN** a validação recebe o mesmo schema de `extr-peticao-processo`, mas `schema_path` é informado como o diretório canônico de schemas compartilhados (`packages/shared-schemas/`), reproduzindo o padrão de chamada usado pela validação offline do cliente Gemini
- **THEN** `#/$defs/PeticaoIdentification` e qualquer outro `$ref` interno ao schema raiz (ex.: `#/$defs/AnchoredString`) ainda resolvem com sucesso, sem levantar `SchemaReferenceError`

### Requirement: Cadeias de referência entre schemas locais são resolvidas

O resolvedor local MUST suportar cadeias de referência que atravessam múltiplos documentos: um `$ref` no schema raiz para um arquivo externo local, cujo conteúdo por sua vez contém um fragmento interno (`#/$defs/...`) resolvido dentro daquele mesmo arquivo externo.

#### Scenario: Fragmento interno em schema externo carregado por $ref
- **WHEN** um schema local é carregado via `$ref` relativo a partir do schema raiz e esse schema externo contém, em seu próprio corpo, uma referência interna (`#/$defs/...`) para uma definição sua
- **THEN** a referência interna do schema externo resolve corretamente contra o documento externo, sem precisar de lógica adicional no schema raiz

#### Scenario: Cadeia raiz → arquivo externo → fragmento interno
- **WHEN** o schema raiz referencia um arquivo externo local por `$ref`, e a resolução dessa referência precisa então localizar um fragmento interno específico dentro do arquivo externo
- **THEN** o resolvedor completa a cadeia inteira (raiz → arquivo externo → fragmento) sem acesso à rede e sem erro

### Requirement: JSON Pointer com segmentos escapados é resolvido corretamente

A resolução de fragmento (JSON Pointer) MUST decodificar corretamente os segmentos escapados definidos pela RFC 6901 (`~0` para `~` e `~1` para `/`) ao navegar por `$defs` ou qualquer outra chave do schema.

#### Scenario: Ponteiro com ~0 e ~1 resolve para a chave correta
- **WHEN** um schema define, sob `$defs`, uma chave cujo nome contém os caracteres `~` ou `/` (codificados como `~0`/`~1` no `$ref`)
- **THEN** o resolvedor localiza a definição correta usando o JSON Pointer decodificado, sem erro de referência não resolvível

### Requirement: Fragmento inexistente falha de forma controlada sem acesso à rede

Quando o documento-base de um `$ref` é resolvido, mas o fragmento (JSON Pointer) apontado não existe naquele documento, o resolvedor MUST levantar `SchemaReferenceError` com informação legível sobre a referência que faltou, e MUST NOT tentar qualquer acesso de rede antes de falhar.

#### Scenario: Fragmento ausente no schema raiz
- **WHEN** um schema contém `"$ref": "#/$defs/NaoExiste"` e essa chave não existe em `$defs` do documento
- **THEN** a validação levanta `SchemaReferenceError` identificando a referência não resolvida, sem qualquer tentativa de conexão de rede
