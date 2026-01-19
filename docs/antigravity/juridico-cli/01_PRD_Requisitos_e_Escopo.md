---
doc_id: doc_prd_01
doc_type: prd
system: juridico-cli
scope: macro
subsystem: global
version: v2.2
status: active
owner: Kiko
audience: [human, ai]
source_of_truth: sim
depends_on: []
inputs: [objetivos_negocio, restricoes_operacionais]
outputs: [lista_de_entregaveis, criterios_de_sucesso, escopo_fases]
acceptance_criteria_ref: doc_qa_04
runbook_ref: doc_runbook_05
last_updated: 2026-01-19
tags: [prd, requisitos, escopo, kpis]
---
## Resumo Executivo
**O que este documento é:** PRD do juridico-cli com objetivos, escopo, entregáveis e critérios de sucesso.  
**Para que serve:** Definir o “porquê” e o “o quê” do sistema para orientar implementação e priorização.  
**Entradas (inputs):** necessidade do caso; restrições operacionais; premissas de rastreabilidade.  
**Saídas (outputs):** lista de entregáveis; KPIs/definição de pronto; roadmap de fases.  
**Critérios de aceite / Validação:** Ver `04_QA_Avaliacao_Criterios_de_Aceite_e_Regressao.md` (conformidade das saídas e regressão mínima).

## 1) Objetivo

Construir um pipeline local (juridico-cli) que transforma documentos jurídicos (Markdown + dataset estruturado) em:

* **Relatório de Evidências** (evidence-agent)
* **Matriz FIRAC** (firac-cli)
* **Petição-esqueleto** (petition-cli)
  com **rastreabilidade (âncoras/source_id)** e **priorização de colheita documental (P0/P1)**.

## 2) Problema que resolve

* Hoje a colheita de documentos e a montagem de evidências tende a ser ampla, lenta e com risco de “levantar documentação irrelevante”.
* O projeto precisa **triagem objetiva**: o que é relevante (P0/P1) e o que tem prova ancorada vs o que apenas é premissa e exige colheita.

## 3) Usuários e uso

* **Usuário operador (você)**: roda pipeline, alimenta contexto, revisa outputs.
* **Jurídico/advogado**: usa FIRAC + petição-esqueleto para revisão e protocolo.
* **Apoio/perícia**: usa anexos (inventário completo, mapas de evidências, linhas do tempo).

## 4) Escopo

Inclui:

* Ingestão (Markdown) → extrações (collector-*) → normalização/cálculo/reconciliação (pipelines) → **DuckDB “verdade única”** → **Pack** → evidence/firac/petição.
* Jurisprudência: seleção via **case-law-cli** usando base local (base_juridica + Qdrant).

Não inclui (fora de escopo agora):

* Automação de busca web aberta (somente base local / conectores controlados).
* Substituir revisão humana final.
* Decidir “veracidade”: o sistema trata premissas do usuário como **verdade operacional** e exige prova documental para findings.

## 5) Artefatos de saída (contratos)

* `artifacts/db/*.duckdb` (verdade única)
* `artifacts/evidence_packs/pack_global.json` (pack consolidado)
* `outputs/.../dataset_v1/*.jsonl` (dataset estruturado)
* `outputs/.../evidence/*.json` + anexos (`*.jsonl`, `*.md`) quando necessário
* `outputs/firac/*.md` e `outputs/peticao/*.md`

## 6) KPIs (mínimo)

* **Confiabilidade**: 100% das saídas LLM parseáveis (JSON válido quando exigido).
* **Cobertura P0/P1**: % de premissas P0/P1 com “documento recomendado” definido e justificativa.
* **Rastreabilidade**: % de findings com evidência ancorada (source_id/âncora/referência).
* **Eficiência**: redução do tempo manual para montar evidências e inventário.

## 7) Restrições e princípios

* “Divulgação progressiva”: dados tratados (Python/DuckDB) antes de análise qualitativa (LLM).
* Governança por allowlists/skills.
* Anti-truncamento: JSON curto + anexos.
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
