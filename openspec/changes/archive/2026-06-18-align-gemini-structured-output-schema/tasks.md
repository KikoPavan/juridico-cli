## 1. Implement Gemini Schema Alignment

- [x] 1.1 Update allowed keys in [GeminiLLMClient._normalize_schema](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L699) to explicitly preserve additionalProperties, title, minItems, maxItems, format, minimum, maximum, and anyOf.
- [x] 1.2 Modify [GeminiLLMClient._normalize_schema](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L699) and its internal `_sanitize` function to preserve `type` arrays containing `"null"` (e.g. `["string", "null"]`) instead of coercing them to a single string type.
- [x] 1.3 Ensure deep scanning in [GeminiLLMClient.generate_structured](file:///home/kiko/devops/juridico-cli/packages/shared-llm/gemini_client.py#L39) continues to block all incompatible keys ($ref, $defs, oneOf, allOf, if, then, else, not).

## 2. Verification and Testing

- [x] 2.1 Update [test_gemini_schema_sanitizer.py](file:///home/kiko/devops/juridico-cli/tests/test_gemini_schema_sanitizer.py) to add unit tests covering nullable type arrays (e.g., `["string", "null"]` and `["integer", "null"]`).
- [x] 2.2 Add unit tests in [test_gemini_schema_sanitizer.py](file:///home/kiko/devops/juridico-cli/tests/test_gemini_schema_sanitizer.py) validating the preservation of the newly allowed keys (`additionalProperties`, `title`, `minItems`, `maxItems`, `format`, `minimum`, `maximum`, `anyOf`).
- [x] 2.3 Add unit tests verifying that incompatible keys ($ref, $defs, oneOf, allOf, if, then, else, not) are still correctly rejected during the deep scan.
- [x] 2.4 Run the test suite using `.venv/bin/pytest tests/test_gemini_schema_sanitizer.py` to ensure all tests pass successfully.
