---
doc_id: doc_arch_03
doc_type: architecture
system: juridico-cli
scope: macro
subsystem: global
version: v2.2
status: active
owner: Kiko
audience: [human, ai]
source_of_truth: sim
depends_on: [doc_prd_01, doc_data_02]
inputs: [dataset_v1_jsonl, duckdb, pack_global_json, evidence_map_json, firac_outputs]
outputs: [fluxo_end_to_end, contratos_componentes, decisoes_arquiteturais]
acceptance_criteria_ref: doc_qa_04
runbook_ref: doc_runbook_05
last_updated: 2026-01-19
tags: [arquitetura, agentes, pipelines, end-to-end]
---

## Resumo Executivo
**O que este documento é:** Arquitetura do subsistema CAD_OBR (pipelines determinísticos + Evidence-Agent + consumo pelo FIRAC).  
**Para que serve:** Documentar o “as-built” do CAD_OBR: dataset_v1 → DuckDB (views) → pack_global → evidências.  
**Entradas (inputs):** `outputs/cad_obr/04_reconciler/dataset_v1`; `artifacts/db/cad_obr_dataset_v1.duckdb`; `pack_global.json`.  
**Saídas (outputs):** views DuckDB (9); `pack_global.json`; evidências para o `firac-cli`.  
**Critérios de aceite / Validação:** Ver `04_QA...` (DuckDB ok, views presentes, pack consistente) e `05_Runbook...` (procedimento de execução).


## 0) Escopo deste documento
Este documento descreve a **Arquitetura e Design do Sistema** do projeto **juridico-cli**, cobrindo:
- arquitetura macro (end-to-end),
- componentes/fluxos,
- modelo de dados e contratos,
- governança e critérios de aceite,
- e, em apêndice, a arquitetura do **Reconciler-CLI** (sub-sistema CAD_OBR).

> Princípio base: **Divulgação Progressiva**, separando processamento determinístico (Python/DuckDB) da análise qualitativa (LLM/Gemini).

---

## 1) Objetivo do sistema
Transformar documentos jurídicos (Markdown + PDFs originais) em:
1) **dados estruturados rastreáveis** (com âncoras),
2) **mapa de evidências** e lacunas documentais,
3) **FIRAC** (matriz fatos–provas–regras),
4) **jurisprudência** selecionada (auditável),
5) **petição-esqueleto** e auditoria final (compliance).

Fluxo-alvo por fases: collectors → pipelines (reconciler/monetary) → `pack_global.json` → evidence-agent → firac-cli → case-law-cli → petition-cli → compliance-cli.

---

## 2) Pilares de arquitetura (estrutura do repo)
O projeto é dividido em quatro pilares principais: **/pipelines**, **/agents**, **/skills**, **/artifacts**.

### 2.1 Desenho — Estrutura do projeto (visual)
```text
/juridico-cli
  ├─ agents/                         # Agentes LLM (padrão 4 arquivos)
  │   ├─ collector-cad_obr/
  │   ├─ collector-proc/
  │   ├─ evidence-agent/
  │   ├─ firac-cli/
  │   ├─ case-law-cli/
  │   ├─ petition-cli/
  │   └─ compliance-cli/
  │
  ├─ pipelines/                      # Determinístico (Python)
  │   ├─ reconciler/                 # JSONL -> DuckDB (dataset_v1 etc.)
  │   ├─ monetary/
  │   ├─ evidence_pack/              # consolidator -> pack_global.json
  │   └─ jurisprudencia_ingest/      # ingestão/normalização/embeddings/Qdrant
  │
  ├─ skills/                         # Inteligência compartilhada (skill-based)
  │   ├─ extracao/
  │   ├─ analise/
  │   ├─ juridico/
  │   └─ scripts/                    # ferramentas Nível 3 (determinísticas)
  │
  ├─ artifacts/
  │   ├─ db/                         # DuckDB (verdade única)
  │   ├─ evidence_packs/
  │   ├─ evidence_outputs/
  │   └─ skills/                     # catálogo/versionamento/hash
  │
  ├─ base_juridica/                  # biblioteca jurídica (híbrida)
  │   ├─ leis/
  │   ├─ jurisprudencia/stj/
  │   ├─ jurisprudencia/stf/
  │   ├─ publicacoes/
  │   └─ manifests/                  # manifesto.yml por PDF
  │
  ├─ schemas/
  ├─ templates/
  ├─ data/
  └─ outputs/
```

---

## 3) Arquitetura macro (end-to-end)

### 3.1 Desenho — Fluxo macro (visual)

```text
[Docs Markdown brutos] + [PDFs originais]
          |
          v
(1) collectors (LLM; schema estrito; âncoras)
          |
          v
(2) pipelines (Python): reconciler/monetary -> JSONL -> DuckDB (verdade única)
          |
          +--> consolidator -> pack_global.json (artefato técnico reprodutível)
          |
          v
(3) evidence-agent (LLM) -> evidence_map.json (curto) + anexos (completos)
          |
          v
(4) firac-cli -> matriz fatos–provas–regras + relatório FIRAC
          |
          +--> (5) case-law-cli (híbrido Qdrant) -> jurisprudencia.md + jurisprudencia.json (auditável)
          |
          v
(6) petition-cli -> petição-esqueleto.md
          |
          v
(7) compliance-cli -> checklist OK/FALHA

> Note (CAD_OBR): FIRAC (Stage 4) consumes the canonical `outputs/cad_obr/05_evidence/dataset_v1/evidence_map.json`.  
> If Evidence produces legacy `evidence_out.json`, run Stage 3.5 `evidence-agent adapt` to produce `evidence_map.json` (+ `evidence_map_full.jsonl`). Details in `03A_Arquitetura_SubSistema_CAD_OBR_Pipelines_Evidence_FIRAC.md`.
```

### 3.2 Contratos comuns (agentes)

Cada agente segue o padrão de **4 arquivos**: `main.py`, `config.yaml`, `prompt.md`, `io.schema.json`.

---

## 4) Modelo de dados: “packs”, evidência e rastreabilidade

### 4.1 `pack_global.json` (definição)

`pack_global.json` é o **artefato técnico** que materializa o “pack consolidado” e garante reprodutibilidade; diferente do “Evidence Pack” (entrega).

Também deve existir a distinção: **pack mínimo para LLM** vs **pack completo para auditoria**.

### 4.2 Inputs do usuário: verdade operacional vs verdade probatória

`data/context.json` e `data/contexto_relacoes.json` entram como **premissas (verdade operacional)**; só viram “fato provado” com **documento/âncora/trecho** (verdade probatória).

### 4.3 `evidence_map.json` (saída padrão do Evidence)

O Evidence deve produzir:

* status por claim (suportado/parcial/não),
* `evidence_refs` (source_id + âncora + trecho),
* triagem P0–P3 (colheita externa só P0/P1).

### 4.4 Regra crítica: “doc consta no pack, mas não há trecho”

Se o pack lista o documento, o Evidence **não pode** afirmar “não existe documento”; deve registrar **falta de âncora/trecho**.

---

## 5) Armazenamentos e consultas

### 5.1 DuckDB (verdade única)

DuckDB atua como “verdade única”, consumindo JSONL gerados pelos pipelines, com consultas SQL rápidas para agentes/CLI.

#### 5.1.1 Estado atual (validado em 2026-01-19)
- **Arquivo DuckDB:** `artifacts/db/cad_obr_dataset_v1.duckdb`
- **Gerador (determinístico):** `pipelines/cad_obr/evidence_pack/evidence_pack_cli.py` (a partir de `outputs/cad_obr/04_reconciler/dataset_v1`)
- **Views criadas automaticamente (1:1 com os JSONL do dataset_v1):**
  - `contratos_operacoes`, `documentos`, `imoveis`, `links`, `novacoes_detectadas`, `onus_obrigacoes`, `partes`, `pendencias`, `property_events`
- **Critério de integridade no pack:** `pack_global.json → inputs.duckdb_info.status == "ok"` e `inputs.duckdb_info.files == 9`
- **Regra operacional:** não criar arquivo `.duckdb` vazio (ex.: `touch`). Se existir arquivo inválido/0 bytes, remover e regerar via pipeline.

**Mudança v2 (obrigatória):** Evidence passa a consumir **DuckDB como fonte tratada** (top-N + agregados), em vez de ler muitos JSON/JSONL diretamente.


### 5.2 Qdrant (vetorial)

Qdrant serve para busca semântica de:

* trechos do processo,
* e biblioteca jurídica (leis/jurisprudência).

---

## 6) Robustez de saída: JSON parseável e anti-truncamento

### 6.1 Contrato “JSON curto + anexos”

O Evidence entrega:

1. JSON curto (sempre parseável),
2. anexos completos fora do JSON (ex.: `evidence_map_full.jsonl`, inventário completo, queries).

### 6.2 Regras mínimas de prompt (baseline)

* máx. 6 findings; máx. 4 evidências por finding;
* trecho máx. 320 chars; 1 linha; sem aspas duplas;
* reduzir conteúdo antes de quebrar JSON; proibido texto fora do JSON.

### 6.3 Documentação obrigatória

Criar seção/página: **“Contrato de Saída e Estratégia Anti-Truncamento”** e replicar em QA/Runbook.

---

## 7) Base jurídica e jurisprudência (arquitetura híbrida)

### 7.1 Decisão: Opção C (híbrida)

Duas bibliotecas em paralelo:

* **Global:** Qdrant “biblioteca jurídica” (leis + jurisprudência geral).
* **Pack do caso:** allowlist do tema + docs do processo + itens selecionados da global.

### 7.2 Padronização de `base_juridica/` + manifesto

Cada PDF deve ter `manifesto.yml` com: tipo, tribunal, classe/número, data, tags, `sha256`, `source_id`.

### 7.3 Ingestão determinística antes do LLM

Pipeline: ingestão → normalização → embeddings → indexação (Qdrant); LLM sintetiza a partir de candidatos retornados.

### 7.4 `case-law-cli` (contrato operacional)

Corrigir contrato/prompt e padronizar:

* Entrada: questões nucleares do FIRAC + recorte fático + filtros.
* Operação: consulta semântica + filtros; ranking.
* Saídas: `jurisprudencia.md` + `jurisprudencia.json` (auditável).

---

## 8) MCP (opcional/recomendado) e Tools (CAD_OBR / Reconciler)

Para subsistemas como CAD_OBR, um MCP server pode expor:

* tools determinísticas (dataset/DB),
* tools RAG (Qdrant),
* builders (Evidence Pack / FIRAC Bridge).

### 8.1 Tools determinísticas (exemplos)

`list_datasets`, `get_document`, `get_property`, `list_onus`, `timeline`, `get_onus`, `list_novacoes`, `link_graph`.

### 8.2 Tools RAG (exemplos)

`semantic_search`, `get_chunk`, `evidence_snippets_for_onus`.

### 8.3 Builders (exemplos)

`build_evidence_pack` e `build_firac_bridge`.

---

## 9) Orquestração (LangGraph) e gates anti-alucinação

Exemplo de fluxo (CAD_OBR / Reconciler):

1. ClarifyGoal
2. DeterministicScan (dataset/DB)
3. PatternBuilder (cruzamentos)
4. RAGProof (Qdrant com filtros)
5. EvidencePack (compilação)
6. FIRACBridge
7. Output (md/json).

Gates:

* se não estiver no dataset/DB: não afirmar; registrar lacuna/narrativa,
* se não houver snippet literal: não afirmar; apenas indicar documento necessário.

---

## 10) Governança e documentação por maturidade

### 10.1) Camadas A/B/C (maturidade)

Organizar evolução em camadas e exigir que cada entrega declare a camada.

### 10.2) 4 anexos mínimos obrigatórios

* `PRD_curto.md`
* `Data_minimal.md`
* `QA_Avaliacao.md`
* `Runbook.md`

Incluindo detalhamento mínimo do Runbook/QA (monitoramento, fallback, regressão, hashes).

### 10.3) Catálogo de prompts + matriz de testes + políticas

Mudanças em prompt/skill exigem versão + QA/regressão mínima.

---

## 11) Critérios de aceite globais (sistema)

1. “Finding” só existe com evidência ancorada; senão vira lacuna/colheita P0/P1.
2. Saídas críticas: JSON sempre parseável + contrato anti-truncamento.
3. Evidence consome DuckDB (top-N/agregados) e usa “JSON curto + anexos”.
4. DuckDB (CAD_OBR) operacional: `pack_global.json` registra `inputs.duckdb_info.status = "ok"` e lista completa de views do `dataset_v1`.
5. Jurisprudência: modelo híbrido + manifesto + ingestão determinística antes do LLM.

---


## 12) Roadmap (alto nível)

F0) Documentos mínimos (PRD/Data/QA/Runbook) + Contrato Anti-Truncamento.
F1) JSONL → DuckDB + consolidator → `pack_global.json`.
F2) Evidence-Agent: DuckDB (top-N) → `evidence_map.json` + anexos.
F3) FIRAC → case-law (híbrido) → petition → compliance.
F4) Base jurídica: manifesto + ingestão determinística + indexação Qdrant.

---

## APÊNDICE A — Arquitetura do Reconciler-CLI (CAD_OBR) v2 (referência)

> Este apêndice preserva e enquadra o documento atual do Reconciler como sub-arquitetura do sistema.

### A1) Entradas e fontes de verdade

Dataset determinístico: `outputs/cad_obr/04_reconciler/dataset_v1/*.jsonl` (documentos, imóveis, partes, ônus, eventos, contratos, novações, links, pendências).
DuckDB (derivado): `artifacts/db/cad_obr_dataset_v1.duckdb` (views 1:1 com os JSONL).
Texto integral: Markdown/PDF convertidos com âncoras (R./AV./[[Folha]]).

### A2) Qdrant (payload mínimo)

Coleção `cad_obr_chunks_v1` e payload obrigatório (doc_id, source_id/sha, property_id, anchor, chunk_type, datas, onus_id, event_type).

### A3) MCP tools e LangGraph

MCP tools e fluxo LangGraph conforme seções 8 e 9.

---

### Atualização v2.2 (2026-01-19)

- DuckDB do CAD_OBR validado e operacional: `artifacts/db/cad_obr_dataset_v1.duckdb`.
- `pack_global.json` passa a registrar `duckdb_info.status = "ok"` e as views derivadas do `dataset_v1`.
- Regra operacional: nunca pré-criar `.duckdb` vazio; o arquivo deve ser criado via `duckdb.connect()` (pipeline).
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
