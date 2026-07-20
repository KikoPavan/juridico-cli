## Why

O processamento real de `Processo.md` já produz um envelope multipiece, mas os metadados globais, limites materializados e decisões de roteamento ainda podem divergir dos `judicial_locator` presentes no Markdown. Isso gera recortes excessivos, `total_pages` menor que páginas efetivamente usadas, códigos documentais espúrios e peças não roteáveis marcadas com impacto/status inadequados.

## What Changes

- Calcular `metadata.total_pages` de forma monotônica, nunca abaixo da maior página dos localizadores nem do maior `pages_end` materializado.
- Tratar `document_code` global como opcional e confiável somente quando representar o documento agregado; impedir promoção de fragmentos espúrios como `umento`.
- Derivar identidade e `document_code` de cada peça prioritariamente dos localizadores realmente contidos no seu texto.
- Tornar o recorte por `pages_start/pages_end` estrito: uma peça não pode incorporar segmentos iniciados por localizadores fora do intervalo, exceto separador explicitamente associado e auditado.
- Reconciliar limites do LLM com evidências reais dos localizadores e registrar ajustes de paginação/identidade em trilha de auditoria determinística.
- Manter `PED HABILIT1` como `nao_classificado` caso não exista tipo canônico seguro, evitando inferência sem contrato; impedir que essa peça seja classificada como nuclear ou pronta para extração profunda sem rota.
- Garantir que qualquer peça sem skill/encaminhamento roteável siga para síntese, revisão ou rota segura e nunca saia como `status: ready` para `extr-*`.
- Adicionar regressão multipiece e validação do fluxo `Processo.md` até envelope curado e Markdown normalizado.
- Manter fora de escopo `pdf-to-md`, `md-clean-markdown`, extratores `extr-*` e provider Gemini.
- Consultar `docs/architecture/juridico_cli_documento_mestre.md`, `docs/runbooks/runbook_operacional_minimo.md` e `docs/reference/project_version_matrix.md` durante a implementação.

## Capabilities

### New Capabilities

- `safe-unroutable-piece-handling`: define impacto, curadoria e status seguros para peças sem tipo/skill de extração reconhecida.

### Modified Capabilities

- `segmentador-juridico-output-schema`: reforça consistência entre paginação global, limites das peças, localizadores materializados e identidade documental.
- `legal-pipeline-traceability`: torna localizadores internos da peça a fonte prioritária de paginação e `document_code`, com auditoria de reconciliações.

## Impact

- Código afetado: materialização/enriquecimento em `apps/data-processing`, regras do `curador-relevancia` e status defensivo do `yaml-normalizador-juridico`.
- Contratos afetados: invariantes de `metadata.total_pages`, escopo de `document_code`, conteúdo permitido por intervalo e política de peças não roteáveis.
- Testes afetados: fixture multipiece, regressões do segmentador/curador/normalizador e execução operacional com `Processo.md`.
- Dependências locais: pressupõe as mudanças completas `fix-segmentador-materialize-multipiece-process` e `fix-segmentador-accept-process-cover-document-type`; não cria dependência externa nova.
