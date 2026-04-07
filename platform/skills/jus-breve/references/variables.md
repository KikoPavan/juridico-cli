# Dicionário de Variáveis — Jus-Breve (FIRAC)

## Índice
1. [Variáveis de Input](#1-variáveis-de-input)
2. [Variáveis de Output JSON](#2-variáveis-de-output-json)
3. [Enumerações e Valores Permitidos](#3-enumerações-e-valores-permitidos)
4. [Template de Sumário Executivo Markdown](#4-template-de-sumário-executivo-markdown)
5. [Exemplos de Valores Válidos e Inválidos](#5-exemplos-de-valores-válidos-e-inválidos)

---

## 1. Variáveis de Input

| Variável | Tipo | Obrigatório | Descrição |
|----------|------|-------------|-----------|
| `documento` | `string` | Sim | Texto integral da peça jurídica |
| `tipo_peca` | `enum` | Não | Tipo do documento (inferido se omitido) |
| `objetivo_analise` | `enum` | Não | `"AUDITORIA"`, `"DUE_DILIGENCE"`, `"CASE_BRIEF"`, `"RELATORIO"` |
| `nivel_detalhe` | `enum` | Não | `"COMPLETO"` (padrão), `"RESUMIDO"` |

---

## 2. Variáveis de Output JSON

### Raiz do Objeto

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `skill` | `string` | Não | Sempre `"jus-breve"` |
| `versao` | `string` | Não | Versão da skill |
| `status_analise` | `enum` | Não | `"COMPLETO"`, `"PARCIAL"`, `"BLOQUEADO"` |
| `motivo_bloqueio` | `string` | Sim | Preenchido quando `status_analise == "BLOQUEADO"` |
| `metadados` | `object` | Não | Informações do documento |
| `firac` | `object` | Não | Container dos 5 componentes FIRAC |
| `avaliacao_risco` | `object` | Não | Sumário de riscos (útil para due diligence) |
| `qualidade` | `object` | Não | Indicadores de confiança |

### Objeto `metadados`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `tipo_peca` | `enum` | Não | Tipo identificado |
| `ramo_direito` | `enum` | Não | Ramo predominante |
| `objetivo_analise` | `enum` | Não | Finalidade da análise |
| `partes` | `object` | Sim | `{"polo_ativo": string, "polo_passivo": string}` |
| `tribunal_juizo` | `string` | Sim | Órgão julgador |
| `data_peca` | `string` | Sim | ISO 8601 `YYYY-MM-DD` |
| `periodo_fatos` | `object` | Sim | `{"inicio": "YYYY-MM-DD", "fim": "YYYY-MM-DD"}` |
| `numero_processo` | `string` | Sim | CNJ ou identificador |

### Objeto `firac`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `facts` | `array<FactItem>` | Não | Inventário fático (mín. 1) |
| `issue` | `array<IssueItem>` | Não | Questões jurídicas (mín. 1 se não bloqueado) |
| `rule` | `array<RuleItem>` | Não | Normas aplicáveis |
| `application` | `array<ApplicationItem>` | Não | Mapeamento contextualizado |
| `conclusion` | `array<ConclusionItem>` | Não | Conclusões com nível de risco |

### Objeto `FactItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | `"F-01"`, `"F-02"` ... |
| `descricao` | `string` | Não | Descrição objetiva do fato |
| `tipo` | `enum` | Não | Tipo do fato (ver enumeração) |
| `fonte` | `enum` | Não | `"CITACAO_DIRETA"`, `"INFERENCIA_NECESSARIA"`, `"INFERENCIA_ESPECULATIVA"` |
| `status_probatorio` | `enum` | Não | `"COMPROVADO"`, `"CONTROVERTIDO"`, `"ESPECULATIVO"` |
| `pagina_ref` | `string` | Sim | Referência à página/seção do documento |

### Objeto `IssueItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | `"I-01"`, `"I-02"` ... |
| `questao` | `string` | Não | Pergunta objetiva |
| `prejudicial` | `boolean` | Não | `true` se deve ser resolvida antes das demais |
| `facts_ref` | `array<string>` | Não | IDs dos Facts que fundamentam esta Issue |

### Objeto `RuleItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | `"R-01"` ... |
| `diploma` | `string` | Não | Nome do diploma legal |
| `artigo` | `string` | Não | Referência artigo/inciso/parágrafo |
| `enunciado` | `string` | Não | Transcrição resumida (máx. 200 chars) |
| `hierarquia` | `enum` | Não | Hierarquia normativa |
| `tipo_norma` | `enum` | Não | `"RATIO_DECIDENDI"`, `"OBITER_DICTUM"`, `"NORMA_DIRETA"`, `"ANALOGIA"` |
| `issue_ref` | `array<string>` | Não | Issues às quais se aplica |

### Objeto `ApplicationItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | `"A-01"` ... |
| `fact_ref` | `string` | Não | ID do Fact mapeado |
| `rule_ref` | `string` | Não | ID da Rule aplicada |
| `elemento_norma` | `string` | Não | Elemento da norma verificado |
| `status` | `enum` | Não | `"PRESENTE"`, `"AUSENTE"`, `"PARCIAL"`, `"CONTROVERSO"`, `"DEPENDENTE_PROVA"` |
| `contexto` | `string` | Não | Análise contextual (diferencial FIRAC vs IRAC) |
| `contrafactual` | `string` | Sim | O que mudaria se o fato fosse diferente |
| `precedente_ref` | `string` | Sim | Referência a caso análogo mencionado no documento |

### Objeto `ConclusionItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | `"C-01"` ... |
| `issue_ref` | `string` | Não | Issue respondida |
| `resposta` | `enum` | Não | `"SIM"`, `"NAO"`, `"CONDICIONAL"`, `"INCONCLUSIVO"` |
| `fundamento` | `string` | Não | Justificativa (norma + fato comprovado) |
| `tese_juridica` | `string` | Sim | Para jurisprudência: tese extraída do julgado |
| `dispositivo` | `string` | Sim | Para acórdãos: parte dispositiva relevante |
| `nivel_risco` | `enum` | Não | `"CRITICO"`, `"RELEVANTE"`, `"MODERADO"`, `"BAIXO"`, `"NULO"` |
| `condicao` | `string` | Sim | Preenchido quando `resposta == "CONDICIONAL"` |

### Objeto `avaliacao_risco`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `nivel_geral` | `enum` | Não | Nível de risco consolidado |
| `riscos` | `array<RiscoItem>` | Não | Lista de riscos identificados |

### Objeto `RiscoItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `descricao` | `string` | Não | Descrição do risco |
| `nivel` | `enum` | Não | `"CRITICO"`, `"RELEVANTE"`, `"MODERADO"`, `"BAIXO"` |
| `conclusion_ref` | `string` | Sim | ID da conclusão que originou este risco |

### Objeto `qualidade`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `confianca` | `enum` | Não | `"ALTA"`, `"MEDIA"`, `"BAIXA"` |
| `cobertura_fatica` | `enum` | Não | `"COMPLETA"`, `"PARCIAL"`, `"INSUFICIENTE"` |
| `limitacoes` | `array<string>` | Não | Lacunas identificadas |
| `recomendacao` | `string` | Sim | Próximos passos sugeridos |

---

## 3. Enumerações e Valores Permitidos

### `tipo_peca`
`PETICAO_INICIAL` | `CONTESTACAO` | `RECURSO` | `SENTENCA` | `ACORDAO` |
`CONTRATO` | `EMENTA` | `PARECER` | `RELATORIO_AUDITORIA` | `LAUDO_PERICIAL` |
`ATO_NOTARIAL` | `OUTROS`

### `ramo_direito`
`CIVIL` | `PROCESSO_CIVIL` | `PENAL` | `PROCESSO_PENAL` | `TRABALHISTA` |
`TRIBUTARIO` | `ADMINISTRATIVO` | `CONSTITUCIONAL` | `EMPRESARIAL` |
`CONSUMIDOR` | `IMOBILIARIO` | `SUCESSOES` | `FAMILIA` | `OUTROS`

### `objetivo_analise`
`AUDITORIA` | `DUE_DILIGENCE` | `CASE_BRIEF` | `RELATORIO` | `TRIAGEM`

### `tipo` (FactItem)
`CONTRATUAL` | `TEMPORAL` | `PATRIMONIAL` | `COMPORTAMENTAL` |
`PROCESSUAL` | `REGISTRAL` | `FINANCEIRO` | `OUTROS`

### `fonte` (FactItem)
- `CITACAO_DIRETA` — fato textualmente explícito no documento
- `INFERENCIA_NECESSARIA` — decorre logicamente e inevitavelmente do texto
- `INFERENCIA_ESPECULATIVA` — pressupõe informação externa ao documento

### `status_probatorio` (FactItem)
- `COMPROVADO` — documentalmente verificado
- `CONTROVERTIDO` — mencionado mas disputado entre partes
- `ESPECULATIVO` — não confirmado no documento

### `nivel_risco`
`CRITICO` | `RELEVANTE` | `MODERADO` | `BAIXO` | `NULO`

---

## 4. Template de Sumário Executivo Markdown

```markdown
---

## 📋 Sumário Executivo — Jus-Breve

**Tipo de Peça:** {metadados.tipo_peca}
**Ramo do Direito:** {metadados.ramo_direito}
**Objetivo da Análise:** {metadados.objetivo_analise}
**Partes:** {partes.polo_ativo} × {partes.polo_passivo}
**Nº Processo:** {metadados.numero_processo}
**Data da Análise:** {data_atual}

---

### 📁 F — Inventário Fático

| ID | Fato | Tipo | Fonte | Status |
|----|------|------|-------|--------|
{Para cada FactItem: | {id} | {descricao} | {tipo} | {fonte} | {status_probatorio} |}

> ⚠️ Fatos especulativos NÃO fundamentam questões jurídicas nesta análise.

---

### ⚖️ I — Questão(ões) Jurídica(s)

{Para cada IssueItem:}
> **[{id}]** {questao}
> *Baseado em: {facts_ref}* {Se prejudicial: | `🔴 PREJUDICIAL`}

---

### 📖 R — Normas Aplicáveis

{Para cada RuleItem:}
- **{diploma}, {artigo}** *({hierarquia} | {tipo_norma})*
  > {enunciado}

---

### 🔗 A — Subsunção Contextualizada

{Para cada ApplicationItem:}
**[{id}] Fato {fact_ref} × Norma {rule_ref}**
- **Elemento verificado:** {elemento_norma}
- **Status:** {status}
- **Contexto:** {contexto}
{Se contrafactual: - **Contrafactual:** {contrafactual}}

---

### ✅ C — Conclusão

{Para cada ConclusionItem:}
**[{issue_ref}] {resposta}** — Risco: {nivel_risco}
> {fundamento}
{Se tese_juridica: > 📌 *Tese: {tese_juridica}*}
{Se dispositivo: > ⚖️ *Dispositivo: {dispositivo}*}
{Se condicao: > ⚠️ *Condição: {condicao}*}

---

### 🚦 Avaliação de Risco Consolidada

**Risco Geral: {avaliacao_risco.nivel_geral}**

| Risco | Nível |
|-------|-------|
{Para cada RiscoItem: | {descricao} | {nivel} |}

---

### 📊 Qualidade da Análise

**Confiança:** {qualidade.confianca}
**Cobertura Fática:** {qualidade.cobertura_fatica}

{Se limitacoes:}
**Limitações:**
{Para cada lim: - {lim}}

{Se recomendacao:}
> 💡 **Próximos Passos:** {recomendacao}
```

---

## 5. Exemplos de Valores Válidos e Inválidos

### Facts — Classificação de Fonte

✅ **Válido:**
> `descricao`: "O contrato de compra e venda foi assinado em 15/03/2022"
> `fonte`: "CITACAO_DIRETA"
> `status_probatorio`: "COMPROVADO"

✅ **Válido (inferência necessária):**
> `descricao`: "A parte que assinou o contrato tinha plena capacidade civil"
> `fonte`: "INFERENCIA_NECESSARIA" *(se o contrato menciona que a parte é maior e capaz)*

❌ **Inválido:**
> `descricao`: "Provavelmente houve fraude na assinatura"
> `fonte`: "CITACAO_DIRETA" *(fraude não consta no documento)*

### Issue — Vinculação aos Fatos

✅ **Válido:**
> `questao`: "O vendedor tem obrigação de transferir o imóvel livre de ônus?"
> `facts_ref`: ["F-01", "F-03"] *(F-01: contrato com cláusula de livre ônus; F-03: matrícula com hipoteca)*

❌ **Inválido:**
> `facts_ref`: [] *(Issue sem ancoragem fática)*

### Conclusion — Nível de Risco em Due Diligence

✅ **Válido:**
> `nivel_risco`: "CRITICO"
> `fundamento`: "O imóvel possui hipoteca registrada (F-03) que impossibilita transferência livre (art. 1.475, CC), contrariando cláusula 4.1 do contrato (F-01)."

❌ **Inválido:**
> `nivel_risco`: "ALTO" *(valor fora do enum)*
> `nivel_risco`: "NULO" com fundamento apontando risco *(inconsistência)*
