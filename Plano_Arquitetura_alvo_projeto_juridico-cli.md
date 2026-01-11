# Arquitetura — Reconciler-CLI (Irregularidades → FIRAC) v2

## 1) Objetivo
Criar um agente jurídico que:
(a) monte “pacotes de evidência” (fatos determinísticos + trechos literais com âncoras) e
(b) **indique** documentos necessários (com `impacto_prova`) e
(c) produza o **FIRAC_BRIDGE**/**FIRAC Bundle** para consumo pelo `firac-cli`.

## 2) Entradas e Fontes de Verdade (camadas)

### 2.1 Determinístico (fatos estruturados)
Origem: outputs/cad-obr/04_reconciler/dataset_v1/*.jsonl
- documentos.jsonl
- imoveis.jsonl
- partes.jsonl
- onus_obrigacoes.jsonl
- property_events.jsonl
- contratos_operacoes.jsonl
- novacoes_detectadas.jsonl
- links.jsonl
- pendencias.jsonl

Função: responder “o que aconteceu” com IDs, datas, valores, status, vínculos.

### 2.2 Texto integral (prova literal)
Origem: Markdown/PDF convertidos (ex.: arq-md/*.md + PDFs originais)
Função: prover trechos literais, com âncoras (R./AV./[[Folha]]) e contexto mínimo.

## 3) Armazenamentos

### 3.1 Relacional (opcional no v1, recomendado no v2)
- SQLite (MVP) ou Postgres (produção local)
- Tabelas espelhando 1:1 os jsonl, com colunas-chave + payload_json (jsonb/json)

Chaves mínimas:
- doc_id, property_id, onus_id, parte_id, credor_id, event_date/data_registro/data_efetiva

### 3.2 Vetorial (Qdrant)
Coleção: cad_obr_chunks_v1
Pontos (embeddings) = chunks do texto integral e/ou “mini-fatos” (opcional).

Payload obrigatório por chunk:
- doc_id
- source_doc_id (ou source_id/sha)
- property_id (matricula:XXXX)
- anchor (R.10 / AV.17 / [[Folha 123]])
- registro_ref (quando existir)
- chunk_type: (FOLHA | REGISTRO | PARAGRAFO | FATOS_JSON)
- date_registro (se aplicável)
- date_efetiva (se aplicável)
- onus_id (se aplicável)
- event_type (ONUS_REGISTRO/ONUS_BAIXA/VENDA/ANUENCIA_BANCO)

Consulta RAG **SEMPRE** com filtros:
- property_id obrigatório quando a pergunta for por matrícula
- doc_id quando o agente já souber o documento
- anchor/onus_id quando for “prova de um registro específico”

## 4) Componentes (alto nível)
[Documentos integrais] ---> (Chunker+Anchors) ---> [Qdrant]
        |                                         ^
        v                                         |
[dataset_v1 jsonl] ---> (Loader/SQL opcional) ---> [DB Relacional]

                         +------------------------------+
                         | LangGraph Orchestrator       |
                         |  reconciler-cli              |
                         +------------------------------+
                           |      |            |
                           |      |            +--> MCP Tool: semantic_search (Qdrant)
                           |      +--> MCP Tool: sql/query_dataset (jsonl/DB)
                           +--> MCP Tool: build_evidence_pack

## 5) MCP Server (mcp-server-cad-obr) — Tools

### 5.1 Tools determinísticas (dataset/DB)
- list_datasets()
- get_document(doc_id)
- get_property(property_id)
- list_onus(property_id, filters...)
- timeline(property_id, date_from?, date_to?)
- get_onus(onus_id)
- list_novacoes(property_id?)
- link_graph(property_id)

### 5.2 Tools RAG (Qdrant)
- semantic_search(query, top_k, filters{property_id/doc_id/anchor/onus_id/...})
- get_chunk(doc_id, anchor, window?)
- evidence_snippets_for_onus(onus_id)

### 5.3 Tools de “produto jurídico” (saídas)
- build_evidence_pack(case_id, property_id, hypothesis, onus_ids?, event_ids?, constraints?)
  -> retorna JSON + markdown com:
  (a) fatos determinísticos (tabelas)
  (b) trechos literais (com âncoras)
  (c) lacunas (o que falta provar)
  (d) lista de documentos internos que “fechariam a prova”
- (novo) build_firac_bridge(evidence_pack_ref, opts)
  -> gera FIRAC Bundle (md/json) a partir do Evidence Pack

## 6) Skills sob demanda (progressive disclosure)

### 6.1 Catálogo leve no prompt do agente
- SKILL: Consulta Determinística (SQL/Dataset)
- SKILL: Busca Semântica com Filtros (Qdrant)
- SKILL: Montar Pacote de Evidência (Evidence Pack)
- SKILL: Auditoria de Datas (efetiva vs registro) e Anomalias
- SKILL: Classificação de Ônus (garantia real vs restrição judicial vs irrelevante ao caso)

### 6.2 Carregamento sob demanda
O agente só chama tool “load_skill(skill_name)” quando:
- detectar ambiguidade
- precisar de regra específica (ex.: arrendamento mercantil não entra como novação)

Implementação:
- “skills_registry.json” descreve: nome, quando usar, entradas/saídas, exemplos
- MCP expõe “get_skill_spec(skill_name)” que retorna o detalhamento completo

## 7) LangGraph — fluxo do agente (estados e gates)

Estado mínimo (state):
- case_id
- hypothesis (ex.: “má-fé: reempacotamento de dívida + troca de garantias sem ciência dos sócios”)
- properties_in_scope: [matricula:7013, matricula:7546, ...]
- time_window (ex.: 1998-05-01 a 1999-07-31)
- actors (sócios, gerente, credor_id)
- evidence: {facts:[], snippets:[], gaps:[]}

Grafo (resumo):
1) ClarifyGoal -> normaliza hipótese e escopo (narrativa-primeira)  
2) DeterministicScan -> timeline/list_onus/list_novacoes (dataset/DB)  
3) PatternBuilder -> cruza por credor_id+valor+datas+matrículas (indícios coordenados)  
4) RAGProof -> busca trechos literais por anchor/doc_id (Qdrant)  
5) EvidencePack -> compila (fatos + trechos + lacunas)  
6) FIRACBridge -> monta FIRAC_BRIDGE e/ou FIRAC Bundle  
7) Output -> exporta md/json (versões)

Gates anti-alucinação:
- Se “fato” não estiver no dataset/DB -> não afirmar; registrar como lacuna ou narrativa.  
- Se “fato” não tiver snippet literal -> **não** “solicitar ao banco”; apenas **indicar** o documento na seção correta.

## 8) Saídas padronizadas (artefatos)
- evidence_pack_<case_id>_<property_id>.md  
- evidence_pack_<case_id>_<property_id>.json  
- firac_bundle_<case_id>_<property_id>.md/json  
- anexos: tabela de eventos + tabela de ônus relevantes + tabela de anomalias de datas

Estrutura do Evidence Pack (mínimo):
1) Hipótese e escopo  
2) Fatos determinísticos (tabelas)  
3) Evidências literais (chunks com âncoras)  
4) Padrões detectados (ex.: renovação coordenada por credor_id)  
5) Lacunas e o que falta para fechar a prova  
6) Documentos internos recomendados (lista objetiva)

## 9) Plano de implementação (sequência curta)
P1) Loader: importar dataset_v1 (jsonl) para DB (ou manter jsonl + consultas diretas)  
P2) Indexer: chunker + embeddings + upsert no Qdrant com payload completo  
P3) MCP Server: expor tools determinísticas + tools Qdrant + builders (evidence + firac_bridge)  
P4) Agent: LangGraph com gates; prompt com catálogo de skills leve (narrativa-primeira)  
P5) Teste de caso: matrícula 7013 + janela 1998-1999 + credor_id alvo  
P6) Regressão: garantir que arrendamento mercantil não entra como novação e que restrição judicial não entra como “ônus relevante”

## 10) Próximo passo imediato
1) Definir storage v1: (A) SQLite ou (B) sem DB (query direto nos jsonl)  
2) Criar coleção Qdrant “cad_obr_chunks_v1” com payload obrigatório  
3) Subir MCP server com 6 tools mínimas:
   - timeline, list_onus, list_novacoes, semantic_search, build_evidence_pack, build_firac_bridge
