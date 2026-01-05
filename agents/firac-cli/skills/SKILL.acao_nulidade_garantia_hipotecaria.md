---
name: firac_acao_nulidade_garantia_hipotecaria
agent: firac-cli
process_types:
  - ACAO_NULIDADE_GARANTIA_HIPOTECARIA
descricao: >
  Skill específica do firac-cli para ações declaratórias de nulidade ou
  ineficácia de escrituras de confissão de dívida com garantias hipotecárias,
  envolvendo excesso de mandato e violação de cláusulas contratuais societárias.
versao: 0.1
---

# Escopo desta Skill

Use estas instruções quando:

- `processo.tipo_processo` em `data/context.json` for `ACAO_NULIDADE_GARANTIA_HIPOTECARIA`, ou
- o contexto indique discussão sobre nulidade/ineficácia de escritura de confissão de dívida
  com garantia hipotecária baseada em:
  - excesso de mandato
  - violação de cláusulas de contrato social
  - uso indevido de bens recebidos por cisão.

## Foco específico da análise

Nesta Skill, o firac-cli deve dar ênfase às seguintes linhas:

1. **Poderes de representação e excesso de mandato**
   - Confrontar:
     - poderes constantes da procuração (campos `procuracoes[]` em `context.json`);
     - cláusulas do contrato social da sociedade proprietária (campo `empresas.jkmg.clausulas_relevantes`).
   - Verificar se:
     - a constituição de hipoteca em nome da sociedade está claramente autorizada;
     - há vedação expressa a garantias (fiança, aval, hipoteca) ou limitação de uso da firma.

2. **Origem e titularidade dos imóveis hipotecados**
   - Usar `imoveis_hipotecados[]` e `garantias` de `context.json`.
   - Destacar que:
     - os imóveis foram recebidos por cisão de outra sociedade;
     - é necessário checar se, na data da escritura, a titularidade estava regular
       e se havia autorização societária para oneração.

3. **Conexão com as garantias e confissão de dívida**
   - Identificar o instrumento específico:
     - data da escritura de confissão de dívidas com hipoteca;
     - quem assinou, em nome de quem e com base em quais poderes.
   - Avaliar:
     - se a confissão de dívida extrapola o mandato;
     - se a hipoteca foi prestada em benefício de terceiros sem amparo contratual.

4. **Efeitos sobre a eficácia da garantia**
   - Basear-se em:
     - cláusulas que limitam a responsabilidade da sociedade (“obriga apenas o sócio infrator”);
     - princípios de mandato, representação e poderes dos administradores.
   - Construir a análise em termos de:
     - nulidade absoluta, relativa ou mera ineficácia em relação à sociedade e aos sócios inocentes;
     - distinção entre a obrigação principal e a garantia real prestada.

## Como usar `context.json` e `contexto_relacoes.json`

- De `data/context.json`, levar em conta especialmente:
  - `processo.tese_principal` e `processo.questoes_a_provar`;
  - `empresas.jkmg.clausulas_relevantes`;
  - `procuracoes[]` (poderes explícitos e não mencionados);
  - `imoveis_hipotecados[]` e `garantias`;
  - `hipoteses_tese_juridica` e `lacunas_a_verificar`.

- De `data/contexto_relacoes.json`, quando disponível:
  - `relacoes_pessoa_empresa` para entender se o signatário era sócio, administrador ou mero procurador;
  - `relacoes_terceiros_pessoas` para identificar possíveis simulações ou negócios entre terceiros
    e sócios que afetam a análise da garantia.

## Orientações para a estrutura FIRAC neste tipo de caso

1. **Facts (Fatos)**  
   - Organizar os fatos em blocos:
     - cadeia societária (cisão, contratos sociais, cláusulas 9ª e 10ª);
     - cadeia de poderes (procurações, atos de administração);
     - cadeia de garantias (hipotecas anteriores, aditivos, escritura impugnada).

2. **Issue (Questões)**  
   - Formular questões claras, por exemplo:
     - “Se a sócia-gerente/procurador possuía poderes para constituir hipoteca em nome da JKMG.”
     - “Se a cláusula 10ª do contrato social torna a garantia ineficaz em relação à sociedade.”

3. **Rule (Regras)**  
   - Incluir:
     - cláusulas contratuais relevantes;
     - normas de mandato e administração societária;
     - precedentes trazidos pelo case-law-cli (quando houver).

4. **Application (Aplicação)**  
   - Cruzar:
     - poderes conferidos x cláusulas restritivas;
     - origem dos imóveis x garantias prestadas;
     - comportamento do procurador/administrador x limites do mandato.

5. **Conclusion (Conclusão)**  
   - Indicar:
     - em que medida a garantia é nula, ineficaz ou oponível apenas ao sócio infrator;
     - quais pontos ainda dependem de prova (lacunas explicitadas em `lacunas_a_verificar`).

## Regras de cautela

- Não afirmar nulidade de forma categórica se a prova for incompleta; indicar o grau de robustez.
- Sempre mencionar as `lacunas_a_verificar` relevantes para a conclusão.
- Manter distinção entre:
  - validade da dívida confessada;
  - validade/eficácia da hipoteca como garantia.
