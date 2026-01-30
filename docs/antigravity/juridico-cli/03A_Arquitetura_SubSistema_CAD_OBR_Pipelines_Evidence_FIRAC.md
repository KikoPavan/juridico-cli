---
doc_id: doc_arch_cadobr_03a
doc_type: architecture
system: juridico-cli
scope: subsystem
subsystem: cad_obr
version: v2.2
status: active
owner: Kiko
audience: [human, ai]
source_of_truth: sim
depends_on: [doc_arch_03, doc_data_02]
inputs:
  - outputs/cad_obr/04_reconciler/dataset_v1
  - artifacts/db/cad_obr_dataset_v1.duckdb
  - artifacts/evidence_packs/dataset_v1/pack_global.json   # canonical pack (source of truth)
  - outputs/cad_obr/pack_global.json                       # optional copy; non-authoritative if differs
outputs: [views_duckdb_cadobr, pack_global_json, evidencia_para_firac]
acceptance_criteria_ref: doc_qa_04
runbook_ref: doc_runbook_05
last_updated: 2026-01-28
tags: [cad_obr, reconciler, evidence_pack, duckdb, firac]
---

## Resumo Executivo
**O que este documento é:** Arquitetura do subsistema CAD_OBR (pipelines determinísticos + Evidence-Agent + consumo pelo FIRAC).  
**Para que serve:** Documentar o “as-built” do CAD_OBR: dataset_v1 → DuckDB (views) → pack_global → evidências.  
**Entradas (inputs):** `outputs/cad_obr/04_reconciler/dataset_v1`; `artifacts/db/cad_obr_dataset_v1.duckdb`; `artifacts/evidence_packs/dataset_v1/pack_global.json` (canônico).  
**Saídas (outputs):** views DuckDB (9); `pack_global.json`; evidências para o `firac-cli`.  
**Critérios de aceite / Validação:** Ver `04_QA...` (DuckDB ok, views presentes, pack consistente) e `05_Runbook...` (procedimento de execução).

## 1) Objetivo
Definir a subarquitetura CADOBR do **juridico-cli**, onde:
- **Pipelines determinísticos** geram e consolidam o dataset (`dataset_v1/*.jsonl`), constroem **DuckDB** (views) e produzem o **pack técnico** (`pack_global.json`).
- O **evidence-agent** (agente LLM) consome o DuckDB/pack para produzir **evidências rastreáveis** (com âncoras/trechos) e lacunas.
- O **firac-cli** consome as evidências (e o contexto/base jurídica) para gerar o **FIRAC**.
> Nota de estado: o antigo “reconciler-cli como agente” **não existe mais**. O reconciler é **script/pipeline**; o componente de raciocínio LLM aqui é o **evidence-agent**.

---

## 2) Entradas e Fontes de Verdade (camadas)

### 2.1) Determinístico (fatos estruturados)
Origem: `outputs/cad_obr/04_reconciler/dataset_v1/*.jsonl`
- `contratos_operacoes.jsonl`
- `documentos.jsonl`
- `imoveis.jsonl`
- `links.jsonl`
- `novacoes_detectadas.jsonl`
- `onus_obrigacoes.jsonl`
- `partes.jsonl`
- `pendencias.jsonl`
- `property_events.jsonl`
Função: responder “o que aconteceu” com IDs, datas, valores, status e vínculos (sem inferência LLM).

### 2.2) Texto integral (prova literal)
Origem: Markdown/PDF convertidos (e PDFs originais sob custódia).
Função: prover trechos literais com **âncoras** (ex.: `R.`, `AV.`, `[[Folha X]]`) para suportar achados.

### 2.3) Pack técnico (artefato de consolidação)
Origem: `artifacts/evidence_packs/dataset_v1/pack_global.json`
**Nota (cópia em outputs):**
- `outputs/cad_obr/pack_global.json` pode existir por compatibilidade/execuções antigas, mas é **não-autoritativo** quando diverge do pack canônico em `artifacts/`.
Função: materializar inventário consolidado + relatórios + ponte de inputs (dataset_dir, duckdb_path, reports_dir etc.).

---

## 3) Armazenamentos

### 3.1) Relacional (verdade única CAD_OBR: DuckDB)
- Caminho padrão: `artifacts/db/cad_obr_dataset_v1.duckdb`
- Views/tabelas espelhando 1:1 os JSONL do `dataset_v1`.
Views esperadas (v2):
- `contratos_operacoes`
- `documentos`
- `imoveis`
- `links`
- `novacoes_detectadas`
- `onus_obrigacoes`
- `partes`
- `pendencias`
- `property_events`
Objetivo:
- Consultas SQL rápidas (top-N/agregados) para reduzir leitura direta de JSONL.
- Fornecer base tratada para o **evidence-agent** e para rotinas de QA/regressão.
Chaves mínimas (conceituais):
- `doc_id`, `property_id`, `onus_id`, `parte_id`, `credor_id`
- `data_evento`, `data_registro`, `data_efetiva` (quando aplicável)

### 3.2) Vetorial (Qdrant) — opcional
Uso recomendado quando a prova literal exigir recuperação semântica (RAG) sobre os textos.
- Coleção sugerida: `cad_obr_chunks_v1`
- Payload mínimo por chunk (quando adotado):
  - `doc_id`, `source_doc_id` (ou `source_id/sha`), `property_id`, `anchor`, `chunk_type`
  - `registro_ref` (se existir), `onus_id`/`event_type` (se aplicável)
Regras:
- Consultas semânticas **sempre** com filtros (ex.: `property_id` obrigatório em perguntas por matrícula).

---

## 4) Componentes e Fluxo (alto nível)

### 4.1) Desenho — fluxo CAD_OBR (as-built)
```text
[Collectors CAD_OBR] -> (pipelines: normalize/monetary/reconciler) -> [dataset_v1/*.jsonl]
                                      |
                                      v
                               (evidence_pack) -> [DuckDB: cad_obr_dataset_v1.duckdb]
                                      |
                                      v
                                      [artifacts/evidence_packs/dataset_v1/pack_global.json]  (canonical pack; optional non-authoritative copy: outputs/cad_obr/pack_global.json)
                                      |
                                      v
                               [evidence-agent] -> evidence_out.json (+ anexos; export evidence_map.json opcional)
                                      |
                                      v
                                  [firac-cli] -> FIRAC-Plus (enriquecimento opcional; FIRAC-Core é process-first via collector-proc)
```

### 4.2) Responsabilidades
- **pipelines/**
  - produzir JSONL consistentes (schema-driven) e derivados (normalize/monetary/reconciler)
  - construir DuckDB views (a partir do dataset_v1)
  - gerar `pack_global.json`

- **evidence-agent/** (LLM)
  - consumir DuckDB/pack para gerar **evidência rastreável**
  - aplicar política anti-truncamento (JSON curto + anexos)
  - registrar lacunas (P0–P3) sem inventar fatos

- **firac-cli/** (LLM ou híbrido)
  - transformar evidências em matriz FIRAC (fatos–provas–regras–análise–conclusão)
  - citar referências (anchors/source_id) e separar “premissa” vs “prova”

---

## 5) Contratos de saída (mínimos)

### 5.1) Evidence (saída canônica do evidence-agent)
Saída canônica (recomendada):
- `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json` (curto, sempre parseável; findings + inventário + recomendações P0/P1)
- anexos (completos): inventário detalhado, tabelas, extrações, logs/queries
Regras operacionais:
- **“Verdade operacional”:** tratar premissas do usuário como base de priorização, sem questionar.
- **“Verdade probatória”:** findings só existem quando houver evidência ancorada no pack/dataset.
- Recomendar colheita externa somente para P0/P1 e com finalidade clara (evitar custo/tempo inútil).

### 5.1.1) Evidence Map Export (Manual) — OPTIONAL BRIDGE (Stage 3.5)
**Why:** Alguns consumidores preferem um contrato "claims/supports". Isso é um **export/view opcional**, não o canônico do Evidence.
- **Command:** `evidence-agent adapt` (quando existir)
- **Input (canônico):**
  - `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json`
- **Optional Outputs (export/view):**
  - `outputs/cad_obr/05_evidence/dataset_v1/evidence_map.json`
  - `outputs/cad_obr/05_evidence/dataset_v1/evidence_map_full.jsonl`
- **Rule:** FIRAC-Core **não depende** desse export. O export só enriquece consumidores opcionais.

### 5.2) FIRAC (process-first)
- **FIRAC-Core (obrigatório):**
  - Entrada: `outputs/processo/collector_out_processo_consolidado_v1.json` (ou equivalente consolidado do collector-proc)
  - Saídas:
    - `outputs/relatorio_firac.json` (canônico)
    - `outputs/relatorio_firac.md` (humano)

- **FIRAC-Plus (opcional, quando CAD_OBR existir):**
  - Pode incorporar:
    - `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json` (triagem/inventário)
    - `outputs/cad_obr/05_evidence/dataset_v1/evidence_map.json` (export/view, se existir)
  - Regra: não bloqueia se não existir (FIRAC-Core sempre roda).

---

## 6) (Opcional) MCP Server e Tools
Se/when o projeto adotar MCP, a recomendação é que o MCP exponha **somente tools determinísticas** e de consulta, mantendo o raciocínio no agente.
Tools candidatas:
- SQL/DuckDB: `sql_query(query, params)`
- Dataset: `get_onus(onus_id)`, `timeline(property_id, ...)`, `list_onus(property_id, ...)`
- RAG (se Qdrant estiver ativo): `semantic_search(query, filters, top_k)`
> Estado: opcional. Não é pré-requisito para o fluxo atual (pipelines + evidence-agent + firac-cli).

---

## 7) QA e critérios de aceite (CAD_OBR)
Aceite técnico mínimo:
1) Pack canônico gerado e consistente:
   - `artifacts/evidence_packs/dataset_v1/pack_global.json` (source of truth)
   - Se existir `outputs/cad_obr/pack_global.json`, ele é **não-autoritativo** quando divergir do canônico.
2) DuckDB válido e carregado:
   - arquivo existente e não-vazio
   - `duckdb_info.status == "ok"`
   - `files == 9` e lista de `views` compatível
3) Evidence:
   - JSON curto sempre parseável
   - evidências com `source_doc_id`/`source_path` + `anchor` (quando aplicável)
   - lacunas classificadas (P0–P3)

---

## 8) Plano de execução (sequência curta)
1) Gerar/atualizar `dataset_v1/*.jsonl` via pipelines.
2) Executar `evidence_pack_cli.py` para gerar DuckDB + pack canônico:
   - `artifacts/db/cad_obr_dataset_v1.duckdb`
   - `artifacts/evidence_packs/dataset_v1/pack_global.json`
   - (Opcional) `outputs/cad_obr/pack_global.json` pode ser criado como cópia, mas não é canônico.
3) (Opcional / quando CAD_OBR existir) Rodar `evidence-agent` e produzir `evidence_out.json` (canônico, JSON curto) + anexos.
4) (Opcional) Rodar `evidence-agent adapt` para export `evidence_map.json` + `evidence_map_full.jsonl` (export/view; não-gate).
5) Rodar `firac-cli`:
   - FIRAC-Core (principal): consome saída do `collector-proc` (process-first) e produz FIRAC.
   - FIRAC-Plus (opcional): se existirem `evidence_out.json` (e/ou `evidence_map.json` como export), incorporar para enriquecer; ausência não bloqueia.
6) Regressão: casos sensíveis (ex.: arrendamento mercantil; relevância de restrições judiciais; datas efetiva vs registro).

---

## 9) Próximo passo imediato
1) Fixar o contrato canônico do Evidence: `evidence_out.json` + anexos (sempre parseável).
2) Manter `evidence-agent adapt` (Stage 3.5) como export/view opcional (`evidence_map.json` + `evidence_map_full.jsonl`) para integrações.
3) Formalizar contrato do FIRAC-Plus: como o `firac-cli` incorpora Evidence quando existir, sem bloquear FIRAC-Core (collector-proc).

---

## Glossário mínimo (termos operacionais)
- **Fonte probatória (PDF original):** documento original que pode ser anexado em petição; serve como prova primária.
- **Fonte operacional (Markdown):** versão convertida do PDF usada para extração; não substitui a prova.
- **source_id:** identificador estável do documento/trecho (normalmente derivado de hash + metadados), usado para rastreabilidade.
- **anchor (âncora):** referência localizável no texto (ex.: `[[Folha X]]`, `[Pág. Y]`), usada para apontar evidência.
- **Evidence Pack (`pack_global.json`):** pacote consolidado do caso contendo dataset, índices e relatórios (inventário/visões) para consumo por agentes.
- **dataset_v1 (`*.jsonl`):** conjunto tabular mínimo (JSON Lines) gerado pelo reconciler/pipeline, base para DuckDB e relatórios.
- **DuckDB:** banco local que materializa `dataset_v1` em views/tabelas para consultas (top-N, agregações, filtros).
- **evidence_out.json:** saída canônica do Evidence-Agent (findings + inventário + recomendações P0/P1), sempre parseável.
- **evidence_map.json:** export/view opcional (claims + supports com `source_id` + anchors) para integrações; não é gate do FIRAC-Core.
- **Finding:** apontamento relevante para o caso (ex.: inconsistência, ausência, indício) sempre com suporte rastreável.
- **Fallback (modo degradado):** execução limitada quando um componente falha (ex.: sem DuckDB), priorizando inventário e recomendações.
