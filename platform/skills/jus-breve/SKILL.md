---
name: jus-breve
description: >
  Análise jurídica aprofundada pelo método FIRAC (Facts, Issue, Rule, Application, Conclusion) para
  documentos jurídicos brasileiros. Use esta skill sempre que o usuário precisar: produzir relatório
  de auditoria jurídica ou due diligence; criar case briefs ou fichas de jurisprudência; elaborar
  resumos processuais completos para clientes ou superiores; ou quando mencionar "FIRAC", "due diligence
  jurídica", "auditoria jurídica", "brief de jurisprudência", "case brief", "relatório jurídico",
  "ficha de julgado", "análise completa do caso", "analisar jurisprudência", "resumo de acórdão para
  relatório" ou qualquer variação. Exige processamento fático prévio como barreira anti-alucinação:
  sem fatos confirmados não há problema jurídico. Entrega obrigatória em JSON estruturado + sumário
  executivo em Markdown. Prefira esta skill sobre Jus-Diagnose quando o documento for um acórdão,
  relatório, contrato complexo ou qualquer peça com contexto fático denso.
---

# Jus-Breve — Análise FIRAC

Método de análise jurídica com **barreira fática de contenção**: o problema jurídico só é formulado
**após** o mapeamento e validação das precondições fáticas. Isso impede que o modelo projete questões
jurídicas para fatos que não existem no documento.

---

## Princípio Operacional

```
FATOS VERIFICADOS → PROBLEMA → NORMA → SUBSUNÇÃO → CONCLUSÃO
        F               I          R          A            C
```

A diferença crítica em relação ao IRAC é o estágio **F (Facts)**:
> *"Sem fatos verificados, não existe questão jurídica."*

Este princípio cria uma **barreira de contenção anti-alucinação**. O modelo deve resistir à tentação
de formular Issues baseadas em presunções, inferências ou conhecimento externo ao documento.

---

## Workflow de Execução

### Passo 1 — Leitura Estruturada do Input

Leia o documento integralmente. Identifique:
- Tipo de peça (acórdão, relatório, contrato, due diligence)
- Partes e relação jurídica subjacente
- Período temporal coberto pelos fatos

Consulte `references/variables.md` para o dicionário completo de variáveis.

### Passo 2 — F: Facts (Precondições Fáticas)

**Esta etapa é obrigatória e não pode ser pulada.**

#### 2.1 — Inventário Fático
Liste **apenas fatos explicitamente declarados** no documento. Para cada fato:
- Atribua um ID (`F-01`, `F-02`, ...)
- Classifique o tipo: `CONTRATUAL`, `TEMPORAL`, `PATRIMONIAL`, `COMPORTAMENTAL`, `PROCESSUAL`, `OUTROS`
- Indique a fonte: citação direta, inferência necessária ou inferência especulativa
- **Marque como `ESPECULATIVO`** qualquer fato não comprovado textualmente

#### 2.2 — Barreira de Contenção
Antes de prosseguir para a Issue, verifique:
- [ ] Todos os fatos estão classificados?
- [ ] Há pelo menos 1 fato `COMPROVADO` (não especulativo)?
- [ ] Os fatos especulativos estão devidamente sinalizados?

Se nenhum fato comprovado for identificado, o output deve retornar `status_analise: "BLOQUEADO"`
com `motivo_bloqueio` explicado.

### Passo 3 — I: Issue (Questão Jurídica)

Só execute este passo após validar a Barreira de Contenção.

- Formule a questão jurídica **exclusivamente** com base nos fatos `COMPROVADO` ou `INFERIDO_NECESSARIO`
- Fatos `ESPECULATIVO` **não podem** fundamentar a Issue
- Vincule cada Issue a pelo menos 1 Fact ID (`facts_ref`)
- Se houver múltiplas issues, ordene por prejudicialidade

### Passo 4 — R: Rule (Regra Aplicável)

- Cite norma com precisão: diploma legal + artigo + inciso/parágrafo
- Inclua ementas de julgados quando o documento for jurisprudência
- Máximo de 5 normas por issue (mais que isso indica que a issue precisa ser desmembrada)
- Para acórdãos: extraia a **ratio decidendi** separada dos obiter dicta

### Passo 5 — A: Application (Subsunção Contextualizada)

Diferente do IRAC simples, a Application do FIRAC inclui:
- **Contexto fático**: como o fato se enquadra na norma no contexto específico do caso
- **Contrafactual**: o que aconteceria se o fato-chave fosse diferente
- **Casos análogos**: referências a precedentes se mencionados no documento

Status possíveis: `PRESENTE`, `AUSENTE`, `PARCIAL`, `CONTROVERSO`, `DEPENDENTE_PROVA`

### Passo 6 — C: Conclusion (Conclusão Fundamentada)

- Responda à Issue com fundamento duplo: **norma** + **fato comprovado**
- Avalie impacto prático quando aplicável (ex.: due diligence → risco identificado)
- Para jurisprudência: extraia a **tese jurídica** e o **dispositivo**
- Classifique o nível de risco jurídico: `CRITICO`, `RELEVANTE`, `MODERADO`, `BAIXO`, `NULO`

### Passo 7 — Montagem do Output

```bash
python scripts/firac_analyzer.py validate --file resultado.json
python scripts/firac_analyzer.py render-markdown --file resultado.json
```

Se o ambiente não suportar execução de scripts, siga o schema manualmente conforme
`assets/firac_schema.json`.

**Estrutura obrigatória de output:**
1. **Bloco JSON** — conforme `assets/firac_schema.json`
2. **Sumário Executivo Markdown** — template em `references/variables.md` (seção "Sumário")

---

## Regras de Qualidade

| Regra | Descrição |
|-------|-----------|
| **Barreira fática** | Issues derivadas apenas de fatos comprovados/inferidos necessários |
| **Anti-alucinação** | Proibido inserir fatos externos ao documento |
| **Precisão normativa** | Toda citação legal: número de lei + artigo |
| **Ratio vs. obiter** | Em acórdãos, distinguir tese vinculante de considerações laterais |
| **Risco quantificado** | Toda conclusão em due diligence deve ter nível de risco |
| **Língua** | Output sempre em português brasileiro |
| **Completude** | Todos os 5 campos FIRAC presentes, mesmo que com `null` justificado |

---

## Uso Ideal

| Cenário | Por quê FIRAC |
|---------|---------------|
| Auditoria jurídica | Mapeamento fático evita conclusões sem suporte |
| Due diligence de M&A ou imóveis | Análise de risco por fato verificável |
| Case briefs de jurisprudência | Separação ratio decidendi / obiter dicta |
| Resumo processual para cliente | Visão completa: fatos + direito + risco |
| Análise de contratos complexos | Inventário de cláusulas como fatos jurídicos |

---

## Arquivos de Suporte

| Arquivo | Quando Consultar |
|---------|-----------------|
| `references/variables.md` | Dicionário de variáveis + template sumário Markdown |
| `assets/firac_schema.json` | Schema JSON para validação |
| `scripts/firac_analyzer.py` | Script Python para geração e validação |

---

## Comparativo com Jus-Diagnose

| Aspecto | Jus-Diagnose (IRAC) | Jus-Breve (FIRAC) |
|---------|---------------------|-------------------|
| Ponto de entrada | Problema jurídico | Fatos verificados |
| Proteção anti-alucinação | Básica | Forte (barreira fática) |
| Profundidade | Triagem rápida | Análise completa |
| Tempo de execução | Rápido | Moderado |
| Uso primário | Exames, triagem | Relatórios, due diligence |
