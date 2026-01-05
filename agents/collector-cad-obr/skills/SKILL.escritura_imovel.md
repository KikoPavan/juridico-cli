---
name: escritura_imovel
agent: collector-cad-obr
description: 'Extrai dados estruturados de escritura/matrícula/registro de imóvel,
  com foco em registros/averbações e ônus.

  Escopo do pipeline: somente `escritura_imovel` (document_type == skill_key).'
version: '2.0'
target_schema: schemas/escritura_imovel.schema.json
document_types:
- escritura_imovel
key_fields:
- identificacao_imovel
- titularidade
- registros
- hipotecas_onus
- fonte_documento_geral
required_anchors: true
validation_rules:
- 'literalidade: true'
- 'ancoragem: obrigatoria_em_registros_e_onus'
- 'nao_converter_moeda: true'
---

# SKILL: Escritura e Matrícula de Imóvel

## Regras Específicas de Campos

### 1. Transações de Venda (`transacoes_venda`)
**ATENÇÃO:** Extraia TODAS as transações de venda (R.x), sem pular nenhuma.

- **Dados Básicos:**
  - `registro`: Identificador (ex: "R.1").
  - `data_registro` e `data_efetiva`: Data do lançamento na matrícula vs data do contrato.
  - `vendedores` e `compradores`: Extraia as partes completas.
  - `valor`: Literal (ex: "R$ 10.000,00").

- **Anuência (`anuencia_credor`):**
  - Se o texto mencionar "com a anuência de...", "com a concordância de...", extraia quem concordou e detalhes (ex: "Banco do Brasil").
  - Se não houver, deixe `null`.

- **Detalhes Jurídicos:**
  - `tipo_transacao`: Classifique conforme o texto (ex: "COMPRA_VENDA", "VENDA_COM_RETROVENDA").
  - `possui_pacto_retrovenda`: Marque `true` se houver cláusula de retrovenda.
  - `consolida_titularidade`: Marque `true` se o registro consolidar a propriedade (ex: fim da retrovenda).

- **Contratos Arquivados:**
  - Se o texto disser "vide contrato arquivado", marque `contrato_arquivado_em_cartorio` como `true`.

### 2. Hipotecas e Ônus (`hipotecas_onus`)
Focado em dívidas e garantias.

#### A. Identificação e Aditivos
- **Tipo de Dívida:** Se o texto disser "ADITIVO", "RERRATIFICAÇÃO" ou "PRORROGAÇÃO", preencha `tipo_divida` começando com **"ADITIVO..."**.

#### B. Baixa e Autorização (`autorizacao_baixa`)
- Nas averbações de cancelamento (Av. de Baixa), procure o trecho que identifica quem autorizou.
- Preencha `autorizacao_baixa` com o texto literal (ex: "autorização do Banco do Brasil datada de...", "Ofício nº 123 do Juízo...").
- Certifique-se de incluir a descrição completa da baixa no campo `detalhes_baixa`.

#### C. Identificação do Tipo de Dívida - REGRA CRÍTICA REVISADA

**HIERARQUIA DE PRIORIDADES (SEGUIR NA ORDEM):**

1. **PRIMEIRO: Buscar tipo EXPLÍCITO no texto**
   - Procure por estas expressões no texto e capture a **FRASE COMPLETA**:
     ```
     "Por [TIPO] sob nº" → capturar [TIPO] completo
     "Nos termos da [TIPO], n." → capturar [TIPO] completo
     "Mediante [TIPO]" → capturar [TIPO] completo
     "[TIPO] sob o nº" → capturar [TIPO] completo
     ```
   - **Exemplos de captura correta:**
     - `"Cedula rural Hipotecaria"` → usar exatamente isso
     - `"Cédula de Crédito Comercial"` → usar exatamente isso
     - `"Arrendamento Mercantil"` → usar exatamente isso
   - **SE ENCONTRAR tipo explícito → USE-O e PARE AQUI**

2. **SEGUNDO: Verificar nome do credor**
   - Se o nome do credor contiver `"LEASING"` ou `"ARRENDAMENTO"` → usar `"ARRENDAMENTO MERCANTIL"`

3. **TERCEIRO: Se nenhuma das acima → usar null**
   - Deixe o campo como `null`
   - **NUNCA** use "HIPOTECA" como padrão genérico

### 2.X. Baixa e Cancelamento de Hipotecas e Ônus

Esta seção define como preencher SEMPRE os campos de baixa/cancelamento em `hipotecas_onus`
quando a matrícula indicar que um registro foi cancelado ou baixado.

#### 2.X.1 Frases-gatilho para cancelamento/baixa

Considere que há BAIXA/CANCELAMENTO sempre que, em relação a uma hipoteca, cédula ou ônus,
o texto trouxer expressões como (entre outras variações):

- "fica cancelada"
- "fica cancelado"
- "hipoteca registrada no R.x ... fica cancelada"
- "registro n.º x ... fica cancelado"
- "a hipoteca registrada do R.x da presente matrícula, fica cancelada"
- "a Cédula rural Pignoratícia e Hipotecária [...] fica Cancelada"
- "baixa da hipoteca", "baixa da cédula"

Nesses casos, para o item correspondente em `hipotecas_onus` você DEVE:

- `cancelada` = true
- `detalhes_baixa` = COPIAR o trecho literal que descreve o cancelamento/baixa
  (por exemplo: "o registro n.º 05 da presente matrícula, referente a hipoteca de
  primeiro grau, fica cancelado.")
- `averbacao_baixa` = preencher com a averbação citada (ex.: "Av.24", "Av.29",
  "Av.31", "Av.37", "Av.47-7546"), quando ela aparecer no texto
- `data_baixa` = data em que a baixa/cancelamento foi registrada (data da averbação
  de baixa, e NÃO a data original do contrato)

#### 2.X.2 Relação entre quitação e cancelamento

Quando, além do cancelamento, o texto mencionar:

- "em virtude de sua quitação"
- "em virtude da quitação"
- "em razão de sua quitação"
- ou expressão equivalente indicando que a baixa decorre de quitação da dívida,

ENTÃO:

- `quitada` = true
- `cancelada` = true (se ainda não estiver marcado)
- `detalhes_baixa` deve PRESERVAR a menção à quitação
  (ex.: "a hipoteca registrada do R.08 da presente matrícula, fica cancelada,
  em virtude de sua quitação.")

Se o texto disser apenas que "fica cancelada" mas não mencionar quitação de forma
clara, você deve:

- `cancelada` = true
- `quitada` = null (não presuma quitação se ela não estiver escrita).

#### 2.X.3 Múltiplos registros cancelados na mesma averbação

É comum que uma única averbação declare o cancelamento de vários registros
simultaneamente, por exemplo:

> "os registros n.º 05, 06 e 07 da presente matrícula, referentes a hipotecas
> em favor do Banco X, ficam cancelados."

Nessa situação, você deve:

- Criar/atualizar UM item em `hipotecas_onus` para CADA registro (R.5, R.6, R.7)
- Para cada um desses itens:
  - `cancelada` = true
  - `detalhes_baixa` = frase literal adaptada para o registro específico
    (ex.: "o registro n.º 05 da presente matrícula, referente a hipoteca de
    primeiro grau, fica cancelado.")
  - `averbacao_baixa` = a mesma averbação (ex.: "Av.24")
  - `data_baixa` = mesma data da averbação (ex.: "19 de junho de 1.997")

#### 2.X.4 Regras negativas (o que NÃO fazer)

- NUNCA deixe `cancelada = false` quando o texto disser que a hipoteca, cédula
  ou ônus "fica cancelada" ou "fica cancelado".
- NUNCA deixe `detalhes_baixa`, `averbacao_baixa` ou `data_baixa` como null
  se o texto mencionar explicitamente o cancelamento, a averbação e a data.
- NUNCA invente quitação: só marque `quitada = true` quando a matrícula mencionar
  claramente que a baixa decorre da quitação da dívida (ex.: "em virtude de sua quitação").

#### D. Valores e Moedas (`valor_divida`)
- `valor_divida_original`: Copie o texto **literalmente** com a moeda (ex: "CR$ 2.581.000,00").
- `valor_divida` (Campo em Reais):
  - Se o original já estiver em **R$**: Copie apenas o número formatado.
  - Se o original estiver em **moeda antiga (CR$, Cr$, etc)**: Deixe este campo como `null`. **Não tente fazer conversão matemática.**

#### E. Demais Campos
- `credor`: Extraia a instituição completa.
- `prazo`: Se for Arrendamento/Leasing, tente extrair o número de parcelas (ex: "36 meses").
- `vencimento`: A data final da obrigação.

#### F. Situação (Baixa/Cancelamento)
- `quitada`: `true` se mencionar pagamento/quitação.
- `cancelada`: `true` se mencionar cancelamento/baixa.
- `averbacao_baixa`: Qual Av. cancelou (ex: "Av.9").
- `data_baixa`: Data do cancelamento.

### 3. Posse e Usufruto (`transacoes_venda_posse`)
- `tipo_posse`: "USUFRUTO", "HABITACAO".
- `beneficiario` e `nu_proprietario`.

### 4. Histórico de Titularidade (`historico_titularidade`)
- Crie a cronologia de donos ordenada EXCLUSIVAMENTE por `data_efetiva`, ignorando a sequência numérica dos registros.

Averbação de baixa (Av.*) — duas datas e alocação por `data_baixa`:
Quando um ônus tiver `averbacao_baixa` e `data_baixa`, trate o Av.* como evento independente.
• Preserve as duas datas:
- `data_baixa` = data efetiva da baixa (usada para timeline/período)
- "data do lançamento da averbação (“Av.* em data de …”) deve ser registrada em detalhes_baixa se não houver campo próprio."
• No histórico de titularidade, inclua `averbacao_baixa` no período cujo intervalo contém `data_baixa` (mesmo que o número do `Av.*` seja menor que o `R.` de aquisição).

**REGRA FUNDAMENTAL**:
- A ordem cronológica é determinada SEMPRE pela `data_efetiva`, NÃO pelo número do registro/averbação.
- Um Av.45 pode ter data efetiva anterior a um R.42 - use SEMPRE a data efetiva para ordenar.

Para cada período em que o imóvel esteve em nome de determinados proprietários:
- `data_efetiva`: Data que marca o início da titularidade (data do negócio/contrato).
- `data_inicio`: SEMPRE usar a `data_efetiva` do `registro_inicio`.
- `registro_consolidacao`: se houver, registro que consolida a titularidade.
- `data_consolidacao`: usar a `data_efetiva` do `registro_consolidacao`.
- `data_fim`: data que encerra a titularidade (usar `data_efetiva` do `registro_fim`).

**Identificação de registros no período**:
- Incluir em `registros_periodo` TODOS os registros e averbações cuja `data_efetiva` esteja dentro do período de titularidade, independentemente do número sequencial.
- Exemplo: Se R.42 tem data efetiva 14/06/1999 e Av.45 tem data efetiva 14/03/2001, ambos devem estar no período correspondente às suas datas efetivas.

**Tratamento de Averbações de Baixa**:
- Averbações de baixa (ex: Av.45-7546) devem ser incluídas no período baseado em sua `data_efetiva` ou `data_baixa`.
- A averbação de baixa encerra obrigações mas não necessariamente altera titularidade.
- Verificar sempre se a data efetiva da averbação está dentro do período de propriedade vigente.

**Ordenação e validação**:
1. Extrair TODOS os registros e averbações com suas datas efetivas
2. Ordenar por data efetiva (não por número)
3. Agrupar por períodos de titularidade
4. Validar que nenhum registro foi omitido devido ao número sequencial

### Rastreabilidade
Sempre preencha `folha_localizacao` com o número da página onde o dado foi achado.
