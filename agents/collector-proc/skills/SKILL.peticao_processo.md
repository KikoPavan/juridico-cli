---
name: peticao_processo
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/peticao_processo.schema.json"
document_types:
  - peticao_processo
key_fields:
  - process_number
  - parties
  - representations
  - peticao_identification
  - valor_da_causa
  - fatos
  - fundamentos
  - provas_e_requerimentos
  - pedidos
validation_rules:
  - literalidade
  - ancoragem_por_pedido
  - nao_resumir_indevidamente
  - nao_inferir_fundamentos
  - preservar_estrutura_listas
---

# SKILL — peticao_processo

## Finalidade
Extrair a estrutura essencial de uma petição (inicial ou incidente, conforme o texto) **sem inferência**, preservando:
- fatos (como trechos literais curtos),
- fundamentos (como trechos literais curtos),
- pedidos (um item por pedido quando possível),
- provas/requerimentos,
com **âncoras por item**.

## Regras específicas (além do CORE)

### 1) Identificação mínima
- Se houver número do processo no texto, preencher `process_number` com âncora.
- Se houver título/cabeçalho da peça (ex.: “PETIÇÃO INICIAL”, “EMENDA À INICIAL”, “MANIFESTAÇÃO”), preencher `peticao_identification` (ou equivalente do schema) com âncora.
- Não inventar “tipo de petição” se não estiver explícito.

### 2) Partes e representantes (somente se constar)
- `parties`: incluir apenas se o texto trouxer partes identificadas (autor/requerente etc.).
- `role`: só classificar quando o texto indicar; caso contrário `role = outro` e `role_raw` literal.
- `representations`: registrar advogados/OAB apenas quando constarem, com âncora.

### 3) Valor da causa (quando constar)
- Capturar como texto literal em `valor_da_causa`, com âncora.
- Não converter moeda, não calcular, não normalizar.

### 4) Fatos e fundamentos — itens curtos, literais e separados
- Se o texto tiver seções (“DOS FATOS”, “DO DIREITO”, “DA FUNDAMENTAÇÃO”), criar itens separados em `fatos` e `fundamentos`.
- Cada item deve:
  - conter trecho literal curto (evitar parágrafos muito longos),
  - ter âncora própria.
- Não “resumir” criativamente; não adicionar conclusões.

### 5) Pedidos — regra crítica
- `pedidos` deve ser a parte mais estruturada:
  - Um item por pedido sempre que o texto permitir (enumerado, alíneas, “requer”, “pede”).
  - Cada pedido deve ter âncora própria (no trecho do pedido).
- Não transformar pedidos implícitos em explícitos.
- Se o texto trouxer lista de pedidos em bloco, faça o melhor esforço para separar em itens.

### 6) Provas e requerimentos
- Capturar menções explícitas a provas, documentos, diligências, intimações, perícias, etc.
- Manter como itens literais curtos em `provas_e_requerimentos`, com âncora por item.

### 7) Coerência
- Não misturar conteúdo de contestação/decisão dentro da petição.
- Se o documento for “petição” mas discutir decisões anteriores, capture isso somente se estiver em fatos/fundamentos e com trecho literal (sem rotular como decisão).

### 8) Consolidação (quando o schema for consolidated)
- Preservar itens e unir âncoras.
- Se houver divergências entre fontes (ex.: pedidos diferentes), registrar em `conflicts` (não “apagar” diferenças).
