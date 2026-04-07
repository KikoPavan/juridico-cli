---
name: decisao_processo
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/decisao_processo.schema.json"
document_types:
  - decisao_processo
key_fields:
  - process_number
  - decision_type
  - decision_date
  - decisor
  - relatorio
  - fundamentacao
  - dispositivo
  - outcome
  - determinacoes
validation_rules:
  - literalidade
  - ancoragem_forte_no_dispositivo
  - nao_inferir_resultado
  - nao_resumir_indevidamente
  - preservar_termos_da_decisao
---

# SKILL — decisao_processo

## Finalidade
Extrair a estrutura essencial de decisões/sentenças/acórdãos/despachos, preservando:
- relatório (se houver),
- fundamentação,
- dispositivo (prioridade máxima),
- resultado/outcome (somente se explícito),
- determinações (prazos, intimações, atos),
com **âncoras por item**, especialmente no dispositivo.

## Regras específicas (além do CORE)

### 1) Identificação mínima
- Se houver número do processo no texto, preencher `process_number` com âncora.
- Determinar `decision_type` apenas se o texto indicar (ex.: “SENTENÇA”, “DECISÃO”, “DESPACHO”, “ACÓRDÃO”).
  - Se não indicar, usar `outro` e preencher `value_raw` quando o schema permitir.

### 2) Data e decisor (quando constar)
- `decision_date`: somente quando houver data explícita.
- `decisor`: preencher apenas com o que estiver explícito (nome, órgão julgador, tribunal, cargo), com âncora.

### 3) Relatório / fundamentação / dispositivo
- Seções claras (“RELATÓRIO”, “FUNDAMENTAÇÃO”, “DISPOSITIVO”) devem virar itens separados.
- `dispositivo`:
  - é obrigatório “ancoragem forte”: cada item do dispositivo deve ter âncora própria.
  - separar itens quando o texto estiver enumerado (I, II, alíneas, “defiro/indefiro” etc.).
- Não reescrever o dispositivo; manter trechos literais curtos.

### 4) Outcome (resultado) — somente se explícito
- Só preencher `outcome` quando o texto afirmar explicitamente (ex.: “defiro”, “indefiro”, “julgo procedente”).
- Se o texto for ambíguo, não inferir: omitir `outcome` ou usar `outro` com `value_raw` quando o schema permitir.

### 5) Determinações
- Capturar determinações explícitas: intimações, prazos, expedição de ofícios, perícias, remessas etc.
- Cada determinação como item literal com âncora.

### 6) Coerência
- Não misturar conteúdo de petição/contestação dentro da decisão.
- Se a decisão reproduzir trechos de peças, capture apenas como parte do relatório/fundamentação quando estiver no texto (sem “atribuir” fora do que está escrito).

### 7) Consolidação (quando o schema for consolidated)
- Preservar itens e unir âncoras.
- Divergências entre decisões (ex.: resultados incompatíveis) devem ir para `conflicts`, não “sumir”.
