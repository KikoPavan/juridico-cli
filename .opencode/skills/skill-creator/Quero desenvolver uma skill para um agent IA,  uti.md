<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Quero desenvolver uma skill para um agent IA,  utilizando  o CLAUDE com skill-creator preciso de material para desenvolver a habilidade

Você consegue montar uma skill bem focada se transformar CREAC em um checklist operacional e em exemplos de entrada/saída para o agent. Abaixo organizei material já “pronto para usar” no skill-creator do Claude.[^1][^2][^3]

## 1. Definição operacional da habilidade

Objetivo da skill (descrição em linguagem natural, para colar no skill-creator):

- “Esta habilidade ajuda o modelo a organizar análises e textos jurídicos no formato CREAC (Conclusion, Rule, Explanation, Application, Conclusion), produzindo respostas estruturadas, claras e consistentes, adequadas a pareceres, memorandos e peças persuasivas.”[^2][^1]

**Comportamento padrão da skill:**

- Sempre estruturar cada questão jurídica em blocos C‑R‑E‑A‑C, mesmo que o usuário não use a palavra “CREAC”.[^1][^2]
- Manter tom objetivo em pareceres/memorandos; tom persuasivo moderado em petições, se o usuário sinalizar isso no prompt.[^4][^5]


## 2. Checklists internos (regras da skill)

Você pode colocar isso como “guidelines” no skill:

1. Bloco C (Conclusão inicial)
    - Enunciar em 1–3 frases a resposta à questão jurídica, com grau de certeza (“provavelmente”, “é pouco provável” etc.).[^6][^2]
    - Se houver vários sub‑pontos, dividir em C1, C2 etc. para cada sub‑questão.
2. Bloco R (Regra)
    - Indicar o enunciado geral da regra: dispositivos legais, súmulas, leading cases, requisitos/elementos.[^3][^2]
    - Se possível, estruturar em tópicos: requisito 1, requisito 2, exceções.[^2][^1]
3. Bloco E (Explanation)
    - Explicar a regra com base em precedentes e doutrina: como os tribunais interpretam cada elemento; quais fatores são relevantes.[^3][^1]
    - Fazer analogia/distinção rápida com 1–3 casos paradigmáticos (sem citar longamente).[^7][^3]
4. Bloco A (Application)
    - Aplicar, na mesma ordem dos elementos apresentados em E, os fatos do caso à regra.[^1][^3]
    - Tratar também contra‑argumentos plausíveis e explicar por que são mais fracos/fortes.[^4][^3]
5. Bloco C final (Conclusão de síntese)
    - Reafirmar a resposta resumida incorporando as nuances levantadas na aplicação (condições, riscos, incertezas).[^6][^2]

## 3. Exemplos de prompt + output (para few‑shots)

Use algo assim nos exemplos da skill (adaptando para seu contexto brasileiro):

### Exemplo 1 – Memorando objetivo (predictive memo)[^4][^2][^1]

Prompt de usuário (exemplo para few‑shot):
> “Analise, de forma objetiva, se é provável que o tribunal reconheça a nulidade de uma citação postal em ação de cobrança, no caso em que o AR foi assinado por terceiro na portaria do prédio. Estruture a resposta em CREAC.”

Resposta exemplo (resumida):

- **C – Conclusão:**
É pouco provável que o tribunal reconheça a nulidade da citação apenas porque o AR foi assinado por terceiro na portaria, desde que haja prova de que o destinatário residia no local e foi efetivamente cientificado.[^5][^2]
- **R – Regra:**
A citação postal é válida quando entregue no endereço correto do citando, admitindo‑se o recebimento por terceiro, salvo demonstração de prejuízo ou de que o citando não mais residia no local.[^8][^2]
- **E – Explicação da regra:**
A jurisprudência tende a considerar suficiente o recebimento por porteiro ou familiar quando o endereço corresponde à residência do réu, entendendo que a finalidade da citação (ciência da demanda) é atendida. Em hipóteses em que se reconheceu a nulidade, em geral havia prova de que o réu havia mudado de endereço ou que o terceiro não tinha qualquer vínculo com o destinatário.[^8]
- **A – Aplicação aos fatos:**
No caso concreto, o AR foi assinado por funcionário da portaria do prédio em que o devedor residia, sem indicação de mudança de endereço. Não há, até o momento, elementos de prova de que o réu não recebeu a comunicação interna da portaria, nem demonstração concreta de prejuízo à defesa. Assim, a situação se aproxima dos precedentes que validam a citação, e se afasta dos casos de nulidade nos quais havia ruptura do vínculo com o endereço ou ocultação dolosa da parte autora.[^8]
- **C – Conclusão final:**
Diante disso, a tendência é que o tribunal mantenha a validade da citação postal e rejeite a preliminar de nulidade, salvo se a parte conseguir demonstrar fato novo relevante (como mudança de endereço anterior à postagem).[^2][^8]


### Exemplo 2 – Peça persuasiva (recurso)[^6][^3]

Prompt de usuário (few‑shot):
> “Redija um argumento em CREAC defendendo, em apelação, que a multa contratual de 20% é abusiva em contrato de adesão de consumo.”

Resposta exemplo (bem compacta, mantendo CREAC):

- C: Conclusão favorável (multas de 20% em contratos de consumo costumam ser reduzidas em razão dos princípios da boa‑fé e do equilíbrio contratual).[^6]
- R: Artigos de CDC sobre cláusulas abusivas; entendimento de que penalidades excessivas podem ser revistas judicialmente.[^6]
- E: Decisões que reduziram multas superiores a 10% em situações análogas, destacando desproporcionalidade e vulnerabilidade do consumidor.[^3]
- A: Mostrar que o caso concreto repete esse padrão (adesão, ausência de negociação, valor elevado da obrigação principal, multa de 20% etc.).[^3]
- C: Reforçar o pedido de redução da multa para patamar razoável, alinhado à jurisprudência (por exemplo, 5–10%).[^3][^6]


## 4. Instruções de implementação no skill‑creator (Claude)

Sugestão de campos/instruções que você pode colar (ajuste à sintaxe da ferramenta):

- “Sempre que o usuário pedir análise jurídica de um caso concreto, organize a resposta em cinco blocos nomeados com títulos claros: ‘Conclusão (C)’, ‘Regra (R)’, ‘Explicação da regra (E)’, ‘Aplicação (A)’ e ‘Conclusão final (C)’, nesta ordem.”[^1][^2]
- “Se o usuário não mencionar CREAC, mas pedir ‘análise estruturada’ ou ‘fundamentação detalhada’, use CREAC por padrão, a menos que ele exija outro formato (por exemplo, IRAC).”[^2][^8]
- “Para pareceres/memos, use linguagem neutra e probabilística; para petições/recursos, use linguagem persuasiva moderada, mas preservando a estrutura CREAC.”[^5][^4]
- “Não reproduza textos de lei ou ementas longas; faça sínteses em linguagem própria, citando apenas o essencial.”[^7][^3]


## 5. Checklist de avaliação (para você testar a skill)

Depois de ativar a skill, teste o agent com 3–5 casos e avalie:

- A resposta sempre contém os cinco blocos C‑R‑E‑A‑C nomeados?
- A regra aparece antes da aplicação e está minimamente explicada com critérios/fatores?[^1][^2]
- A aplicação segue a mesma ordem dos elementos listados na explicação da regra?[^1][^3]
- A conclusão final é compatível com a análise feita e deixa claro o grau de incerteza?

Se quiser, posso te ajudar a escrever um “prompt de sistema” inteiro já no formato aceito pelo Claude (role system), encapsulando todas essas regras da skill. Você pensa em focar esse agent em um único ramo (ex.: cível/consumidor) ou deixá‑lo mais geral para qualquer área?
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^9]</span>

<div align="center">⁂</div>

[^1]: https://drew-m-loewe.gitbook.io/undergraduate-legal-writing-an-open-resource/essential-concepts-and-skills/rule-based-writing-and-creac

[^2]: https://www.law.columbia.edu/sites/default/files/2021-07/organizing_a_legal_discussion.pdf

[^3]: https://engagedscholarship.csuohio.edu/context/clevstlrev/article/3859/viewcontent/4_Kraft.pdf

[^4]: https://lawtutors.net/wp-content/uploads/2019/07/How-to-Write-an-Objective-Legal-Memo.pdf

[^5]: https://www.law.cuny.edu/academics/academic-resources-support/legal-writing-center/student-resources/drafting-a-law-office-memorandum/

[^6]: https://www.law.columbia.edu/sites/default/files/2022-06/WC Handout IRAC, CRAC, CREAC.revised 5.22.pdf

[^7]: https://www.legalwritingjournal.org/article/136367-teaching-cases-how-legal-writing-textbooks-approach-the-rule-support-section.pdf

[^8]: https://stmarys-ca.libguides.com/c.php?g=850387\&p=10434483

[^9]: https://www.reddit.com/r/LawSchool/comments/1fcsl7o/understanding_the_irac_crac_creac_method_of_legal/

[^10]: https://law.lclark.edu/centers/law_school_writing_center/tips_for_better_writing/creac/

[^11]: https://www.studocu.com/row/document/kenyatta-university/legal-research-and-writing/colombia-law-school-wc-organizing-legal-discusions/67813410

[^12]: https://www.youtube.com/watch?v=s22I4Bwaao0

[^13]: https://www.untdallas.edu/sites/default/files/center_for_writing_excellence-crac_overview.pdf

[^14]: https://uknowledge.uky.edu/law_facpub/519/

[^15]: https://www.westacademic.com/Interactive-Legal-Research-Writing-Objective-Writing-Writing-in-IRAC-IREAC-StREAC-CREAC-Form-Voigt

[^16]: https://www.scribd.com/document/1007803353/Module-2-IRAC-and-Organization-of-Legal-Writing-Legal-Writing-Online

