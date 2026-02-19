```yaml
# **Mapa do Projeto**

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

## Plano — case-law-cli (agente)

**1) Objetivo e valor**

- Selecionar jurisprudência **auditável** a partir de (i) questões nucleares do FIRAC + (ii) recorte fático + (iii) filtros, usando base local (`base_juridica`) e Qdrant.
- Produzir `jurisprudencia.md` (humano) e `jurisprudencia.json` (auditável e reprodutível).

**2) Escopo**

- Inclui:
  - Consulta híbrida (semântica + filtros) e ranking; explicitar por que cada precedente foi escolhido.
  - Registro de linhagem (queries, filtros, candidates, seleção final).

- Não inclui:
  - Busca web aberta.

- Dependências diretas:
  - FIRAC (`outputs/relatorio_firac.json`) como fonte das “questões nucleares” e do recorte fático.
  - Qdrant com base jurídica indexada + `base_juridica` com `manifesto.yml`.

**3) Entradas, saídas e contratos**

- Entradas (formatos, origem):
  - **Obrigatório:** conjunto de questões nucleares do FIRAC + recorte fático + filtros (tribunal, classe, tags, janela temporal).
  - **Opcional:** allowlist do tema (conforme estratégia híbrida “Global + Pack do caso”).

- Saídas (formatos, destino):
  - `outputs/jurisprudencia/jurisprudencia.md` _(caminho exato: lacuna nos docs)_
  - `outputs/jurisprudencia/jurisprudencia.json` com: itens selecionados, metadados do `manifesto.yml` (tipo/tribunal/classe-número/data/tags/sha256/source_id), queries/filtros aplicados e referências de chunks/trechos quando usados.

- Contratos mínimos e validações:
  - Saída **auditável**: toda seleção deve carregar `source_id` e metadados do manifesto; proibir item sem origem verificável.

- Versionamento/compatibilidade:
  - `jurisprudencia.json` deve registrar versão do agente + versão do índice/coleção consultada (ex.: `*_v1`). _(Lacuna: campos exatos do schema.)_

- Linhagem/auditoria:
  - Logar query, filtros, top_k, scores e lista de candidatos (ao menos top-N) para reproduzir a seleção.

**4) Arquitetura e fluxos**

---
case-law-cli/ # gemini API
  ├─ main.py
  ├─ config.yaml
  ├─ io.schema.json
  ├─ skills/
  └─ prompt.md
---

- Encaixe no end-to-end:
  - Executa **após FIRAC** e antes de `petition-cli`.

- Fluxo principal:
  1. Ler FIRAC e extrair “questões nucleares” + recorte fático.
  2. Consultar Qdrant (biblioteca jurídica) com filtros e ranking; produzir lista curta de precedentes.
  3. Gerar `jurisprudencia.json` (auditável) + `jurisprudencia.md` (síntese).

- Alternativos/fallback:
  - Sem resultados: gerar saída com “sem precedentes suficientes” + lista de lacunas de filtro/tema (sem inventar).

- Integrações:
  - Qdrant; `base_juridica/manifests`; pipeline de ingestão determinística.

**5) Plano de trabalho (fases executáveis)**

- **Fase 1 — Contrato de entrada/saída**
  - Tarefas: definir schema mínimo do `jurisprudencia.json` (campos auditáveis + rastreio de consulta).
  - Entregáveis: `agents/case-law-cli/io.schema.json` + `prompt.md` alinhado ao contrato operacional.
  - DoD: validação do JSON (parseável) e presença de `source_id`/manifesto por item.
  - Risco: truncamento → limitar top-N e mover candidatos completos para anexo.

- **Fase 2 — Integração com Qdrant + filtros**
  - Tarefas: implementar consulta semântica com filtros; registrar top_k e ranking.
  - Entregáveis: comandos/CLI + logs de query.
  - DoD: “caso mínimo” retorna precedentes; “caso denso” não quebra parsing.

- **Fase 3 — Auditoria e rastreabilidade**
  - Tarefas: anexar referências (manifesto + eventuais trechos/chunks) e trilha de consulta no output.
  - DoD: reprodução da seleção a partir dos logs.

**6) Observabilidade e Operação**

- Logs obrigatórios:
  - versões (schema/skills), hash do pack consultado (se usar allowlist do caso), query+filtros, top_k e ids selecionados.

- Alertas/detecção:
  - “Sem resultados” ou “muitos resultados sem filtros” → marcar como degradação e exigir ajuste de filtros.

- Fallback:
  - Emitir saída com lacunas e recomendações de ajuste (sem busca web).

- Runbook:
  - Como validar índice (Qdrant ok), como reproduzir consulta a partir do log. _(Comandos: lacuna.)_

**7) QA e critérios de aceite**

- Testes essenciais:
  - Unit: validação do JSON contra schema.
  - Integration: FIRAC → case-law → outputs (`md/json`) auditáveis.

- Aceite:
  - `jurisprudencia.json` sempre parseável; cada item com `source_id` + metadados do manifesto; sem afirmações sem referência.

- Regressão:
  - Revalidar 3 casos (mínimo/lacunas/denso) sempre que mudar embeddings/coleção/prompt.

- Dados de teste:
  - Usar `base_juridica` com manifestos e subset indexado para testes determinísticos.

**8) Segurança e conformidade**

- Controles mínimos:
  - Somente base local + conectores controlados; trilha de consulta e hashes quando aplicável.

- Ameaças prováveis:
  - “Precedente inadequado ao caso” por falta de filtros → exigir filtros no contrato de entrada e registrar no output.

**9) Lacunas e perguntas**

1. **Schema exato e paths de saída de `jurisprudencia.{md,json}`**
   - Importa: padronização de downstream (petition/compliance).
   - Decisão: contrato e integração.

2. **Filtros obrigatórios mínimos (tribunal/classe/data/tags)**
   - Importa: reduz falsos positivos.
   - Decisão: validação de entrada do agente.

3. **Política de “allowlist do tema” (Pack do caso + global)**
   - Importa: escopo e custos.
   - Decisão: como combinar “Global + Pack do caso”.
