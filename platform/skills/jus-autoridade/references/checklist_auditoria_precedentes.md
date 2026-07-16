# Checklist de Auditoria de Precedentes

Use este checklist para validar se cada precedente foi corretamente identificado, extraído e aplicado antes de finalizar a fundamentação.

---

## Bloco 1 — Identificação do precedente

- [ ] O tribunal foi identificado corretamente?
- [ ] O órgão julgador foi indicado (turma, câmara, plenário, seção)?
- [ ] O número do processo foi informado ou marcado como não informado?
- [ ] O relator foi informado ou marcado como não informado?
- [ ] A data do julgamento foi informada ou marcada como não informada?
- [ ] O tipo de precedente foi classificado: vinculante | qualificado | persuasivo | ilustrativo?

**Atenção:** Nunca inventar número de processo, relator ou data. Se não informado, registrar "não informado".

---

## Bloco 2 — Extração da ratio decidendi

- [ ] Os fatos relevantes do precedente foram identificados?
- [ ] A questão jurídica central foi isolada?
- [ ] A ratio decidendi foi extraída de forma precisa?
- [ ] O obiter dictum foi separado da ratio?
- [ ] A ementa foi tratada como meramente informativa, não como o precedente?
- [ ] O inteiro teor foi consultado quando a ementa era insuficiente?

**Alerta de patologia:** Se a fundamentação usa apenas a ementa, marcar `ha_cultura_da_ementa: true` no JSON.

---

## Bloco 3 — Força normativa

- [ ] A força normativa foi indicada corretamente?
- [ ] Decisão monocrática foi diferenciada de acórdão colegiado?
- [ ] Precedente de tribunal inferior foi identificado como persuasivo ou ilustrativo?
- [ ] Precedente formado em IRDR, IAC ou recurso repetitivo teve sua abrangência verificada?

---

## Bloco 4 — Analogia com o caso concreto

- [ ] Os fatos do caso atual foram comparados com os fatos do precedente?
- [ ] A semelhança fática foi demonstrada de forma explícita?
- [ ] A identidade da questão jurídica foi verificada?
- [ ] A analogia é material (fatos + direito) ou apenas temática (mesmo assunto)?
- [ ] Se apenas temática: marcar `ha_aproximacao_meramente_tematica: true` no JSON.
- [ ] A pertinência foi demonstrada, não presumida?

**Estrutura obrigatória de comparação:**
```
No precedente: [fatos determinantes]
No caso atual: [fatos equivalentes]
Analogia: [por que a semelhança é material]
```

---

## Bloco 5 — Distinguishing

- [ ] Há diferença fática relevante entre o precedente e o caso atual?
- [ ] A diferença é material (afeta a ratio) ou superficial?
- [ ] Se houver distinguishing necessário: o fundamento foi articulado de forma precisa?
- [ ] Se a parte adversária usou precedente: o distinguishing foi construído para afastá-lo?
- [ ] O impacto do distinguishing foi avaliado: baixo | médio | alto?

---

## Bloco 6 — Risco de superação

- [ ] O precedente foi classificado quanto ao risco: estável | estável com ressalvas | controvertido | em risco de superação | superado?
- [ ] Foram verificados votos vencidos relevantes?
- [ ] Foram verificadas mudanças legislativas posteriores ao julgado?
- [ ] Foram verificados julgamentos em sentido contrário em outros tribunais?
- [ ] Foram verificadas sinalizações de mudança de entendimento pelo próprio tribunal?

**Atenção:** Usar precedente em risco de superação sem alertar é falha grave. Marcar a classificação e justificar.

---

## Bloco 7 — Auditoria argumentativa final

- [ ] Há cultura da ementa? → `ha_cultura_da_ementa`
- [ ] Há aproximação meramente temática? → `ha_aproximacao_meramente_tematica`
- [ ] Há uso de obiter dictum como ratio decidendi? → `ha_uso_de_obiter_como_ratio`
- [ ] Há comparação fática suficiente? → `ha_comparacao_fatica_suficiente`
- [ ] O placar de força argumentativa foi avaliado: baixo | médio | alto?

---

## Bloco 8 — Checklist estratégico (Atuação de elite)

- [ ] A petição identifica a norma central além da mera ementa? (**Rigor na ratio**)
- [ ] Foi demonstrado o elo entre os fatos do caso atual e os do precedente? (**Analogia fática**)
- [ ] A fundamentação do juiz de primeiro grau foi auditada quanto a patologias? (**Auditoria de decisão**)
- [ ] A estratégia visa os fundamentos determinantes, não apenas o resultado? (**Foco na unidade**)
- [ ] Há dados técnicos, econômicos ou sociais que podem enriquecer a fundamentação? (**Inovação epistêmica**)

---

## Resultado esperado da auditoria

Após aplicar o checklist, toda fundamentação deve atender aos seguintes critérios mínimos:

| Critério | Padrão mínimo |
|---|---|
| Ratio decidendi extraída | Sim — não apenas ementa |
| Obiter dictum separado | Sim |
| Força normativa indicada | Sim |
| Comparação fática demonstrada | Sim — estrutura explícita |
| Distinguishing quando necessário | Sim |
| Risco de superação avaliado | Sim |
| Ausência dos 4 vícios principais | Confirmada |

Se algum critério mínimo não for atendido, a fundamentação deve ser revisada antes de ser incluída na peça.
