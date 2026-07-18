## Why

Documentos judiciais em PDF frequentemente chegam escaneados, com OCR de baixa qualidade, ligaduras tipográficas não expandidas, linhas quebradas artificialmente por extração de PDF/OCR, e páginas de separação do eproc/TJSP que não são estruturadas como metadados. Isso degrada a qualidade do Markdown enviado ao LLM para extração JSON, gerando extrações incompletas ou incorretas. A mudança é necessária agora porque o pipeline jurídico está em ativação e a qualidade da entrada é o principal gargalo.

## What Changes

- **Rejeitar documentos com apenas localizadores judiciais**: impedir que documentos sejam aceitos no pipeline quando contiverem apenas cabeçalhos processuais (ex: "Processo X, Evento Y, Documento Z, Página W") sem conteúdo útil — tanto na validação por página quanto na validação do documento completo antes da extração JSON.
- **Aprimorar OCR/fallback para anexos escaneados**: melhorar a detecção de páginas escaneadas sem texto nativo, priorizando fallback OCR e melhorando a qualidade da decisão de qual backend usar.
- **Normalizar ligaduras tipográficas**: expandir caracteres Unicode de ligadura (ﬁ, ﬂ, ﬀ, ﬃ, ﬄ, etc.) para seus equivalentes ASCII antes da limpeza e extração.
- **Recompor quebras artificiais de linha**: unir linhas quebradas por hifenização de final de linha ou por fragmentação de OCR, antes da limpeza Markdown.
- **Estruturar páginas de separação do eproc/TJSP**: extrair e estruturar como metadados: evento, título do evento, data, usuário, papel do usuário, processo e sequência.

## Capabilities

### New Capabilities
- `ligature-normalization`: Expandir ligaduras tipográficas Unicode (ﬁ, ﬂ, ﬀ, ﬃ, ﬄ, etc.) para equivalentes ASCII no pipeline de limpeza.
- `line-recomposition`: Recompor linhas quebradas artificialmente por hifenização de final de linha e por fragmentação de OCR/PDF.
- `eproc-page-structuring`: Extrair e estruturar metadados completos de páginas de separação do eproc/TJSP (evento, título, data, usuário, papel, processo, sequência).
- `document-content-validation`: Validar se o documento completo contém conteúdo útil além de localizadores judiciais, rejeitando documentos vazios ou com apenas metadados processuais antes da extração JSON.

### Modified Capabilities
- `pdf-to-md`: Melhorar detecção de páginas escaneadas sem texto nativo, priorizando fallback OCR e refinando a decisão de qualidade pós-OCR.
- `md-clean-markdown`: Adicionar estágios de normalização de ligaduras e recomposição de linhas quebradas no pipeline de limpeza.

## Impact

- **Código afetado:**
  - `platform/skills/pdf-to-md/scripts/convert_pdf_to_md.py` — validação de documento completo, OCR fallback
  - `platform/skills/md-clean-markdown/scripts/clean_markdown.py` — novas etapas de normalização
  - `packages/shared-llm/judicial_locator.py` — estruturação de metadados eproc/TJSP
  - `apps/data-processing/src/data_processing/validation/output_checks.py` — validação de conteúdo útil
  - `apps/data-processing/src/data_processing/cleaners/clean_legal_docs.py` — normalização de ligaduras
- **Testes**: novos testes para ligaduras, recomposição de linhas, validação de documento completo, estruturação eproc
- **Dependências**: nenhuma nova dependência externa prevista
- **Documentação**: SKILL.md das skills afetadas podem precisar de atualização