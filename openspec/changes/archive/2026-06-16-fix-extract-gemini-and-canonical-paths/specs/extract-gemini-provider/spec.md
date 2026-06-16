# extract-gemini-provider

## ADDED Requirements

### Requirement: Extract uses provider from llm_profile

The system SHALL use the LLM provider resolved by the skill dispatcher's llm_profile when executing the extract command, instead of relying solely on the LLM_PROVIDER environment variable.

#### Scenario: Extract with high_reasoning profile uses Gemini

- GIVEN the bundle profile resolves to `high_reasoning`
- AND the profile's execution_class is `gemini_api`
- WHEN the extract command creates the LLM client
- THEN the system SHALL instantiate a `GeminiLLMClient` via `LLMClientFactory.create_client(provider_override="gemini")`
- AND the system SHALL NOT attempt to connect to any llama.cpp endpoint

#### Scenario: Provider override falls back to LLM_PROVIDER when profile lacks provider

- GIVEN the `llm_profile` has no `execution_class.provider`
- WHEN the extract command creates the LLM client
- THEN the system SHALL fall back to `os.environ.get("LLM_PROVIDER", "gemini")"

### Requirement: Extract reads from var/output/processed/

The system SHALL read the input file from `var/output/processed/` instead of `var/staging/` when executing the extract command.

#### Scenario: Extract finds file in var/output/processed/

- GIVEN the file `exemplo_clean.md` exists in `var/output/processed/`
- WHEN the extract command runs with `--input exemplo_clean.md`
- THEN the system SHALL read `var/output/processed/exemplo_clean.md`

#### Scenario: Extract exits with error when file not found

- GIVEN the file does not exist in `var/output/processed/`
- WHEN the extract command runs
- THEN the system SHALL print an error message and exit with code 1

### Requirement: Extract saves JSON to var/output/extracted/

The system SHALL save the extracted JSON to `var/output/extracted/` with the pattern `result_{bundle_id}_{input_stem}.json`.

#### Scenario: JSON is saved to extracted directory

- GIVEN the extract command completes successfully
- AND the bundle is `extr-peticao-processo`
- AND the input file is `Petição Declaração de Nulidade_clean.md`
- WHEN the extraction finishes
- THEN the output JSON SHALL be written to `var/output/extracted/result_extr-peticao-processo_Petição Declaração de Nulidade_clean.json`

### Requirement: Clean command default output directory

The clean command's `--output` default value SHALL be `var/output/processed/` instead of `var/staging/`.

#### Scenario: Clean without --output saves to var/output/processed/

- GIVEN the user runs `clean --input "var/input/md"`
- WHEN the clean command completes
- THEN the cleaned files SHALL be saved in `var/output/processed/`

#### Scenario: Clean with explicit --output uses specified path

- GIVEN the user runs `clean --input "var/input/md" --output "var/staging"`
- WHEN the clean command completes
- THEN the cleaned files SHALL be saved in `var/staging/`
