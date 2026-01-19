---
doc_id: doc_runbook_05
doc_type: runbook
system: juridico-cli
scope: macro
subsystem: global
version: v2.1
status: active
owner: Kiko
audience: [human, ai]
source_of_truth: sim
depends_on: [doc_arch_03, doc_data_02, doc_qa_04]
inputs: [comandos_execucao, paths_artefatos, limites_operacionais]
outputs: [procedimentos_operacao, fallbacks, resposta_incidente]
acceptance_criteria_ref: doc_qa_04
runbook_ref: doc_runbook_05
last_updated: 2026-01-19
tags: [operacao, runbook, fallback, anti-truncamento]
---

## Resumo Executivo
**O que este documento é:** Runbook operacional do pipeline (execução, fallbacks, incident response, anti-truncamento).  
**Para que serve:** Padronizar operação local e diagnóstico rápido de falhas.  
**Entradas (inputs):** comandos de execução; paths de artefatos; limites de saída (JSON curto + anexos).  
**Saídas (outputs):** procedimentos passo-a-passo; plano de fallback; checklist de incidentes.  
**Critérios de aceite / Validação:** Ver `04_QA...` (passar checks após cada execução relevante).

## 1) Visão operacional

Pipeline (ordem):

1. collector-*
2. pipelines (normalize/monetary/reconciler) → dataset_v1
3. load DuckDB
4. gerar `pack_global.json` (pack mínimo + anexos completos)
5. evidence-agent → FIRAC → petition

## 2) Política anti-truncamento (obrigatória)

**Regra de ouro:** JSON final do LLM é **curto**; detalhamento é **anexo**.

Orçamento padrão do evidence-agent:

* findings ≤ 6 (preferir 4 em caso denso)
* evidências por finding ≤ 4 (preferir 3 em caso denso)
* `documentos_apresentados.lista` ≤ 20
* `documentos_faltantes` ≤ 15
* `documentos_recomendados_para_colheita` ≤ 15
* `trecho` ≤ 320 chars, 1 linha, sem aspas duplas
* `resumo_executivo` ≤ 1000 chars, 1 linha

## 3) Logs mínimos (para auditoria e depuração)

Registrar por execução:

* versões de schemas/skills usadas
* hash do pack (`pack_global.json`) e do dataset (lista de JSONL + hash)
* caminho dos anexos gerados
* raw output do modelo (para post-mortem quando falhar)

## 4) Fallbacks (quando algo falhar)

* **DuckDB falhou / vazio inesperado**: evidence roda em modo “inventário + recomendações P0/P1”, sem findings.
* **Parsing falhou (JSON truncado)**: reduzir orçamento (4 findings, 3 evidências, 240 chars) e reexecutar.
* **Pack grande demais**: mover mais conteúdo para anexos e manter no pack apenas agregados + top-N.

## 5) Resposta a incidentes

* Classificar severidade:

  * S1: pipeline não gera outputs
  * S2: outputs gerados mas evidence não parseia
  * S3: qualidade (findings sem evidência, recomendações excessivas)
* Procedimento:

  1. identificar etapa que falhou
  2. coletar logs + raw + hash do pack
  3. corrigir e revalidar com QA “caso denso”
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
