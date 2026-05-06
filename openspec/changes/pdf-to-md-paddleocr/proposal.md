# PDF to Markdown com PaddleOCR

## Objective

Implementar a etapa inicial do projeto: conversão de PDFs para Markdown bruto rastreável.

## Scope

- PDF digital: extração textual direta.
- PDF escaneado, ilegível ou com baixa extração textual: OCR com PaddleOCR.
- Preservação de páginas.
- Criação de anchors por página.
- Geração de Markdown bruto compatível com etapas posteriores.

## Out of scope

- Outlines.
- schemas estruturados.
- extração jurídica.
- classificação de peças.
- process-processing.
- legal-knowledge.
- RAG.
- Mem0.
- TurboQuant.
- RLM.
- alteração em runtime de skills sem necessidade validada.

## Official references

- docs/architecture/juridico_cli_documento_mestre.md
- docs/runbooks/runbook_operacional_minimo.md
- docs/reference/project_version_matrix.md
- openspec/config.yaml

## Decision

Criar um pipeline focado estritamente na conversão PDF -> MD bruto, utilizando PaddleOCR como fallback para PDFs escaneados e injetar metadados de âncoras (anchors) delimitadores de páginas para garantir rastreabilidade em etapas futuras.
