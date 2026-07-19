## ADDED Requirements

### Requirement: Judicial locators survive the legal pipeline

The `segmentador-juridico → curador-relevancia → yaml-normalizador-juridico` pipeline SHALL preserve every structured `[[judicial_locator: ...]]` marker already present in the piece text through to the final Markdown body.

#### Scenario: Full locator survives normalization
- **WHEN** the input text contains `[[judicial_locator: process_number="4000153-37.2026.8.26.0136/SP", event="1", document_code="INIC1", page="1"]]`
- **THEN** the final Markdown body contains that marker with the same attributes and values

### Requirement: Generated anchors include available judicial identity

When the legal pipeline generates an anchor, it MUST include `page`, `process_number`, `event`, and `document_code` whenever each respective value is available from the piece, envelope metadata, or existing locator. The pipeline MUST NOT replace an existing non-null anchor attribute with null.

#### Scenario: Generated anchor is enriched from available metadata
- **WHEN** an anchor is generated for page `1` and the available metadata contains process `4000153-37.2026.8.26.0136/SP`, event `1`, and document code `INIC1`
- **THEN** the generated anchor carries `page="1"`, `process_number="4000153-37.2026.8.26.0136/SP"`, `event="1"`, and `document_code="INIC1"`

#### Scenario: Partial metadata still produces a valid anchor
- **WHEN** an anchor is generated with only page `3` available
- **THEN** the generated anchor carries `page="3"` and does not invent process, event, or document values

