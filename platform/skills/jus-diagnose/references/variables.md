# Dicionário de Variáveis — Jus-Diagnose (IRAC)

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
| `documento` | `string` | Sim | Texto integral da peça jurídica a analisar |
| `tipo_peca` | `enum` | Não | Tipo do documento (ver enumeração abaixo) |
| `ramo_direito` | `enum` | Não | Ramo do direito preponderante (inferido se omitido) |
| `foco_issue` | `string` | Não | Indica qual aspecto priorizar se o doc tiver múltiplos problemas |

---

## 2. Variáveis de Output JSON

### Raiz do Objeto

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `skill` | `string` | Não | Sempre `"jus-diagnose"` |
| `versao` | `string` | Não | Versão da skill (ex: `"1.0.0"`) |
| `metadados` | `object` | Não | Informações do documento analisado |
| `irac` | `object` | Não | Container dos 4 componentes IRAC |
| `qualidade` | `object` | Não | Indicadores de confiança da análise |

### Objeto `metadados`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `tipo_peca` | `enum` | Não | Tipo identificado do documento |
| `ramo_direito` | `enum` | Não | Ramo do direito predominante |
| `partes` | `object` | Sim | `{"polo_ativo": string, "polo_passivo": string}` |
| `tribunal_juizo` | `string` | Sim | Identificação do órgão julgador, se presente |
| `data_peca` | `string` | Sim | Data da peça no formato `YYYY-MM-DD` (ISO 8601) |
| `issues_multiplas` | `boolean` | Não | `true` se o doc contém mais de uma questão jurídica |

### Objeto `irac`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `issue` | `array<IssueItem>` | Não | Lista de questões jurídicas identificadas (mín. 1) |
| `rule` | `array<RuleItem>` | Não | Lista de normas aplicáveis |
| `application` | `array<ApplicationItem>` | Não | Mapeamento fato→norma |
| `conclusion` | `array<ConclusionItem>` | Não | Conclusões por issue |

### Objeto `IssueItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | Identificador único ex: `"I-01"` |
| `questao` | `string` | Não | Pergunta objetiva formulada |
| `prejudicial` | `boolean` | Não | `true` se esta issue deve ser resolvida antes das demais |

### Objeto `RuleItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | Identificador único ex: `"R-01"` |
| `diploma` | `string` | Não | Nome do diploma legal (ex: `"Código Civil"`, `"Lei 8.078/1990"`) |
| `artigo` | `string` | Não | Referência completa do artigo/inciso/parágrafo |
| `enunciado` | `string` | Não | Transcrição resumida da norma (máx. 200 chars) |
| `hierarquia` | `enum` | Não | `"CF"`, `"LEI_FEDERAL"`, `"LEI_ESTADUAL"`, `"REGULAMENTO"`, `"SUMULA"`, `"TESE_REPERCUSSAO"` |
| `issue_ref` | `array<string>` | Não | IDs das issues às quais esta norma se aplica |

### Objeto `ApplicationItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | Identificador único ex: `"A-01"` |
| `fato` | `string` | Não | Fato extraído do documento |
| `elemento_norma` | `string` | Não | Elemento da norma ao qual o fato é mapeado |
| `rule_ref` | `string` | Não | ID da RuleItem referenciada |
| `status` | `enum` | Não | `"PRESENTE"`, `"AUSENTE"`, `"PARCIAL"`, `"CONTROVERSO"` |

### Objeto `ConclusionItem`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `id` | `string` | Não | Identificador único ex: `"C-01"` |
| `issue_ref` | `string` | Não | ID da Issue respondida |
| `resposta` | `enum` | Não | `"SIM"`, `"NAO"`, `"CONDICIONAL"`, `"INCONCLUSIVO"` |
| `fundamento` | `string` | Não | Justificativa em 1-3 frases |
| `condicao` | `string` | Sim | Preenchido apenas quando `resposta == "CONDICIONAL"` |

### Objeto `qualidade`

| Campo | Tipo | Nulável | Descrição |
|-------|------|---------|-----------|
| `confianca` | `enum` | Não | `"ALTA"`, `"MEDIA"`, `"BAIXA"` |
| `limitacoes` | `array<string>` | Não | Lista de lacunas ou ambiguidades encontradas |
| `recomendacao` | `string` | Sim | Sugestão de skill complementar quando aplicável |

---

## 3. Enumerações e Valores Permitidos

### `tipo_peca`
`PETICAO_INICIAL` | `CONTESTACAO` | `RECURSO` | `SENTENCA` | `ACORDAO` | `CONTRATO` |
`EMENTA` | `PARECER` | `ENUNCIADO_EXAME` | `OUTROS`

### `ramo_direito`
`CIVIL` | `PROCESSO_CIVIL` | `PENAL` | `PROCESSO_PENAL` | `TRABALHISTA` |
`TRIBUTARIO` | `ADMINISTRATIVO` | `CONSTITUCIONAL` | `EMPRESARIAL` |
`CONSUMIDOR` | `IMOBILIARIO` | `SUCESSOES` | `FAMILIA` | `OUTROS`

### `hierarquia` (normas)
`CF` | `LEI_FEDERAL` | `LEI_COMPLEMENTAR` | `LEI_ESTADUAL` |
`LEI_MUNICIPAL` | `REGULAMENTO` | `SUMULA_VINCULANTE` | `SUMULA` |
`TESE_REPERCUSSAO` | `ENUNCIADO_FONAJE`

---

## 4. Template de Sumário Executivo Markdown

Use este template exatamente após o bloco JSON:

```markdown
---

## 📋 Sumário Executivo — Jus-Diagnose

**Tipo de Peça:** {metadados.tipo_peca}
**Ramo do Direito:** {metadados.ramo_direito}
**Data da Análise:** {data_atual}

---

### ⚖️ Questão(ões) Jurídica(s)

{Para cada IssueItem:}
> **[{id}]** {questao}
{Se prejudicial: `🔴 Prejudicial`}

---

### 📖 Normas Aplicáveis

{Para cada RuleItem:}
- **{diploma}, {artigo}** *(hierarquia: {hierarquia})*
  {enunciado}

---

### 🔗 Subsunção

{Para cada ApplicationItem:}
| Fato | Elemento da Norma | Norma Ref. | Status |
|------|-------------------|------------|--------|
| {fato} | {elemento_norma} | {rule_ref} | {status} |

---

### ✅ Conclusão

{Para cada ConclusionItem:}
**[{issue_ref}] Resposta: {resposta}**
{fundamento}
{Se condicional: ⚠️ *Condição: {condicao}*}

---

### 📊 Qualidade da Análise

**Confiança:** {qualidade.confianca}

{Se limitacoes não vazio:}
**Limitações identificadas:**
{Para cada limitacao: - {limitacao}}

{Se recomendacao:}
> 💡 **Recomendação:** {recomendacao}
```

---

## 5. Exemplos de Valores Válidos e Inválidos

### Issue — Formulação

✅ **Válido:**
> "O locatário tem obrigação de pagar multa rescisória quando devolve o imóvel antes do término do prazo contratual?"

❌ **Inválido:**
> "Claramente o locatário deve pagar a multa" *(contém conclusão antecipada + opinião)*
> "Analisando os fatos, parece que..." *(vago, sem formulação de questão)*

### Application — Mapeamento

✅ **Válido:**
> `fato`: "O contrato estabelece multa de 3 aluguéis por rescisão antecipada"
> `elemento_norma`: "penalidade convencional para descumprimento de obrigação (art. 408, CC)"
> `status`: "PRESENTE"

❌ **Inválido:**
> `fato`: "Provavelmente houve inadimplência" *(inferência não textual)*
> `status`: "PRESENTE" sem fato correspondente

### Conclusion — Resposta

✅ **Válido:**
> `resposta`: "SIM"
> `fundamento`: "O art. 4º, Lei 8.245/91 autoriza a multa proporcional ao tempo restante, e o contrato previu expressamente 3 aluguéis, elemento presente nos fatos."

❌ **Inválido:**
> `fundamento`: "Como se vê claramente..." *(linguagem partidária)*
> `resposta`: "TALVEZ" *(valor fora do enum)*
