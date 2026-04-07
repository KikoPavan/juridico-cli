---
name: contestacao_processo
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/contestacao_processo.schema.json"
document_types:
  - contestacao_processo
key_fields:
  - process_number
  - parties
  - representations
  - contestacao_identification
  - preliminares
  - merito
  - provas_e_requerimentos
  - pedidos_finais
validation_rules:
  - literalidade
  - ancoragem_por_bloco
  - nao_inferir_preliminares_ou_merito
  - preservar_estrutura_listas
  - nao_criar_teses
---

# SKILL — contestacao_processo

## Finalidade
Extrair a estrutura essencial da contestação, preservando:
- preliminares (quando existirem),
- mérito/impugnações,
- provas/requerimentos,
- pedidos finais da contestação,
com **âncoras por bloco/itens** e **sem inferência**.

## Regras específicas (além do CORE)

### 1) Identificação mínima
- Se houver número do processo no texto, preencher `process_number` com âncora.
- Se houver título/cabeçalho da peça (ex.: “CONTESTAÇÃO”, “RESPOSTA”, “IMPUGNAÇÃO”), preencher `contestacao_identification` (ou equivalente do schema) com âncora.
- Não deduzir “tipo de contestação”.

### 2) Partes e representantes (somente se constar)
- `parties`: incluir apenas se o texto trouxer partes identificadas.
- Para `role`, só classificar quando o texto indicar; caso contrário `role = outro` e `role_raw` literal.
- `representations`: registrar advogados/OAB apenas quando constarem, com âncora.

### 3) Preliminares (quando existirem)
- Se o texto tiver seção “PRELIMINAR(ES)” ou expressões equivalentes, criar itens em `preliminares`.
- Cada item deve:
  - conter trecho literal curto (sem “tese reescrita”),
  - ter âncora própria.
- Não criar preliminares “implícitas”.

### 4) Mérito / impugnações
- Se o texto tiver seção “MÉRITO”, “NO MÉRITO”, “IMPUGNAÇÃO”, criar itens em `merito`.
- Cada item deve:
  - conter trecho literal curto,
  - ter âncora própria.
- Não transformar alegações em conclusões jurídicas.

### 5) Provas e requerimentos
- Capturar menções explícitas a provas, documentos, perícias, depoimentos, intimações etc.
- Registrar como itens literais em `provas_e_requerimentos`, com âncora por item.

### 6) Pedidos finais
- Identificar e separar pedidos finais quando o texto os listar (ex.: “requer”, “pede”, “ao final”).
- `pedidos_finais`: um item por pedido sempre que possível, com âncora própria.
- Não inferir pedidos não escritos.

### 7) Coerência
- Não misturar conteúdo de decisão/sentença dentro da contestação.
- Se o documento mencionar decisões anteriores, capture apenas como trecho literal (sem rotular como decisão).

### 8) Consolidação (quando o schema for consolidated)
- Unir itens preservando âncoras.
- Se houver divergências entre fontes (ex.: pedidos finais diferentes), registrar em `conflicts`.
