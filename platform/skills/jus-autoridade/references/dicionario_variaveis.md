# Dicionário de Variáveis — Jus-Autoridade

Referência de todas as variáveis usadas pela skill, seus tipos, valores possíveis e descrições.

---

## Variáveis de entrada (CreateAuthorityRequest)

| Variável | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `peca_ou_trecho` | string | Não | Texto da peça ou trecho a ser reforçado |
| `tese_principal` | string | Sim | A tese jurídica central a ser sustentada |
| `fatos_relevantes` | string | Sim | Fatos relevantes do caso concreto |
| `precedentes_indicados` | array[string] | Não | Precedentes fornecidos pelo usuário |
| `jurisprudencia_adversaria` | array[string] | Não | Jurisprudência citada pela parte contrária |
| `objetivo_processual` | string | Não | O que se quer obter com a peça |
| `tipo_de_peca` | enum | Sim | inicial \| contestação \| impugnação \| recurso \| parecer \| memoriais |

---

## Variáveis do precedente (PrecedentAnalysis)

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `tribunal` | string | Livre | STF, STJ, TRT-X, TJXX etc. |
| `orgao_julgador` | string | Livre | Plenário, Turma, Câmara, Seção |
| `processo` | string | Livre / "não informado" | Classe e número. Nunca inventar. |
| `relator` | string | Livre / "não informado" | Nome do relator. Nunca inventar. |
| `data_julgamento` | string | Livre / "não informado" | Data. Nunca inventar. |
| `tipo_precedente` | enum | vinculante \| qualificado \| persuasivo \| ilustrativo | Força normativa |
| `fatos_relevantes_do_precedente` | array[string] | Livre | Fatos determinantes do julgado |
| `questao_juridica_decidida` | string | Livre | Problema jurídico central |
| `ratio_decidendi` | string | Livre | Fundamento determinante vinculante |
| `obiter_dictum_identificado` | array[string] | Livre | Trechos não vinculantes |
| `forca_normativa` | string | Livre | Descrição da força normativa |

---

## Variáveis de analogia

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `semelhancas_faticas` | array[string] | Livre | Fatos do caso atual análogos ao precedente |
| `semelhancas_juridicas` | array[string] | Livre | Questões jurídicas comuns |
| `grau_de_aderencia` | enum | baixo \| medio \| alto | Grau de aderência entre precedente e caso atual |

---

## Variáveis de distinguishing

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `existe` | boolean | true \| false | Se há diferença material que justifica o distinguishing |
| `fundamento` | string | Livre | Qual diferença fática ou jurídica justifica o distinguishing |
| `impacto` | enum | baixo \| medio \| alto | Impacto sobre a aplicabilidade do precedente |

---

## Variáveis de risco de superação

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `classificacao` | enum | estavel \| estavel_com_ressalvas \| controvertido \| em_risco_de_superacao \| superado | Status de estabilidade do precedente |
| `justificativa` | string | Livre | Por que recebeu essa classificação |

---

## Variável de conclusão de uso

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `conclusao_de_uso` | enum | aplicavel \| aplicavel_com_ressalvas \| distinguivel \| inaplicavel \| superado | Resultado final da análise de aplicabilidade |

---

## Variáveis da auditoria argumentativa

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `ha_cultura_da_ementa` | boolean | true \| false | Risco de uso de ementa como substituto do precedente |
| `ha_aproximacao_meramente_tematica` | boolean | true \| false | Precedente atraído apenas por identidade de assunto |
| `ha_uso_de_obiter_como_ratio` | boolean | true \| false | Obiter dictum sendo usado como ratio decidendi |
| `ha_comparacao_fatica_suficiente` | boolean | true \| false | Comparação fática adequada foi demonstrada |
| `observacoes` | array[string] | Livre | Observações específicas sobre qualidade argumentativa |

---

## Variáveis do placar de força argumentativa

| Variável | Tipo | Valores possíveis | Descrição |
|---|---|---|---|
| `classificacao` | enum | baixo \| medio \| alto | Avaliação geral da força da fundamentação |
| `justificativa` | string | Livre | Por que recebeu essa classificação |

---

## Constantes internas (não expostas ao usuário)

| Constante | Valor fixo | Descrição |
|---|---|---|
| `skill` | `"Jus-Autoridade"` | Identificador da skill |
| `metodo` | `"CREAC"` | Método estrutural obrigatório |
| `estrutura` | `"HOOK_CONTENT_CTA"` | Não aplicável (uso de CREAC, não de conteúdo de redes sociais) |

---

## Regras de preenchimento

1. **Nunca inventar:** processo, relator, data, tese, súmula ou número de julgado
2. **"não informado"** é a resposta correta quando o dado não foi fornecido
3. **Enum inválido** deve ser recusado — registrar observação e solicitar esclarecimento
4. **Arrays vazios** são permitidos quando não há dado para preencher
5. **Strings livres** devem ser fiéis ao conteúdo fornecido pelo usuário ou extraído do precedente
