
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

## Plano — Qdrant (banco de dados)

**1) Objetivo e valor**

- Prover **busca semântica** (RAG) para: (i) trechos do processo e (ii) biblioteca jurídica (leis/jurisprudência), com filtros e rastreabilidade por `source_id`/âncoras.
- Habilitar recuperação de prova literal quando necessário, sem romper o princípio de “divulgação progressiva”.

**2) Escopo**

- Inclui:
  - Coleção sugerida para CAD_OBR: `cad_obr_chunks_v1` com payload mínimo por chunk.
  - Indexação para “biblioteca jurídica” conforme pipeline de ingestão determinística (ingestão → normalização → embeddings → indexação).

- Não inclui:
  - Busca web aberta.

- Dependências diretas:
  - `base_juridica/` com `manifesto.yml` por PDF (inclui `sha256`, `source_id` e metadados).
  - Conteúdo textual com âncoras (Markdown convertido) e custódia dos PDFs originais.

**3) Entradas, saídas e contratos**

- Entradas (origem):
  - Textos/chunks derivados de Markdown (processo e/ou CAD_OBR) e de `base_juridica` (leis/jurisprudência).

- Saídas (destino):
  - Resultados de `semantic_search` (top_k) consumidos por agentes (ex.: case-law-cli) e/ou tools RAG (se MCP ativo).

- Contratos mínimos e validações (governança):
  - **Payload mínimo CAD_OBR (por chunk):** `doc_id`, `source_doc_id` (ou `source_id/sha`), `property_id`, `anchor`, `chunk_type`, e quando aplicável `registro_ref`, `onus_id`, `event_type`.
  - **Regra de consulta:** buscas semânticas **sempre com filtros**; por matrícula/pergunta de imóvel, `property_id` é obrigatório.

- Regras de versionamento/compatibilidade:
  - Versionar coleções por sufixo (`*_v1`) e evoluir via nova coleção (migração) quando payload/embedding mudar. _(Lacuna: política formal de migração não está explícita nos docs.)_

- Requisitos de linhagem e auditoria:
  - Logar por consulta: query, filtros, top_k, ids retornados, `source_id`/`anchor` de cada chunk selecionado para uso em evidência/jurisprudência.

**4) Arquitetura e fluxos**

- Encaixe no end-to-end:
  - Qdrant é suporte a RAG para evidence/firac/case-law/petition, sem substituir DuckDB/pack como “verdade tratada”.

- Fluxo principal (passo a passo):
  1. Ingestão determinística de documentos (processo/base jurídica) → normalização → chunking → embeddings.
  2. Upsert no Qdrant com payload mínimo e chaves de rastreabilidade (`source_id`, `anchor`).
  3. Consulta semântica com filtros (ex.: `property_id`, tribunal/tags quando aplicável).

- Fluxos alternativos/fallback:
  - Se Qdrant indisponível: operar sem RAG (apenas DuckDB/pack + inventário/lacunas), preservando gates (“não afirmar sem prova”).

- Pontos de integração:
  - Pipeline `pipelines/jurisprudencia_ingest/` (indexação) e tools RAG via MCP (opcional).

**5) Plano de trabalho (fases executáveis)**

- **Fase 1 — Contrato e desenho de coleções**
  - Tarefas:
    - Fixar payload mínimo de `cad_obr_chunks_v1` conforme docs.
    - Definir estratégia de coleções para biblioteca jurídica (uma vs múltiplas; naming; filtros por tribunal/tags). _(Lacuna a decidir.)_

  - Entregáveis: spec de coleções/payload + regras de filtro; documentação curta no repositório.
  - DoD: payload mínimo documentado; queries exigem filtros (ex.: `property_id`).
  - Riscos/mitigação: inconsistência de payload → bloquear upsert sem campos mínimos.

- **Fase 2 — Ingestão determinística e indexação**
  - Tarefas:
    - Implementar/ajustar pipeline de ingestão: ingestão → normalização → embeddings → indexação.
    - Garantir `manifesto.yml` por PDF na `base_juridica` com `sha256` e `source_id`.

  - Entregáveis: pipeline executável + logs de indexação + manifesto padrão.
  - DoD: reindexação reproduzível (mesmos inputs → mesmos ids/payloads).
  - Riscos/mitigação: divergência de IDs → derivar `source_id` de hash/metadados (conforme princípio de rastreabilidade).

- **Fase 3 — Operação e manutenção**
  - Tarefas:
    - Definir política de atualização/reindexação (quando re-embedar, quando criar `*_v2`). _(Lacuna.)_
    - Definir backup/restore/retenção (local). _(Lacuna.)_

  - Entregáveis: runbook do Qdrant (comandos, verificação de saúde, restore).
  - DoD: procedimento testado no “caso denso” e sem impacto no fluxo degradado (sem Qdrant).

**6) Observabilidade e Operação**

- Métricas/logs obrigatórios:
  - Contagem de vetores por coleção; taxa de upsert; latência de consulta; % consultas sem filtros (deve ser 0).
  - Logs por execução: versões, hash de fontes (manifestos), queries e filtros aplicados.

- Alertas:
  - Qdrant indisponível → degradar para “sem RAG” e registrar no log.

- Fallback/recuperação:
  - Desativar chamadas RAG e seguir com DuckDB/pack.

- Rotina operacional:
  - Checklist de saúde (ping, coleções existentes, contagens) + validação de consulta com filtro. _(Comandos específicos: lacuna nos docs.)_

**7) QA e critérios de aceite**

- Testes essenciais:
  - Indexação de um pacote “mínimo” e “denso” e busca com filtros retornando resultados.
  - Garantir que resultados carregam `source_id`/`anchor` e são rastreáveis.

- Critérios de aceite:
  - Consultas do CAD_OBR exigem `property_id`; resultados auditáveis (payload completo).

- Regressão:
  - A cada mudança de embeddings/payload: revalidar top_k, filtros e rastreabilidade em 3 casos (mínimo/lacunas/denso).

- Estratégia de dados de teste:
  - Reutilizar os 3 pacotes/datasets definidos em QA (mínimo, lacunas, denso).

**8) Segurança e conformidade**

- Controles mínimos:
  - Base local + conectores controlados (sem web aberta); governança via allowlists/skills.
  - Logs com hashes (pack/dataset/manifestos) e trilha de consulta.

- Ameaças prováveis:
  - Recuperação sem filtros → evidência incorreta; mitigar bloqueando queries sem filtros obrigatórios.

**9) Lacunas e perguntas**

1. **Coleções da biblioteca jurídica:** uma coleção única ou separadas (leis vs jurisprudência; STJ/STF)?
   - Importa: define naming, filtros e manutenção.
   - Decisão: desenho final de coleções e payload.

2. **Modelo/dimensão de embeddings:** qual modelo padrão e compatibilidade entre coleções?
   - Importa: afeta reindexação e ranking.
   - Decisão: política de versionamento (`*_v1`→`*_v2`).

3. **Backup/restore/retenção/custos:** qual política local obrigatória?
   - Importa: recuperação operacional.
   - Decisão: runbook e rotinas.
