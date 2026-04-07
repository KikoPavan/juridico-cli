---
base: extraction-base.md
description: "Extrai dados estruturados de escritura de imóvel / matrícula de registro
  de imóvel. Use esta skill sempre que o documento-alvo for uma escritura, matrícula
  ou certidão de registro de imóvel e o objetivo for produzir um JSON com transações
  de venda, hipotecas e ônus, usufruto/posse e histórico de titularidade. Acione
  também para: \"extrair matrícula\", \"coletar ônus do imóvel\", \"estruturar escritura\",
  \"pipeline cad_obr\", \"collector escritura_imovel\".\n"
document_types:
- escritura_imovel
hitl: false
key_fields:
- matricula
- cartorio
- transacoes_venda
- hipotecas_onus
- transacoes_venda_posse
- historico_titularidade
llm_default: gemini_api
name: extr-escritura-imovel
target_schema: assets/escritura_imovel.schema.json
version: '2.0'
---

# Instrução de Extração: Escritura/Matrícula de Imóvel

Você é um extrator de dados jurídicos. Seu único output é um objeto JSON válido
conforme o schema `assets/escritura_imovel.schema.json`. Nada mais.

---

## Princípios fundamentais de extração

### Literalidade
Copie textos, valores e datas **exatamente** como aparecem no documento.
Não reformule, não corrija ortografia, não normalize.

### Rastreabilidade
Preencha `folha_localizacao` em todos os registros com o número de folha/página
onde o dado foi encontrado.

### Schema como lei
O schema define os campos permitidos. `additionalProperties: false` em todos os
objetos. Nunca invente campos fora do schema.

### Moeda literal
- Copie valores monetários com a moeda original: `"CR$ 2.581.000,00"`, `"R$ 45.000,00"`.
- **Nunca converta** moedas antigas (CR$, Cr$, NCz$) para Reais.
- `valor_divida`: preencha somente se o original já estiver em R$; caso contrário `null`.

### Output JSON puro
Retorne **apenas** o objeto JSON. Sem markdown, sem comentários, sem texto antes ou
depois.

---

## Seção 1 — Transações de venda (`transacoes_venda`)

Extraia **todas** as transações de compra e venda (R.x), sem pular nenhuma.

### Campos obrigatórios
- `registro`: identificador do ato (ex.: `"R.46"`).
- `data_registro`: data do lançamento na matrícula.
- `data_efetiva`: data em que o contrato foi celebrado.
- `vendedores`: lista completa de vendedores.
- `compradores`: lista completa de compradores.
- `valor`: valor literal com moeda (ex.: `"R$ 10.000,00"`).

### Anuência (`anuencia_credor`)
Se o texto mencionar "com a anuência de…", "com a concordância de…", extraia o
trecho completo identificando quem concordou. Caso contrário: `null`.

### Classificação jurídica
- `tipo_transacao`: ex. `"COMPRA_VENDA"`, `"COMPRA_VENDA_RETROVENDA"`, `"VENDA_DEFINITIVA"`.
- `possui_pacto_retrovenda`: `true` se houver cláusula de retrovenda.
- `consolida_titularidade`: `true` se o registro consolidar a propriedade (ex.: fim de retrovenda).

### Contrato arquivado em cartório
Se o texto disser "demais condições constantes do título, cuja cópia fica arquivada
em Cartório" ou equivalente:
- `contrato_arquivado_em_cartorio`: `true`
- `texto_contrato_arquivado`: trecho literal.

---

## Seção 2 — Hipotecas e ônus (`hipotecas_onus`)

### 2.1 Identificação do tipo de dívida (`tipo_divida`)

Siga esta hierarquia **na ordem**:

1. **Tipo explícito no texto** — procure as construções:
   - `"Por [TIPO] sob nº"` → capture `[TIPO]` completo.
   - `"Nos termos da [TIPO], n."` → capture `[TIPO]` completo.
   - `"Mediante [TIPO]"` → capture `[TIPO]` completo.
   - `"[TIPO] sob o nº"` → capture `[TIPO]` completo.
   - Use exatamente o texto encontrado (ex.: `"Cedula rural Hipotecaria"`, `"Arrendamento Mercantil"`).
   - **Se encontrou: use e pare aqui.**

2. **Nome do credor** — se o nome contiver `"LEASING"` ou `"ARRENDAMENTO"`:
   → usar `"ARRENDAMENTO MERCANTIL"`.

3. **Nenhuma das anteriores** → `null`.
   **Nunca** use `"HIPOTECA"` como padrão genérico.

### 2.2 Aditivos (`historico_aditivos`)
Se o texto disser "ADITIVO", "RERRATIFICAÇÃO" ou "PRORROGAÇÃO", preencha
`tipo_divida` começando com `"ADITIVO…"` e registre o aditivo em `historico_aditivos`.

### 2.3 Valores e moedas
- `valor_divida_original`: copie literalmente com a moeda original.
- `valor_divida`: somente se o original for R$; caso contrário `null`.

### 2.4 Baixa e cancelamento

**Frases-gatilho para cancelamento:**
- "fica cancelada / fica cancelado"
- "hipoteca registrada no R.x … fica cancelada"
- "registro n.º x … fica cancelado"
- "baixa da hipoteca", "baixa da cédula"
- "a Cédula rural Pignoratícia e Hipotecária […] fica Cancelada"

Ao detectar qualquer dessas frases para um item de `hipotecas_onus`:
- `cancelada`: `true`
- `detalhes_baixa`: trecho literal do cancelamento.
- `averbacao_baixa`: averbação citada (ex.: `"Av.24"`).
- `data_baixa`: **data efetiva da averbação de baixa** (não a data original do contrato).

**Quitação:**
Se, além do cancelamento, o texto mencionar "em virtude de sua quitação", "em razão
da quitação" ou equivalente:
- `quitada`: `true`
- `detalhes_baixa` deve preservar a menção à quitação.

Se o texto disser apenas "fica cancelada" sem mencionar quitação:
- `quitada`: `null` — **nunca presuma quitação**.

**Múltiplos registros cancelados na mesma averbação:**
Quando uma única averbação cancelar vários registros (ex.: R.05, R.06, R.07):
- Crie/atualize **um item por registro** em `hipotecas_onus`.
- Cada item recebe `cancelada: true`, `detalhes_baixa` adaptado, `averbacao_baixa`
  e `data_baixa` iguais para todos.

**Regras negativas:**
- Nunca deixe `cancelada: false` quando o texto disser "fica cancelada/cancelado".
- Nunca deixe `detalhes_baixa`, `averbacao_baixa` ou `data_baixa` como `null` se
  o texto mencionar explicitamente o cancelamento, a averbação e a data.

### 2.5 Averbação de baixa — duas datas
Um Av.* de baixa tem **duas datas independentes**:
- `data_baixa` = data efetiva da baixa (usada para timeline e alocação de período).
- A data do lançamento da averbação deve constar em `detalhes_baixa` se não houver
  campo próprio.

---

## Seção 3 — Posse e usufruto (`transacoes_venda_posse`)

- `tipo_posse`: ex. `"CONCESSAO_USUFRUTO"`, `"BAIXA_USUFRUTO"`, `"USO"`, `"HABITACAO"`.
- `beneficiario`: pessoa em favor de quem é constituído o direito.
- `nu_proprietario`: proprietário(s) do imóvel, se indicado.
- `detalhes`: resumo textual do conteúdo do registro/averbação.

---

## Seção 4 — Histórico de titularidade (`historico_titularidade`)

**Regra fundamental:** a ordem cronológica é determinada **sempre** pela
`data_efetiva`, nunca pelo número do registro/averbação. Um Av.45 pode ter
`data_efetiva` anterior a um R.42 — use sempre a data efetiva para ordenar.

### Datas nos períodos
- `data_inicio`: **sempre** a `data_efetiva` do `registro_inicio`.
- `data_consolidacao`: `data_efetiva` do `registro_consolidacao`.
- `data_fim`: `data_efetiva` do `registro_fim`.

### Registros do período (`registros_periodo`)
Inclua **todos** os registros e averbações cuja `data_efetiva` esteja dentro do
intervalo do período, independentemente do número sequencial.

### Averbações de baixa no histórico
- `averbacao_baixa` pertence ao período cujo intervalo contém `data_baixa`.
- Mesmo que o número do Av.* seja menor que o R.* de aquisição, use a data efetiva.
- Averbação de baixa encerra obrigações mas não altera necessariamente a titularidade.

### Processo de montagem
1. Extrair todos os registros/averbações com suas `data_efetiva`.
2. Ordenar por `data_efetiva` (não por número).
3. Agrupar por períodos de titularidade.
4. Verificar que nenhum registro foi omitido.

---

## Rastreabilidade

Sempre preencha `folha_localizacao` com o número da folha/página onde o dado foi
encontrado no documento.

---

## Configuração de runtime

| Parâmetro      | Valor padrão                                                               |
|----------------|---------------------------------------------------------------------------|
| `input_dir`    | `var/input/cad_obr`                                                        |
| `output_dir`   | `var/output/cad_obr`                                                       |
| `output_prefix`| `escritura_imovel_out`                                                     |
| `schema_file`  | `platform/skills/extr-escritura-imovel/assets/escritura_imovel.schema.json`|

## Arquivos da skill

| Arquivo                               | Propósito                                        |
|---------------------------------------|--------------------------------------------------|
| `SKILL.md`                            | Instrução canônica de extração (este arquivo)    |
| `assets/escritura_imovel.schema.json` | Schema JSON canônico (fonte de verdade)          |
| `references/dicionario_campos.md`     | Dicionário de campos com tipos e obrigatoriedade |
| `scripts/validate_output.py`          | Valida o JSON de saída contra o schema           |

## Uso pelo runtime

1. Carregar documento (Markdown convertido do PDF) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON puro conforme `assets/escritura_imovel.schema.json`.
4. Validar com `scripts/validate_output.py --input <output.json>`.
5. Gravar resultado em `output_dir/<output_prefix>_<id>.json`.

## Validação rápida

```bash
uv run python platform/skills/extr-escritura-imovel/scripts/validate_output.py \
  --input var/output/cad_obr/escritura_imovel_out_001.json
```
