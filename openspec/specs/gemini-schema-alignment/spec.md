# gemini-schema-alignment Specification

## Purpose
TBD - created by archiving change align-gemini-structured-output-schema. Update Purpose after archive.
## Requirements
### Requirement: Support Nullable Types
The Gemini schema sanitizer in [GeminiLLMClient._normalize_schema](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L699) MUST support and preserve type arrays containing `"null"` (such as `["string", "null"]` or `["integer", "null"]`) representing nullable fields.

#### Scenario: Preserving standard string null type array
- **WHEN** the input schema has a property with `"type": ["string", "null"]`
- **THEN** the sanitized schema SHALL retain `"type": ["string", "null"]` for that property.

#### Scenario: Preserving integer null type array
- **WHEN** the input schema has a property with `"type": ["integer", "null"]`
- **THEN** the sanitized schema SHALL retain `"type": ["integer", "null"]` for that property.

### Requirement: Preserve Approved Keys
The Gemini schema sanitizer MUST preserve critical JSON Schema keys such as `additionalProperties`, `title`, `minItems`, `maxItems`, `format`, `minimum`, `maximum`, and `anyOf` in the sanitized output.

#### Scenario: Additional properties preserved
- **WHEN** the input schema specifies `"additionalProperties": false` on an object property
- **THEN** the sanitized schema SHALL preserve `"additionalProperties": false`.

#### Scenario: Verification constraints preserved
- **WHEN** the input schema defines keys like `"minItems"`, `"maxItems"`, `"format"`, `"minimum"`, `"maximum"`, `"title"`, or `"anyOf"`
- **THEN** the sanitized schema SHALL retain all of these keys in their respective properties.

### Requirement: Block Incompatible Features
The Gemini structured output system MUST enforce validation and block or filter out incompatible schema features including `$ref` (leftover after inlining), `$defs`, `oneOf`, `allOf`, `if`, `then`, `else`, and `not`.

#### Scenario: Deep scanning detects prohibited keys
- **WHEN** the sanitized schema contains any of `$ref`, `$defs`, `oneOf`, `allOf`, `if`, `then`, `else`, or `not` keys
- **THEN** the deep scan routine in [GeminiLLMClient.generate_structured](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L39) SHALL raise a `ValueError` indicating the forbidden key.

