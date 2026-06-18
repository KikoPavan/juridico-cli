## Why

The current JSON Schema sanitization used for Gemini Structured Outputs in [GeminiLLMClient](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L17) removes or forces type coercion on valid JSON Schema features supported by the Gemini API. Specifically, it does not support `type` arrays containing `"null"` (which are standard for nullable fields in Pydantic v2/JSON Schema) and filters out critical keys like `additionalProperties`, `title`, `minItems`, `maxItems`, `format`, `minimum`, `maximum`, and `anyOf`. Aligning the sanitizer with the current Gemini documentation ensures accurate schemas and prevents API errors or loss of schema precision.

## What Changes

- Modify [GeminiLLMClient._normalize_schema](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L699) to preserve `type` arrays containing `"null"` (e.g., `["string", "null"]` or `["integer", "null"]`) instead of coercing them to a single type.
- Update the allowed keys list in the schema sanitizer to explicitly preserve `additionalProperties`, `title`, `minItems`, `maxItems`, `format`, `minimum`, `maximum`, and `anyOf`.
- Ensure that incompatible JSON Schema features such as `$ref`, `$defs`, `oneOf`, `allOf`, `if`, `then`, `else`, and `not` remain blocked and are properly filtered out or trigger failures.
- Update tests in [test_gemini_schema_sanitizer.py](file:///home/kiko/devops/juridico-cli/tests/test_gemini_schema_sanitizer.py) to cover these new cases and prevent regressions.

## Capabilities

### New Capabilities
- `gemini-schema-alignment`: Updates the schema normalization and validation requirements for Gemini Structured Outputs, allowing nullable types, `additionalProperties`, and other advanced schema keys while strictly blocking incompatible features.

### Modified Capabilities

## Impact

- [packages/shared-llm/gemini_client.py](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py): Normalization and validation logic.
- [tests/test_gemini_schema_sanitizer.py](file:///home/kiko/devops/juridico-cli/tests/test_gemini_schema_sanitizer.py): Unit tests for schema sanitization.
