---
name: processo
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/processo.schema.json"
document_types:
  - processo
key_fields:
  - process_number
  - court
  - comarca
  - vara
  - classe
  - assunto
  - parties
  - representations
  - documentos_referenciados
  - anchors
validation_rules:
  - literalidade
  - ancoragem_em_identificacao_e_partes
  - nao_misturar_document_types
  - nao_inferir_papeis
---

# SKILL — processo (dossiê do processo)

## Finalidade
Gerar a “visão dossiê” do processo quando o `document_type` for `processo`.  
Este tipo é agregador/índice: captura identificação, partes, representantes e referências úteis **somente se estiverem explicitamente no texto recebido**.

## Regras específicas (além do CORE)

### 1) Identificação do processo (prioridade máxima)
- Se houver número do processo, capture como `process_number` com âncora.
- Se houver tribunal/foro/comarca/vara/classe/assunto, capture cada item com âncora própria.
- **Não inventar** número, classe, assunto, vara, comarca. Se não estiver escrito, omita.

### 2) Partes (polo ativo/passivo) — sem inferência
- Liste partes somente se constarem no texto.
- Para o papel (`role`), só classifique como “autor/réu/etc.” quando houver indicação explícita.
- Se o texto trouxer um rótulo diferente, use:
  - `role = outro`
  - `role_raw` com o rótulo literal
- Se houver qualificação (CPF/CNPJ, RG, endereço, estado civil etc.), manter como texto literal e ancorar.

### 3) Representação (advogados/OAB) — somente quando constar
- Vincule advogado a parte somente se o texto permitir (ex.: “Advogado do Autor: …”).
- OAB deve ser literal. Se não houver, não preencher.

### 4) Referências a documentos / peças
- Se o texto listar peças (petição inicial, contestação, decisão, procuração etc.), registre como “documentos referenciados” (ou equivalente do schema).
- Para cada referência:
  - incluir tipo/título literal
  - incluir data se explícita
  - incluir âncora

### 5) Âncoras
- Identificação, partes e referências de documentos devem ter âncoras.
- Evite âncoras “genéricas” para múltiplos fatos: prefira 1 âncora por fato.

### 6) Coerência
- Não misturar conteúdos de outros `document_type` dentro deste JSON.
- Se o texto recebido for claramente uma peça específica (ex.: petição), mas o front matter diz `processo`, **não corrija o metadata**: apenas extraia o que o texto realmente contém e omita o que não existir.
