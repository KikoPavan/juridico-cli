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

- **O que este documento é:** PRD do juridico-cli com objetivos, escopo, entregáveis e critérios de sucesso.
- **Para que serve:** Definir o “porquê” e o “o quê” do sistema para orientar implementação e priorização.
- **Entradas (inputs):** necessidade do caso; restrições operacionais; premissas de rastreabilidade.
- **Saídas (outputs):** lista de entregáveis; KPIs/definição de pronto; roadmap de fases.
- **Critérios de aceite / Validação:** Ver `04_QA_Avaliacao_Criterios_de_Aceite_e_Regressao.md` (conformidade das saídas e regressão mínima).

## 1) Objetivo

- **Construir um pipeline local (juridico-cli)** que transforma documentos jurídicos em entregáveis com rastreabilidade (âncoras/source_id) e priorização P0/P1, com dois modos:

* **FIRAC-Core (principal / process-first):** gerar relatório/matriz FIRAC do processo a partir do collector-proc, mesmo sem CAD_OBR/evidence.
* **FIRAC-Plus (opcional):** enriquecer o FIRAC quando existirem outputs do CAD_OBR/Evidence (ex.: evidence_out.json e anexos; evidence_map.json apenas como export).
* **Petição-esqueleto:** derivada do FIRAC (Core ou Plus), com revisão humana final.

## 2) Problema que resolve

- Hoje a colheita de documentos e a montagem de evidências tende a ser ampla, lenta e com risco de “levantar documentação irrelevante”.
- O projeto precisa **triagem objetiva**: o que é relevante (P0/P1) e o que tem prova ancorada vs o que apenas é premissa e exige colheita.

## 3) Usuários e uso

- **Usuário operador (você)**: roda pipeline, alimenta contexto, revisa outputs.
- **Jurídico/advogado**: usa FIRAC + petição-esqueleto para revisão e protocolo.
- **Apoio/perícia**: usa anexos (inventário completo, mapas de evidências, linhas do tempo).

## 4) Escopo

**Inclui:**

- Ingestão (Markdown) → extrações (collector-\*) → normalização/cálculo/reconciliação (pipelines) → **DuckDB “verdade única”** → **Pack** → evidence/firac/petição.
- Nota de fluxo: o sistema suporta FIRAC-Core (process-first via collector-proc) independentemente da execução de CAD_OBR/Evidence. Outputs do Evidence podem existir ou não; quando existirem, são usados apenas no modo FIRAC-Plus.
- Jurisprudência: seleção via **case-law-cli** usando base local (base_juridica + Qdrant).

**Não inclui (fora de escopo agora):**

- Automação de busca web aberta (somente base local / conectores controlados).
- Substituir revisão humana final.
- Decidir “veracidade”: o sistema trata premissas do usuário como **verdade operacional** e exige prova documental para findings.

## 5) Artefatos de saída (contratos)

- `artifacts/db/*.duckdb` (verdade única; CAD_OBR quando existir)
- `artifacts/evidence_packs/dataset_v1/pack_global.json` (pack consolidado canônico, derivado do DuckDB/dataset_v1)
- `outputs/cad_obr/04_reconciler/dataset_v1/*.jsonl` (dataset estruturado do CAD_OBR)
- Quando Evidence existir:
  - `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json` + anexos (`*.jsonl`, `*.md`)
  - (opcional) export/view: `evidence_map.json` e `evidence_map_full.jsonl`
- `outputs/relatorio_firac.json` e `outputs/relatorio_firac.md` (FIRAC — process-first, independente de Evidence)
- `outputs/peticao/petition_draft.md` e `outputs/compliance/compliance_check.md` (quando executados)

## 6) KPIs (mínimo)

- **Confiabilidade**: 100% das saídas LLM parseáveis (JSON válido quando exigido).
- **Cobertura P0/P1**: % de premissas P0/P1 com “documento recomendado” definido e justificativa.
- **Rastreabilidade**: % de findings com evidência ancorada (source_id/âncora/referência).
- **Eficiência**: redução do tempo manual para montar evidências e inventário.

## 7) Restrições e princípios

- “Divulgação progressiva”: dados tratados (Python/DuckDB) antes de análise qualitativa (LLM).
- Governança por allowlists/skills.
- Anti-truncamento: JSON curto + anexos.

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
