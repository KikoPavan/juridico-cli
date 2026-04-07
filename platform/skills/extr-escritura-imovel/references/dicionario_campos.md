# Dicionário de Campos — escritura_imovel.schema.json

Derivado de `assets/escritura_imovel.schema.json`.
Legenda: **Obrig.** = obrigatório dentro do objeto pai; **Tipo** inclui `null` quando permitido.

---

## Objeto raiz

| Campo                   | Tipo           | Obrig. | Descrição                                                      |
|-------------------------|----------------|--------|----------------------------------------------------------------|
| `tipo_documento`        | string         | não    | Tipo de documento. Default: `"Escritura de Imóvel/Matrícula"` |
| `matricula`             | string \| null | não    | Número da matrícula do imóvel                                  |
| `cartorio`              | string \| null | não    | Cartório responsável pela matrícula                            |
| `transacoes_venda`      | array          | não    | Histórico de transações de compra e venda                      |
| `transacoes_venda_posse`| array          | não    | Registros de usufruto, uso, habitação e outros direitos        |
| `hipotecas_onus`        | array \| null  | não    | Hipotecas, alienações fiduciárias e demais ônus                |
| `historico_titularidade`| array \| null  | não    | Períodos de titularidade do imóvel                             |

---

## `transacoes_venda[]` — TransacaoCompraVenda

| Campo                          | Tipo             | Obrig. | Descrição                                                                                        |
|--------------------------------|------------------|--------|--------------------------------------------------------------------------------------------------|
| `registro`                     | string           | **sim**| Identificador do ato (ex.: `"R.46"`)                                                             |
| `anuencia_credor`              | string \| null   | não    | Texto de quem autorizou/concordou com a venda (ex.: banco credor)                                |
| `data_registro`                | string \| null   | **sim**| Data do lançamento na matrícula                                                                  |
| `data_efetiva`                 | string \| null   | **sim**| Data em que o contrato foi celebrado                                                             |
| `vendedores`                   | array\<string\>  | **sim**| Lista completa de vendedores                                                                     |
| `compradores`                  | array\<string\>  | **sim**| Lista completa de compradores                                                                    |
| `valor`                        | string           | **sim**| Valor literal com moeda (ex.: `"R$ 10.000,00"`)                                                  |
| `folha_localizacao`            | string \| null   | não    | Número da folha onde o registro aparece                                                          |
| `tipo_transacao`               | string \| null   | não    | Classificação jurídica (ex.: `"COMPRA_VENDA"`, `"VENDA_DEFINITIVA"`)                             |
| `possui_pacto_retrovenda`      | boolean \| null  | não    | `true` se houver cláusula de retrovenda                                                          |
| `consolida_titularidade`       | boolean \| null  | não    | `true` se o registro consolida a propriedade                                                     |
| `observacao_juridica`          | string \| null   | não    | Resumo jurídico do efeito do registro                                                            |
| `contrato_arquivado_em_cartorio`| boolean \| null | não    | `true` se as condições constam de título arquivado em cartório                                   |
| `texto_contrato_arquivado`     | string \| null   | não    | Trecho literal sobre o contrato arquivado                                                        |

---

## `transacoes_venda_posse[]` — TransacaoPosseUsufruto

| Campo                 | Tipo            | Obrig. | Descrição                                                                              |
|-----------------------|-----------------|--------|----------------------------------------------------------------------------------------|
| `registro_ou_averbacao`| string         | **sim**| Número do registro (R) ou averbação (Av)                                               |
| `data_registro`       | string \| null  | **sim**| Data do lançamento na matrícula                                                        |
| `data_efetiva`        | string \| null  | **sim**| Data em que o direito foi constituído                                                  |
| `tipo_posse`          | string \| null  | **sim**| Ex.: `"CONCESSAO_USUFRUTO"`, `"BAIXA_USUFRUTO"`, `"USO"`, `"HABITACAO"`               |
| `beneficiario`        | string \| null  | não    | Pessoa em favor de quem é constituído o direito                                        |
| `nu_proprietario`     | string \| null  | não    | Proprietário(s) do imóvel (nu-proprietário)                                            |
| `prazo`               | string \| null  | não    | Prazo contratual ou duração                                                            |
| `detalhes`            | string \| null  | não    | Resumo textual do conteúdo do registro/averbação                                       |
| `folha_localizacao`   | string \| null  | não    | Número da folha onde consta o registro                                                 |

---

## `hipotecas_onus[]` — HipotecaOnus

| Campo                                   | Tipo             | Obrig. | Descrição                                                                                                       |
|-----------------------------------------|------------------|--------|-----------------------------------------------------------------------------------------------------------------|
| `registro_ou_averbacao`                 | string \| null   | **sim**| Identificador do ato (ex.: `"R.5"`, `"Av.24"`)                                                                 |
| `historico_aditivos`                    | array \| null    | não    | Aditivos contratuais que modificaram o registro                                                                 |
| `historico_aditivos[].averbacao`        | string           | não    | Identificador da averbação do aditivo                                                                           |
| `historico_aditivos[].data`             | string           | não    | Data do aditivo                                                                                                 |
| `historico_aditivos[].resumo`           | string           | não    | Resumo do aditivo                                                                                               |
| `data_registro`                         | string \| null   | **sim**| Data do lançamento na matrícula                                                                                 |
| `data_efetiva`                          | string \| null   | **sim**| Data em que o contrato foi celebrado                                                                            |
| `tipo_divida`                           | string \| null   | **sim**| Natureza da obrigação (ex.: `"HIPOTECA"`, `"ALIENACAO_FIDUCIARIA"`, `"ARRENDAMENTO_MERCANTIL"`)                 |
| `numero_contrato`                       | string \| null   | não    | Número do contrato bancário ou instrumento                                                                      |
| `credor`                                | string \| null   | **sim**| Instituição ou pessoa em favor de quem é constituída a garantia                                                 |
| `valor_divida_original`                 | string \| null   | **sim**| Valor original literal com moeda (ex.: `"CR$ 2.581.000,00"`)                                                   |
| `valor_divida`                          | string \| null   | não    | Valor em R$ quando o original já for R$; `null` para moeda antiga                                              |
| `prazo`                                 | integer \| null  | não    | Número total de parcelas/prestações                                                                             |
| `vencimento`                            | string \| null   | não    | Data de vencimento da última prestação                                                                          |
| `taxas`                                 | string \| null   | não    | Juros, comissões e outros encargos                                                                              |
| `quitada`                               | boolean \| null  | não    | `true` se a matrícula mencionar quitação; `null` se não mencionado                                             |
| `cancelada`                             | boolean \| null  | não    | `true` se o ônus constar como cancelado/baixado                                                                 |
| `detalhes_baixa`                        | string \| null   | não    | Trecho literal descrevendo o cancelamento/baixa                                                                 |
| `averbacao_baixa`                       | string \| null   | não    | Averbação que formaliza a baixa (ex.: `"Av.47"`)                                                                |
| `data_baixa`                            | string \| null   | não    | Data efetiva da baixa (**nunca** a data_registro; ver nota abaixo)                                              |
| `folha_localizacao`                     | string \| null   | não    | Folha(s) onde o ônus aparece                                                                                    |
| `valor_presente`                        | string \| null   | não    | Valor corrigido na data da baixa, se informado                                                                  |
| `contrato_arquivado_em_cartorio`        | boolean \| null  | não    | `true` se as condições constam de título arquivado em cartório                                                  |
| `texto_contrato_arquivado`              | string \| null   | não    | Trecho literal sobre o contrato arquivado                                                                       |
| `informacoes_devedor_dependem_de_contrato`| boolean \| null| não    | `true` quando a identificação do devedor depende do contrato arquivado                                          |

> **Nota `data_baixa`:** usar sempre a `data_efetiva` da averbação de baixa, **não** a `data_registro`
> (conforme instrução literal no schema: *"usar SEMPRE a data_efetiva e NÃO a data_registro"*).

---

## `historico_titularidade[]` — PeriodoTitularidade

| Campo                  | Tipo             | Obrig. | Descrição                                                                                                         |
|------------------------|------------------|--------|-------------------------------------------------------------------------------------------------------------------|
| `id_periodo`           | string \| null   | não    | Identificador interno (ex.: `"P1"`, `"P2"`)                                                                       |
| `proprietarios`        | array\<string\>  | **sim**| Lista de proprietários durante o período                                                                          |
| `registro_inicio`      | string \| null   | não    | Registro que dá origem à titularidade (ex.: `"R.46"`)                                                             |
| `data_inicio`          | string \| null   | não    | Sempre a `data_efetiva` do `registro_inicio` (nunca a `data_registro`)                                            |
| `registro_consolidacao`| string \| null   | não    | Registro que consolida a titularidade                                                                             |
| `data_consolidacao`    | string \| null   | não    | `data_efetiva` do `registro_consolidacao`                                                                         |
| `registro_fim`         | string \| null   | não    | Registro que encerra a titularidade                                                                               |
| `data_fim`             | string \| null   | não    | `data_efetiva` do `registro_fim`                                                                                  |
| `registros_periodo`    | array\<string\> \| null | não | Todos os registros/averbações cuja `data_efetiva` está dentro do período (ordenados por data efetiva)         |
| `descricao_periodo`    | string \| null   | não    | Descrição resumida do período de titularidade                                                                     |
