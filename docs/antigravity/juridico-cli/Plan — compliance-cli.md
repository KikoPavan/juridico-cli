```yaml
# Mapa do Projeto

* **Objetivo do sistema:** pipeline **local** (`juridico-cli`) que transforma documentos jurídicos (Markdown + PDFs originais) em **dados estruturados rastreáveis** (âncoras/source_id), **evidências/lacunas**, **FIRAC**, **jurisprudência selecionada**, **petição-esqueleto** e **checklist de conformidade**, preservando “divulgação progressiva” (determinístico antes de LLM).
* **Stakeholders/usuários:** (i) operador (você) executa pipeline e revisa outputs, (ii) advogado revisa FIRAC/petição, (iii) apoio/perícia usa anexos (inventário, mapas, timelines).
* **Modos principais:** **FIRAC-Core (process-first)** deve rodar a partir do `collector-proc` **mesmo sem CAD_OBR/Evidence**; **FIRAC-Plus** enriquece quando houver outputs do CAD_OBR/Evidence; **petição-esqueleto** deriva do FIRAC com revisão humana final.
* **Escopo (inclui):** ingestão Markdown → collectors → pipelines determinísticos (normalize/monetary/reconciler) → **DuckDB (verdade única)** → **pack_global** → evidence/firac/petição/compliance; jurisprudência via **case-law-cli** usando **base local** (`base_juridica` + Qdrant).
* **Fora de escopo (agora):** busca web aberta; substituir revisão humana; “decidir veracidade” — premissas do usuário são “verdade operacional” e só viram “verdade probatória” com referência rastreável.
* **Fluxo end-to-end (macro):** collectors → pipelines determinísticos → `dataset_v1/*.jsonl` → DuckDB → `artifacts/evidence_packs/dataset_v1/pack_global.json` (canônico) → evidence-agent (`evidence_out.json` + anexos; export opcional `evidence_map`) → FIRAC → case-law (Qdrant) → petition → compliance.
* **Sub-sistemas e responsabilidades:** `/pipelines` (determinístico), `/agents` (LLM; padrão 4 arquivos), `/artifacts` (DuckDB/packs/outputs), `/base_juridica` (leis/jurisprudência + manifesto).
* **Dados e governança:**

  * “Verdade operacional”: `data/context.json` + `data/contexto_relacoes.json` (priorização P0/P1).
  * “Verdade probatória”: apenas com `source_id` + `anchor`/referência rastreável em dataset/DuckDB/pack.
* **Linhagem mínima:** OCR/Usuário → Markdown → collectors JSON → pipelines → `dataset_v1` (JSONL) → DuckDB → `pack_global.json` → Evidence → FIRAC-Core (process-first) e opcional FIRAC-Plus → petição.
* **Contratos/artefatos-chave:** `artifacts/db/*.duckdb`, `artifacts/evidence_packs/dataset_v1/pack_global.json` (source of truth), `outputs/.../evidence_out.json` (canônico), `outputs/relatorio_firac.{json,md}`, `outputs/peticao/petition_draft.md`, `outputs/compliance/compliance_check.md`.
* **Anti-truncamento (obrigatório):** “JSON curto + anexos”; budgets do evidence-agent (findings/evidências/trechos/listas) e reexecução com orçamento menor se parsing falhar.
* **Qdrant (papel):** busca semântica de trechos do processo e da biblioteca jurídica; no CAD_OBR, coleção sugerida `cad_obr_chunks_v1` com payload mínimo e consultas **sempre com filtros** (ex.: `property_id`).
* **QA (gates):** JSON sempre parseável; 100% findings com evidência; recomendações externas apenas P0/P1; regressão com 3 casos (mínimo, lacunas, denso/truncamento); DuckDB carrega tabelas e `pack_global` mínimo tem agregados + top-N + inventário limitado + P0/P1.
* **Operação (runbook):** ordem de execução; logs mínimos (versões de schemas/skills, hash do pack/dataset, raw do modelo, caminhos de anexos); fallbacks (DuckDB falhou → inventário+recomendações; parsing falhou → reduzir orçamento; pack grande → mover para anexos); severidade S1/S2/S3 e procedimento.
```

## Plano — compliance-cli (agente)

**1) Objetivo e valor**

- Executar **checagens objetivas** (OK/FALHA) sobre artefatos e saídas do pipeline (pack/evidence/FIRAC/petição), reduzindo regressões e prevenindo “afirmações sem evidência”.
- Gerar `outputs/compliance/compliance_check.md` como relatório operacional/auditável.

**2) Escopo**

- Inclui:
  - Gates de QA: parsing, rastreabilidade, budgets anti-truncamento, regras “não afirmar sem evidência”, recomendações externas apenas P0/P1.
  - Verificações de integridade do DuckDB/pack (status ok; views esperadas).

- Não inclui:
  - Revisão jurídica final (humana).

- Dependências diretas:
  - `pack_global.json` canônico em `artifacts/…`, `evidence_out.json` (quando existir), FIRAC, petição.

**3) Entradas, saídas e contratos**

- Entradas:
  - `artifacts/evidence_packs/dataset_v1/pack_global.json` (canônico).
  - `outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json` + anexos (quando executado).
  - `outputs/relatorio_firac.json` e `outputs/peticao/petition_draft.md` (quando executados).

- Saídas:
  - `outputs/compliance/compliance_check.md` com lista de checks, evidências de execução (hashes/paths) e status OK/FALHA.

- Contratos mínimos e validações:
  - Checks binários conforme matriz QA (collector/pipelines/DuckDB/pack/evidence/FIRAC/petition).
  - Validar regra: “finding só existe com evidência ancorada”; senão deve estar como lacuna/colheita.
  - Validar anti-truncamento: budgets máximos (findings/evidências/trechos/listas).

- Versionamento/compatibilidade:
  - Registrar versões de schemas/skills e hashes do pack/dataset.

- Linhagem/auditoria:
  - Referenciar paths verificados e hashes coletados no relatório.

**4) Arquitetura e fluxos**

---
compliance-cli # gemini API
  ├─ main.py
  ├─ config.yaml
  ├─ io.schema.json
  ├─ skills/
  └─ prompt.md
---

- Encaixe:
  - `compliance-cli` é etapa final (após petition) para emitir checklist OK/FALHA.

- Fluxo principal:
  1. Carregar `pack_global.json` (canônico) e validar `duckdb_info.status == ok` e views esperadas (quando CAD_OBR existir).
  2. Validar outputs LLM: JSON parseável (evidence/FIRAC quando aplicável).
  3. Validar rastreabilidade: findings com `source_id`/âncora/trecho; “não existe doc” proibido se doc estiver no pack sem trecho.
  4. Emitir `compliance_check.md` com OK/FALHA + ações recomendadas (fallback/reexecução).

- Alternativos/fallback:
  - Se evidence não existir: validar FIRAC-Core e petição derivada do FIRAC; registrar “modo degradado” (sem Evidence).

**5) Plano de trabalho (fases executáveis)**

- **Fase 1 — Checklist mínimo alinhado ao QA**
  - Tarefas: mapear checks do `04_QA...` para regras executáveis e formato do relatório.
  - Entregáveis: `agents/compliance-cli/prompt.md`, `io.schema.json` (se houver saída estruturada adicional), template do `compliance_check.md`.
  - DoD: 100% checks críticos implementados (parsing, rastreabilidade, budgets, P0/P1).

- **Fase 2 — Integração com artefatos (pack/evidence/FIRAC/petição)**
  - Tarefas: validar paths canônicos vs cópias não-autoritativas; coletar hashes e versões.
  - DoD: relatório inclui hash do pack e do dataset (lista JSONL + hash) e versões de schemas/skills.

- **Fase 3 — Fallbacks e incidentes**
  - Tarefas: codificar respostas S1/S2/S3 conforme runbook (ex.: parsing falhou → reduzir orçamento e reexecutar).
  - DoD: recomendações de recuperação aparecem no relatório e batem com runbook.

**6) Observabilidade e Operação**

- Logs/métricas:
  - % checks OK; contagem de falhas por categoria; detecção de truncamento/parsing; presença de hashes/versões.

- Alertas:
  - S1/S2/S3 conforme runbook; registrar etapa que falhou.

- Runbook:
  - Procedimento: identificar etapa, coletar logs+raw+hash, corrigir, revalidar no caso denso.

**7) QA e critérios de aceite**

- Testes essenciais:
  - Rodar em 3 casos (mínimo/lacunas/denso) e garantir relatório consistente.

- Aceite:
  - Detecta 0 falhas de parsing em execuções válidas; marca FALHA quando houver finding sem evidência; valida budgets.

- Regressão:
  - Revalidar sempre que mudar prompts/skills/schemas (exigir versão).

- Dados de teste:
  - Reuso dos 3 pacotes definidos.

**8) Segurança e conformidade**

- Controles mínimos:
  - Trilhas de auditoria (hashes, versões, raw do modelo quando falhar).
  - Respeitar “sem web aberta” e governança por allowlists/skills.

- Ameaças prováveis:
  - Falsa conformidade por checar cópia errada do pack → sempre usar caminho canônico em `artifacts/`.

**9) Lacunas e perguntas**

1. **Formato exato do relatório `compliance_check.md` (seções obrigatórias e nomenclatura de checks)**
   - Importa: padronização operacional.
   - Decisão: template final do relatório.

2. **Quais checks adicionais além do QA macro são obrigatórios (ex.: jurídicos/estilo/redação)**
   - Importa: escopo real do compliance-cli.
   - Decisão: backlog e critérios de aceite.
