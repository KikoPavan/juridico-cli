## Context

The current schema sanitization and normalization pipeline in [GeminiLLMClient._normalize_schema](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L699) limits the JSON Schema sent to the Gemini Structured Outputs API. While the Gemini API now natively supports advanced JSON Schema features like nullable types (represented as type arrays containing `"null"`), validation constraints (`minItems`, `maxItems`, `minimum`, `maximum`, `format`), and `additionalProperties` / `anyOf` keywords, our current sanitizer must be updated to fully preserve these features while continuing to filter or reject unsupported components like `oneOf`, `allOf`, `not`, `if`, `then`, `else`, `$ref`, and `$defs`.

## Goals / Non-Goals

**Goals:**
- Preserve `type` arrays containing `"null"` (e.g. `["string", "null"]` or `["integer", "null"]`) in the schema definition.
- Preserve and forward approved JSON Schema keys: `additionalProperties`, `title`, `minItems`, `maxItems`, `format`, `minimum`, `maximum`, and `anyOf`.
- Keep incompatible JSON Schema features strictly blocked (by raising a `ValueError` during deep scan if they are present in the final sanitized schema) or filtered: `$ref`, `$defs`, `oneOf`, `allOf`, `if`, `then`, `else`, and `not`.

**Non-Goals:**
- Changing the overall fallback or retry flow of [GeminiLLMClient.generate_structured](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L39).
- Modifying production domain schemas or files under `packages/shared-schemas/`.

## Decisions

### 1. Update Allowed Keys and Keep Type Arrays Intact
We will verify that the sanitizer preserves all requested allowed keys (`additionalProperties`, `title`, `minItems`, `maxItems`, `format`, `minimum`, `maximum`, `anyOf`, and `type`). When `type` is specified as a list (e.g. `["string", "null"]`), we will ensure it is left unmodified by the sanitizer instead of being forced into a single type.

*Alternative considered*: Converting `type: ["string", "null"]` into `anyOf: [{"type": "string"}, {"type": "null"}]`.
*Rationale*: Gemini accepts type arrays with `"null"` directly, which keeps the schema flatter and less complex.

### 2. Maintain strict blocking for prohibited keywords
The deep scan check (`_scan_deep`) inside [GeminiLLMClient.generate_structured](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L39) will continue to block `$ref`, `$defs`, `oneOf`, `allOf`, `if`, `then`, `else`, and `not`. This ensures that even if these keywords are not filtered out by the sanitizer (or if they are introduced incorrectly in the final schema), the client fails-fast offline instead of generating an API error.

## Risks / Trade-offs

- **Risk:** Some legacy or local endpoints might not support type arrays with `"null"` or keys like `minItems`.
- **Mitigation:** The robust fallback pipeline (generate without response schema + block-by-block extraction) implemented in [GeminiLLMClient](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py) will automatically catch any API rejection and perform the extraction successfully.
