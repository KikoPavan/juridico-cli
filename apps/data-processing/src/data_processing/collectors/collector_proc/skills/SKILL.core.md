```
name: collector_core
agent: collector-proc
descricao: |
  Núcleo do agente collector-proc, responsável por extrair dados estruturados
  de documentos jurídicos já convertidos para Markdown, respeitando schemas
  JSON específicos por tipo de documento e mantendo rastreabilidade por página.
version: "0.2.0"
input_format: markdown com marcadores de paginação
output_format: JSON estruturado
strict_mode: true
target_schema: io.schema.json
document_types:
  - processo
  - cabecalho_processo
  - peticao_processo
  - contestacao_processo
  - decisao_processo
  - procuracao
  - mandato_processo
key_fields:
  - document_type
  - anchors
validation_rules:
  - literalidade
  - ancoragem_obrigatoria
  - json_estrito_schema
  - nao_inferir
---

# SKILL CORE — Regras universais (obrigatórias)

## 1) Literalidade (regra-mestra)
- Extraia **somente** o que está **explicitamente** escrito no documento.
- Não deduza dados (ex.: papel de parte, datas, valores, resultados) se o texto não afirmar.

## 2) JSON estrito
- Responda **apenas** com um JSON válido (objeto), sem texto adicional.
- Obedeça **estritamente** ao schema injetado (tipos, required, enums, estruturas).
- Não crie campos fora do schema.

## 3) Âncoras (rastreabilidade) — obrigatório em itens relevantes
Para cada informação relevante (partes, pedidos, poderes, preliminares, mérito, dispositivo etc.):
- Preencha `anchors` com pelo menos 1 item contendo:
  - `kind`: `folha` | `pagina` | `secao` | `outro`
  - `page_marker`: marcador literal do documento (ex.: `[[Folha 12]]`, `[Pág. 3]`)
  - `quote`: trecho literal curto que prova o fato

Regras de qualidade da âncora:
- `page_marker` deve ser **idêntico** ao texto.
- `quote` deve ser **literal** e curto (não reescrever).
- Não invente `line_start/line_end` se não houver no documento.
- Se houver múltiplos trechos que sustentam o mesmo item, use múltiplas âncoras.

## 4) Ausência de dados
- Se não estiver no texto, **não preencha**.
- Quando o campo for opcional: prefira **omitir**.
- Para campos que são listas: use `[]` somente quando fizer sentido manter o campo presente (ex.: listas centrais do tipo); caso contrário omita.

## 5) Consistência com `document_type` e `mode`
- Nunca misture tipos diferentes dentro do mesmo JSON.
- Se o schema for `consolidated`:
  - respeite `sources`, `merge_meta`, `conflicts` conforme o schema exigir
  - não “apague divergências”: registre em `conflicts` quando houver valores incompatíveis
- Se o schema for `individual`:
  - não incluir campos de consolidação (ex.: `sources`, `merge_meta`, `conflicts`) **se o schema não prever**

## 6) Tratamento de nomes/termos
- Preserve nomes, cargos, qualificações e expressões do documento (sem “normalizar” criativamente).
- Só use enums/categorização quando o próprio documento indicar explicitamente.

## 7) Qualidade mínima por bloco
- Se o documento tiver seções claras (“DOS FATOS”, “DO DIREITO”, “DISPOSITIVO”), capture trechos literais curtos em itens separados com âncoras próprias.
- Para pedidos/itens enumerados (a), b), I, II): mantenha 1 item por pedido sempre que possível.

## 8) Nunca “explicar” a saída
- Não inclua justificativas, comentários ou texto fora do JSON.
