---
doc_id: doc_data_02
doc_type: data_governance
system: juridico-cli
scope: macro
subsystem: global
version: v2.1
status: active
owner: Kiko
audience: [human, ai]
source_of_truth: sim
depends_on: [doc_prd_01]
inputs: [markdown_convertido, pdf_original, outputs_json, dataset_v1_jsonl, duckdb]
outputs: [regras_linhagem, contratos_minimos_dados, definicao_verdades]
acceptance_criteria_ref: doc_qa_04
runbook_ref: doc_runbook_05
last_updated: 2026-01-19
tags: [dados, linhagem, duckdb, pack_global, rastreabilidade]
---

## Resumo Executivo
**O que este documento é:** Contrato mínimo de dados (linhagem, “verdade operacional vs probatória”, artefatos e tabelas mínimas).  
**Para que serve:** Garantir consistência e auditabilidade dos dados entre pipelines e agentes.  
**Entradas (inputs):** Markdown convertido + PDF original; `dataset_v1/*.jsonl`; DuckDB.  
**Saídas (outputs):** regras de linhagem; entidades mínimas; requisitos de rastreabilidade (anchors/source_id).  
**Critérios de aceite / Validação:** Ver `04_QA...` (checagens de completude, consistência e integridade dos artefatos).


## 1) Verdades e fontes

* **Verdade operacional**: `data/context.json` + `data/contexto_relacoes.json` (premissas/questões; guiam prioridade).
* **Verdade probatória**: apenas o que tiver **referência rastreável** (documento/âncora/source_id) em dataset/DuckDB/pack.

## 2) Linhagem mínima (pipeline)

1. **Usuário/OCR → Markdown** (`data/.../*.md`)
2. **collector-* → JSON individuais** (`outputs/.../01_collector/...`)
3. **pipelines (normalize/monetary/reconciler) → JSONL dataset_v1**
   Ex.: `outputs/cad_obr/04_reconciler/dataset_v1/*.jsonl`
4. **dataset_v1 → DuckDB** (`artifacts/db/cad_obr_dataset_v1.duckdb`)
5. **DuckDB → Pack** (`artifacts/evidence_packs/dataset_v1/pack_global.json`)
6. **Pack → evidence-agent → FIRAC → petição**

## 3) Dataset_v1 (views/tabelas no DuckDB)

O pipeline `evidence_pack` gera views no DuckDB (`artifacts/db/cad_obr_dataset_v1.duckdb`), espelhando 1:1 os arquivos JSONL do `outputs/cad_obr/04_reconciler/dataset_v1/`.

Views (validadas em 2026-01-19):

- `documentos` — inventário documental
- `links` — ligações doc↔entidade↔evento
- `imoveis` — matrículas/ativos
- `partes` — pessoas/empresas/credor/devedor
- `onus_obrigacoes` — ônus, dívidas, garantias, status, valores
- `novacoes_detectadas` — cadeias/transformações de dívida
- `property_events` — eventos cronológicos por matrícula
- `contratos_operacoes` — operações/contratos relevantes
- `pendencias` — lacunas/pendências geradas por reconciliação

**Campos mínimos (contrato conceitual)**
Sem impor nome exato, mas o dataset deve permitir:

* Identificadores estáveis (`*_id`, `property_id`, `doc_id`)
* Datas relevantes (efetiva/registro/vencimento/baixa quando aplicável)
* Valores (original, convertido, presente quando aplicável)
* Referência rastreável (ex.: `source_id`, `referencia`, `ancora`, `doc_ref`)

## 4) O que é Pack e como evitar truncamento

### 4.1 Pack Global (consolidado)

`pack_global.json` é o **objeto único** consumido por agentes LLM (evidence/firac/case-law/petition).
Ele deve ser **gerado por código determinístico** a partir do DuckDB + contexto do usuário.

### 4.2 Pack mínimo para LLM (obrigatório)

Para evitar truncamento e manter previsibilidade, o pack entregue ao LLM deve conter:

* **Agregados** (contagens por tipo/status; resumos por matrícula; flags de inconsistência)
* **Top-N exemplos** (poucos itens representativos por categoria)
* **Inventário limitado** (top-N documentos, com contagem total)
* **P0/P1 do usuário** (premissas e questões priorizadas)

### 4.3 Pack completo (anexos)

Tudo que exceder os limites deve ir para anexos em `outputs/.../05_evidence/dataset_v1/` (ou pasta equivalente), por exemplo:

* `inventario_documental_full.jsonl`
* `evidence_map_full.jsonl`
* `timeline_full.jsonl`

O JSON final do evidence-agent **referencia** esses anexos em texto (ex.: “lista truncada; ver anexo X”).

## 5) Regras de rastreabilidade

* Nenhum finding sem evidência ancorada.
* Se “documento consta no PACK, mas sem âncora/trecho”, não é “inexistente”: vira lacuna probatória e, se P0/P1, **recomendação de colheita**.

## 6) Regra operacional do DuckDB (importante)

- O arquivo `.duckdb` **não** deve ser pré-criado vazio (ex.: `touch`).
- Se existir um `.duckdb` inválido/0 bytes, remover e regerar via `pipelines/cad_obr/evidence_pack/evidence_pack_cli.py` apontando para `dataset_v1`.
- Critério de integridade: `pack_global.json → inputs.duckdb_info.status == "ok"` e `inputs.duckdb_info.files == 9`.
---
## Glossário mínimo (termos operacionais)
- **Fonte probatória (PDF original):** documento original que pode ser anexado em petição; serve como prova primária.
- **Fonte operacional (Markdown):** versão convertida do PDF usada para extração; não substitui a prova.
- **source_id:** identificador estável do documento/trecho (normalmente derivado de hash + metadados), usado para rastreabilidade.
- **anchor (âncora):** referência localizável no texto (ex.: `[[Folha X]]`, `[Pág. Y]`), usada para apontar evidência.
- **Evidence Pack (`pack_global.json`):** pacote consolidado do caso contendo dataset, índices e relatórios (inventário/visões) para consumo por agentes.
- **dataset_v1 (`*.jsonl`):** conjunto tabular mínimo (JSON Lines) gerado pelo reconciler/pipeline, base para DuckDB e relatórios.
- **DuckDB:** banco local que materializa `dataset_v1` em views/tabelas para consultas (top-N, agregações, filtros).
- **evidence_map.json:** saída do Evidence-Agent com alegações (claims) + suportes (support) apontando `source_id` + anchors.
- **Finding:** apontamento relevante para o caso (ex.: inconsistência, ausência, indício) sempre com suporte rastreável.
- **Fallback (modo degradado):** execução limitada quando um componente falha (ex.: sem DuckDB), priorizando inventário e recomendações.
