## MODIFIED Requirements

### Requirement: Contrato do Envelope de Processo

O `output-schema.json` SHALL descrever o Envelope de Processo `{metadata, pecas[]}` conforme documentado em `SKILL.md` e `references/variable-dictionary.md` da skill `segmentador-juridico`, incluindo os campos obrigatórios de `metadata` (`processo_id`, `total_pecas`, `gerado_por`, `timestamp`, `source_file`, `total_pages`, `schema_version`) e de cada item de `pecas[]` (`piece_id`, `document_type`, `document_type_confidence`, `pages_start`, `pages_end`, `pages_total`, `title`, `summary`, `impacto_sentenca_proposto`, `text_excerpt`, `text`, `anchors`, `observacoes`, `source_file`, `source_path`, `source_sha256`, `process_group_id`, `origin_piece_index`, `relevancia_estimada`). O enum oficial de `document_type` MUST incluir `capa_processo` e a documentação e validadores manuais da skill MUST permanecer alinhados ao schema.

#### Scenario: Exemplo de referência valida contra o schema

- **WHEN** `assets/example-output.json` é validado contra `assets/output-schema.json` usando `jsonschema.Draft7Validator`
- **THEN** a validação não produz nenhum erro

#### Scenario: Validador da skill aceita o exemplo de referência

- **WHEN** `scripts/validate_output.py assets/example-output.json` é executado usando o schema padrão
- **THEN** o processo termina com exit code `0` e imprime `[OK]`

#### Scenario: Envelope aceita capa processual

- **WHEN** uma peça materializada possui `document_type: capa_processo` e os demais campos obrigatórios válidos
- **THEN** o envelope passa pela validação canônica e pode ser persistido como `envelope_segmentacao.json`

### Requirement: O envelope materializado valida pelo schema canônico

Depois de reconstruir texto, canonicalizar aliases e enriquecer proveniência, `run_segmentador_stage()` MUST validar o envelope final usando `platform/skills/segmentador-juridico/assets/output-schema.json` antes de gravar `envelope_segmentacao.json`, incluindo documentos compostos cuja primeira peça seja `capa_processo`.

#### Scenario: Regressão unitária gera envelope válido

- **WHEN** `Petição Inicial_evento_1.md` ou fixture mínima equivalente passa por `run_segmentador_stage()`
- **THEN** o arquivo gerado contém `metadata` e `pecas`, possui texto preenchido por Python e não produz erros com `jsonschema.Draft7Validator` e o schema canônico

#### Scenario: Processo multipiece com capa gera envelope

- **WHEN** uma fixture multipiece contém uma `capa_processo` seguida por peças processuais reais e passa por `run_segmentador_stage()`
- **THEN** `envelope_segmentacao.json` é gravado, mantém a capa como primeira peça e valida contra o schema canônico

