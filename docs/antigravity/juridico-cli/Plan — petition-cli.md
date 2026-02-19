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

## Plano — petition-cli (agente)

**1) Objetivo e valor**

- Gerar **petição-esqueleto** derivada do FIRAC (Core ou Plus), mantendo rastreabilidade e revisão humana final.
- Produzir `outputs/peticao/petition_draft.md` com remissões a FIRAC/jurisprudência/evidências quando disponíveis.

**2) Escopo**

- Inclui:
  - Pipeline de geração: entrada (FIRAC + jurisprudência + evidências opcionais) → estrutura → argumentos → referências → versão final (esqueleto).
  - Gates: não afirmar sem referência; separar premissa vs prova.

- Não inclui:
  - Substituir revisão humana final e protocolo.

- Dependências diretas:
  - `outputs/relatorio_firac.json` (+ opcional `outputs/relatorio_firac.md`).
  - `jurisprudencia.json/md` do case-law-cli (quando executado).
  - Evidence do CAD_OBR (`evidence_out.json`) apenas para enriquecer (FIRAC-Plus), sem bloquear FIRAC-Core.

**3) Entradas, saídas e contratos**

- Entradas:
  - FIRAC-Core (obrigatório): saída do `collector-proc` transformada em FIRAC (`outputs/relatorio_firac.json`).
  - Jurisprudência: `jurisprudencia.json/md`.
  - Evidence (opcional): `evidence_out.json` + anexos (CAD_OBR).

- Saídas:
  - `outputs/peticao/petition_draft.md` (petição-esqueleto).

- Contratos mínimos e validações:
  - Petição **não pode afirmar** fatos sem remissão ao FIRAC/jurisprudência; quando faltar prova, registrar como lacuna e/ou “documento recomendado” (P0/P1).
  - Se Evidence existir, respeitar “finding só existe com evidência ancorada” e política anti-truncamento (usar anexos).

- Versionamento/compatibilidade:
  - Registrar versão do agente e referências (hash do FIRAC/pack/jurisprudência usados) no cabeçalho/rodapé do draft. _(Campos exatos: lacuna.)_

- Linhagem/auditoria:
  - Logar inputs consumidos (paths + hashes) e mapa de remissões (seções → itens do FIRAC/jurisprudência).

**4) Arquitetura e fluxos**

---
petition-cli # gemini API
  ├─ main.py
  ├─ config.yaml
  ├─ io.schema.json
  ├─ skills/
  └─ prompt.md
---

- Encaixe:
  - FIRAC → (case-law) → petition → compliance.

- Fluxo principal:
  1. Carregar FIRAC (JSON canônico) e extrair: fatos, provas, regras e conclusões.
  2. Incorporar (se existir) jurisprudência selecionada com metadados auditáveis.
  3. Montar esqueleto com seções e argumentos, inserindo remissões explícitas (IDs/âncoras quando aplicável) e marcando lacunas probatórias.
  4. Emitir `petition_draft.md`.

- Alternativos/fallback:
  - Sem jurisprudência: gerar petição-esqueleto apenas com FIRAC + lista “jurisprudência pendente” (sem inventar).
  - Evidências insuficientes: manter narrativa como premissa e criar seção “pendências/documentos recomendados (P0/P1)”.

- Integrações:
  - Templates (`/templates`) e contratos globais (packs/outputs).

**5) Plano de trabalho (fases executáveis)**

- **Fase 1 — Contrato do draft e estrutura mínima**
  - Tarefas: definir outline obrigatório do `petition_draft.md` e regras de remissão (FIRAC/jurisprudência/evidência).
  - Entregáveis: `agents/petition-cli/prompt.md`, `io.schema.json` (se produzir metadados estruturados), template base.
  - DoD: draft gerado em caso “mínimo” e “lacunas” sem afirmações não suportadas.
  - Risco: drift narrativo → gates (“não afirmar sem referência”).

- **Fase 2 — Integração com jurisprudência e Evidence (opcional)**
  - Tarefas: consumir `jurisprudencia.json` e (se existir) `evidence_out.json` para enriquecer sem bloquear FIRAC-Core.
  - DoD: ausência de Evidence/jurisprudência não impede geração; apenas cria seções pendentes.

- **Fase 3 — Auditoria e anti-truncamento**
  - Tarefas: registrar hashes/versões e manter anexos fora do conteúdo principal quando necessário.
  - DoD: compatível com compliance-cli e QA (sem regressões).

**6) Observabilidade e Operação**

- Logs obrigatórios:
  - inputs (paths + hashes), versão do agente, contagem de remissões, lacunas P0/P1 geradas.

- Alertas:
  - Detectar “sem referências suficientes” acima de limiar (ex.: muitas seções sem remissão) e marcar como degradação. _(Limiar: lacuna.)_

- Fallback/recuperação:
  - Se FIRAC não disponível → bloquear (S1) e orientar reexecução do pipeline até FIRAC-Core.

- Runbook:
  - Usar severidades S1/S2/S3 e revalidar no caso denso após mudanças.

**7) QA e critérios de aceite**

- Testes essenciais:
  - E2E: FIRAC-Core → (case-law opcional) → petition → compliance, nos 3 casos (mínimo/lacunas/denso).

- Aceite:
  - Petição não afirma sem referência FIRAC/jurisprudência; lacunas explícitas; outputs estáveis.

- Regressão:
  - Revalidar após mudanças em prompts/skills/schemas/templates.

- Dados de teste:
  - 3 pacotes definidos em QA.

**8) Segurança e conformidade**

- Controles mínimos:
  - Não usar web aberta; manter trilhas (hashes/versões) e rastreabilidade de remissões.

- Ameaças prováveis:
  - “Alucinação jurídica/fática” → aplicar gates e converter incerteza em lacuna/colheita P0/P1 (sem afirmar).

**9) Lacunas e perguntas**

1. **Estrutura obrigatória do `petition_draft.md` (seções fixas e placeholders)**
   - Importa: consistência e revisão humana.
   - Decisão: template final em `/templates`.

2. **Formato de remissões (como citar FIRAC/evidência/jurisprudência no texto)**
   - Importa: rastreabilidade auditável.
   - Decisão: padrão de citação e parsing pelo compliance-cli.

3. **Quando Evidence (CAD_OBR) entra no draft: direto na petição ou apenas via FIRAC-Plus?**
   - Importa: acoplamento e risco de bloqueio.
   - Decisão: integração FIRAC-Plus → petition.
