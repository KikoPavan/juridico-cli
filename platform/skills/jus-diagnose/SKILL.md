---
name: jus-diagnose
description: >
  Análise jurídica estruturada pelo método IRAC (Issue, Rule, Application, Conclusion) para documentos
  jurídicos brasileiros. Use esta skill sempre que o usuário precisar: identificar rapidamente o problema
  jurídico de uma peça processual, resumo de aula ou ementa; fazer triagem inicial de petições contrárias;
  realizar análise de questões de exame (OAB, concursos); ou quando mencionar "IRAC", "diagnose jurídico",
  "triagem jurídica", "resumo de petição", "qual o problema jurídico", "analise esta peça",
  "identifique o problema", "subsunção", "enquadramento legal" ou qualquer variação. Entrega obrigatória
  em JSON estruturado + sumário executivo em Markdown. Ative mesmo para solicitações parciais como
  "analisa isso pra mim" quando houver um documento jurídico em contexto.
---

# Jus-Diagnose — Análise IRAC

Método de análise jurídica que **reduz a complexidade** de qualquer questão legal a uma equação de
quatro variáveis. Opera em modo **gatilho neutro**: não toma partido, apenas mapeia.

---

## Princípio Operacional

```
PROBLEMA → NORMA → SUBSUNÇÃO → CONCLUSÃO
   I           R          A            C
```

A lógica é dedutiva e mecânica. O modelo não deve adicionar opinião ou estratégia —
apenas identificar, enquadrar e concluir. Argumentação é tarefa de outra skill.

---

## Workflow de Execução

### Passo 1 — Leitura Estruturada do Input

Leia o documento integralmente antes de iniciar a análise. Identifique:
- Tipo de peça (petição, sentença, contrato, ementa, enunciado)
- Partes envolvidas (se aplicável)
- Ramo do direito dominante

Consulte `references/variables.md` para o dicionário completo de variáveis de output.

### Passo 2 — Execução IRAC

Execute cada componente em sequência. **Não pule etapas.**

#### I — Issue (Questão Jurídica)
- Formule em **uma única pergunta objetiva**
- Formato: *"[Sujeito] tem direito/responsabilidade/obrigação de [conduta] em razão de [fato]?"*
- Proibido: afirmações, opiniões, conclusões antecipadas
- Se houver múltiplas issues, liste-as em ordem de prejudicialidade

#### R — Rule (Regra Aplicável)
- Cite a norma com precisão: diploma legal + artigo + inciso/parágrafo (se aplicável)
- Inclua enunciados de súmula ou tese de repercussão geral quando relevante
- Máximo de 3 normas por issue (priorize hierarquia: CF > lei federal > lei estadual > regulamento)

#### A — Application (Subsunção)
- Mapeie os **fatos do caso** sobre os **elementos da norma**
- Formato: *"O fato [X] corresponde ao elemento [Y] da norma [Z]"*
- Se um elemento da norma **não** está presente nos fatos, registre explicitamente como `AUSENTE`
- Não infira fatos não declarados no documento

#### C — Conclusion (Conclusão)
- Responda diretamente à Issue formulada
- Binário quando possível: *"Sim / Não, porque [norma] + [fato mapeado]"*
- Se a conclusão depender de fatos não verificáveis, use: `CONDICIONAL: [condição]`

### Passo 3 — Montagem do Output

Execute o script de validação e geração:

```bash
python scripts/irac_analyzer.py --validate
```

Se o ambiente não suportar execução de scripts, siga o schema manualmente conforme
`assets/irac_schema.json`.

**Estrutura obrigatória de output:**

1. **Bloco JSON** — estruturado conforme schema em `assets/irac_schema.json`
2. **Sumário Executivo Markdown** — template em `references/variables.md` (seção "Sumário")

---

## Regras de Qualidade

| Regra | Descrição |
|-------|-----------|
| **Neutralidade** | Proibido usar linguagem partidária ("claramente", "evidentemente", "absurdo") |
| **Precisão normativa** | Toda citação legal deve ter número de lei + artigo |
| **Escopo fechado** | Analise apenas o que está no documento; não extrapole |
| **Língua** | Output sempre em português brasileiro |
| **Completude** | Todos os 4 campos IRAC devem estar presentes, mesmo que com valor `null` justificado |

---

## Uso Ideal

- Resumos de aula e fichamentos jurídicos
- Triagem de petições contrárias (identificar o "coração" do argumento adverso)
- Resolução de questões de exame (OAB, concursos públicos)
- Primeira leitura de novos processos

---

## Arquivos de Suporte

| Arquivo | Quando Consultar |
|---------|-----------------|
| `references/variables.md` | Dicionário de variáveis + template de sumário Markdown |
| `assets/irac_schema.json` | Schema JSON para validação do output |
| `scripts/irac_analyzer.py` | Script Python para geração e validação automatizada |

---

## Limitações

Esta skill **não** realiza:
- Estratégia processual ou recomendação de teses
- Pesquisa de jurisprudência atualizada
- Análise de admissibilidade recursal
- Due diligence fática aprofundada (→ use Jus-Breve para isso)
