## ADDED Requirements

### Requirement: Recursively Sanitize anyOf Branches
O sanitizador de schema em [GeminiLLMClient._normalize_schema](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L699) MUST aplicar recursivamente a mesma filtragem de chaves usada em `properties` e `items` a cada subschema listado dentro de `anyOf`, em vez de copiar esses subschemas sem sanitização.

#### Scenario: anyOf branch with disallowed keys is sanitized
- **WHEN** um subschema dentro de `anyOf` contém chaves não presentes na lista de chaves permitidas (ex.: `pattern`, `minLength`, `maxLength`)
- **THEN** o schema sanitizado final remove essas chaves do subschema de dentro de `anyOf`, da mesma forma que removeria se estivessem em `properties`

#### Scenario: anyOf branch with allowed keys is preserved
- **WHEN** um subschema dentro de `anyOf` contém apenas chaves permitidas (ex.: `type`, `enum`, `format`)
- **THEN** o schema sanitizado final preserva essas chaves no subschema de dentro de `anyOf`
