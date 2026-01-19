---
doc_id: doc_qa_04
doc_type: qa
system: juridico-cli
scope: macro
subsystem: global
version: v2.1
status: active
owner: Kiko
audience: [human, ai]
source_of_truth: sim
depends_on: [doc_prd_01, doc_arch_03, doc_data_02]
inputs: [artefatos_pipeline, outputs_agentes, logs_execucao]
outputs: [checklists, criterios_aceite, cenarios_regressao]
acceptance_criteria_ref: doc_qa_04
runbook_ref: doc_runbook_05
last_updated: 2026-01-19
tags: [qa, aceite, regressao, validacao]
---

## Resumo Executivo
**O que este documento é:** Matriz de QA com critérios de aceite e cenários de regressão do sistema e dos agentes.  
**Para que serve:** Evitar regressões e garantir que cada saída é parseável, rastreável e consistente.  
**Entradas (inputs):** `pack_global.json`; `evidence_map.json` e anexos; outputs FIRAC/petição; logs.  
**Saídas (outputs):** checklists; testes mínimos; regras de falha/bloqueio; métricas de qualidade.  
**Critérios de aceite / Validação:** Este documento é a referência de validação (executar checks antes de promover versões).

## 1) Objetivo

Garantir que o pipeline rode ponta-a-ponta com:

* saídas parseáveis,
* rastreabilidade mínima,
* regressão controlada quando skills/schemas mudarem.

## 2) Conjuntos mínimos de teste

Use 3 pacotes/datasets representativos:

1. **Caso “mínimo”** (poucos docs, poucos ônus)
2. **Caso “com lacunas”** (pendências presentes)
3. **Caso “denso”** (muitos ônus/eventos — teste de truncamento)

## 3) Matriz de checks (binária)

**Collector**

* Extrai fatos literais sem inferência
* Preserva referência (página/folha/âncora quando existir)
* JSON válido e conforme schema

**Pipelines (normalize/monetary/reconciler)**

* Geram `dataset_v1/*.jsonl` completos
* Coerência mínima: ids estáveis; datas parseáveis; valores coerentes
* Produzem `pendencias.jsonl` quando faltam peças para prova

**DuckDB**

* Consegue carregar todas as tabelas do `dataset_v1`
* Consultas de agregação retornam linhas (não vazio inesperado)

**Pack**

* `pack_global.json` gerado sem duplicidade grosseira
* Pack mínimo tem agregados + top-N + inventário limitado + P0/P1

**Evidence-Agent**

* **Sempre retorna JSON parseável**
* Respeita orçamento:

  * findings ≤ 6
  * evidências/finding ≤ 4
  * inventário lista ≤ 20
* Não cria finding sem evidência
* Gera recomendações P0/P1 padronizadas

**FIRAC / Petition**

* Não afirma sem referência ao FIRAC/jurisprudência
* Mantém conectores e remissões (rastreabilidade textual)

## 4) Critérios de aceite

* 0 falhas de parsing em 10 execuções seguidas no caso “denso”
* 100% findings com evidência ancorada
* Recomendações externas apenas P0/P1
* Logs e hashes presentes quando aplicável
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
