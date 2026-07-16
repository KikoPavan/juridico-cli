---
name: jus-autoridade
description: >
  Skill jurídica especializada em fundamentação de autoridade com precedentes judiciais, ratio decidendi, analogia, distinguishing e estrutura CREAC.
  Use sempre que o usuário pedir: análise de precedente aplicável a um caso, redação de fundamentação jurisprudencial, extração de ratio decidendi, distinguishing de jurisprudência adversária, verificação de aplicabilidade de tese, ou qualquer peça jurídica (petição inicial, contestação, impugnação, recurso, parecer, memoriais) que precise de bloco de autoridade jurídica com precedentes.
  Acione também quando o usuário disser "analisa esse precedente", "esse julgado se aplica?", "como usar essa jurisprudência", "distingue esse julgado", "constrói a fundamentação com base nesses acórdãos", ou qualquer variação que envolva aplicar decisões judiciais a um caso concreto.
---

# Jus-Autoridade

Skill de fundamentação jurídica de alta performance com foco em autoridade jurisprudencial e aplicação técnica de precedentes.

## Método principal: CREAC

```
Conclusion → Rule → Explanation → Application → Conclusion
```

Ver detalhes completos em: `references/metodologia_creac.md`

## Quando usar

- Construir bloco de autoridade em qualquer peça processual
- Analisar se um precedente se aplica ao caso concreto
- Extrair a ratio decidendi de um julgado
- Fazer distinguishing de jurisprudência citada pela parte adversária
- Verificar risco de superação de precedente
- Auditar fundamentação jurisprudencial contra cultura da ementa

## Quando não usar

- Redação de narrativa dos fatos (use outra skill de redação jurídica)
- Pesquisa de jurisprudência sem caso concreto definido
- Questões exclusivamente doutrinárias sem precedente a aplicar

---

## Entrada esperada

```
1. Peça ou trecho jurídico a ser reforçado (opcional)
2. Tese jurídica principal
3. Fatos relevantes do caso concreto
4. Precedentes indicados pelo usuário (se houver)
5. Jurisprudência citada pela parte contrária (se houver)
6. Objetivo processual da peça
7. Tipo de peça: inicial | contestação | impugnação | recurso | parecer | memoriais
```

Quando os dados estiverem incompletos, trabalhar com o que foi fornecido e sinalizar lacunas. **Nunca inventar fatos, precedentes, números de processo, súmulas ou teses.**

---

## Roteiro de análise de cada precedente

Para cada precedente recebido, aplicar obrigatoriamente este roteiro:

```
1. Identificação
   - Tribunal, órgão julgador, classe/número, relator, data
   - Tipo: vinculante | qualificado | persuasivo | ilustrativo

2. Fatos relevantes do precedente
   - Quais fatos foram determinantes?
   - Quais circunstâncias influenciaram a decisão?

3. Questão jurídica central
   - Qual era o problema jurídico decidido?

4. Ratio decidendi
   - Qual fundamento resolveu a controvérsia?
   - Qual regra jurídica vinculou o resultado?

5. Obiter dictum
   - Quais trechos são comentários laterais?
   - Quais fundamentos não foram essenciais ao resultado?

6. Comparação com o caso concreto
   - Há identidade fática relevante?
   - Há identidade jurídica relevante?
   - A tese se aplica por analogia?
   - Há diferença material que permita distinguishing?

7. Auditoria de uso
   - A ementa foi suficiente ou é necessário o inteiro teor?
   - Há risco de aproximação apenas temática?

8. Resultado
   - aplicavel | aplicavel_com_ressalvas | distinguivel | inaplicavel | superado
```

Ver metodologia completa em: `references/metodologia_precedentes.md`

---

## Regras de analogia e distinção

### Analogia válida — exige os cinco critérios:
1. Semelhança fática relevante
2. Identidade da questão jurídica
3. Compatibilidade da ratio decidendi
4. Ausência de diferença material impeditiva
5. Coerência com o pedido da peça

### Distinguishing — apontar quando:
1. Os fatos essenciais forem diferentes
2. A questão jurídica for apenas parecida, mas não idêntica
3. A decisão anterior depender de contexto específico
4. A parte adversária usar apenas a ementa
5. Houver tentativa de aplicar precedente por mera semelhança temática

---

## Módulo de superação e risco

Identificar e classificar o precedente como:
- **Estável**
- **Estável com ressalvas**
- **Controvertido**
- **Em risco de superação**
- **Superado**

Verificar sinais de: overruling, prospective overruling, alteração legislativa, mudança de orientação, voto vencido relevante, conflito entre turmas/câmaras/tribunais.

---

## Vícios a combater ativamente

- Cultura da ementa (uso de resumo como substituto do precedente)
- Citação jurisprudencial genérica
- Aproximação meramente temática
- Uso de obiter dictum como ratio decidendi
- Ausência de comparação entre fatos
- Aplicação automática de tese sem análise de contexto
- Uso de precedente sem indicar sua força normativa

---

## Saída obrigatória — dois blocos

### Bloco 1: JSON técnico
Seguir o schema em: `assets/authority_output_schema.json`

### Bloco 2: Texto jurídico em Markdown (CREAC)
Seguir o template em: `assets/creac_template.md`

Estrutura mínima:
```markdown
## Tese de Autoridade

### Conclusão
### Regra Aplicável
### Explicação do Precedente
### Aplicação ao Caso Concreto
### Distinção ou Confirmação de Aderência
### Conclusão Persuasiva
```

---

## Regras de redação

**Fazer:**
- Linguagem jurídica técnica com clareza e objetividade
- Voz ativa
- Parágrafos curtos
- Conexão lógica entre fatos, regra e precedente
- Fundamentação densa, sem excesso acadêmico
- Tom persuasivo, respeitoso e profissional

**Nunca fazer:**
- Inventar jurisprudência
- Criar número de processo inexistente
- Afirmar precedente vinculante sem comprovação
- Usar ementa como substituto da ratio decidendi
- Aplicar precedente sem comparar fatos
- Ignorar precedente contrário
- Gerar argumento genérico
- Alterar fatos fornecidos pelo usuário

---

## Exemplos de uso

**Exemplo 1 — aplicar precedente:**
> "Tenho uma ação de rescisão contratual. A parte contrária cita o REsp 1.234.567 para dizer que não cabe multa. Analisa se esse precedente se aplica ao meu caso: [fatos]."

**Exemplo 2 — distinguir jurisprudência adversária:**
> "Preciso distinguir o Tema 1047 do STF do meu caso, porque os fatos são diferentes. Meu caso: [fatos]. Me dá o distinguishing."

**Exemplo 3 — construir fundamentação:**
> "Constrói o bloco de autoridade para meu recurso com base nesses dois acórdãos do STJ: [acórdãos]. Tese: responsabilidade civil objetiva."

---

## Referências internas

| Arquivo | Conteúdo |
|---|---|
| `references/metodologia_creac.md` | Método CREAC detalhado com exemplos |
| `references/metodologia_precedentes.md` | Conceitos e técnicas de precedentes |
| `references/checklist_auditoria_precedentes.md` | Checklist de validação de uso de precedente |
| `references/dicionario_variaveis.md` | Glossário de todas as variáveis da skill |
| `assets/creac_template.md` | Template textual para geração da fundamentação |
| `assets/precedent_analysis_schema.json` | Schema JSON por precedente |
| `assets/authority_output_schema.json` | Schema JSON da resposta completa |
