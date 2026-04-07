# Dicionário de Campos — escritura_hipotecaria.schema.json

Derivado de `assets/escritura_hipotecaria.schema.json`.
Legenda: **Obrig.** = obrigatório; **Tipo** inclui `null` quando permitido.

---

## Tipos compartilhados (`$defs`)

### Fonte
Estrutura reutilizada em todos os campos de rastreabilidade.

| Campo            | Tipo            | Obrig. | Descrição                                               |
|------------------|-----------------|--------|---------------------------------------------------------|
| `arquivo_md`     | string          | **sim**| Nome do arquivo Markdown de origem                      |
| `fls`            | string \| null  | não    | Número ou intervalo de folhas dos autos                 |
| `rotulo_documento`| string \| null | não    | Identificação amigável do documento                     |
| `ancora`         | string \| null  | não    | Âncora de página no Markdown (ex.: `[[PÁGINA 2]]`)      |

### RepresentanteEmpresa
Usado em `emitente_devedor.representantes[]` e `interveniente_garante.representantes[]`.

| Campo                     | Tipo                   | Obrig. | Descrição                                                  |
|---------------------------|------------------------|--------|------------------------------------------------------------|
| `nome`                    | string                 | **sim**| Nome completo do representante/sócio                       |
| `assinatura_por_procuracao`| boolean               | **sim**| Se este representante assina por procuração                |
| `procurador`              | string \| boolean      | não    | Nome do procurador ou `false` se não houver                |
| `detalhes_da_procuracao`  | string \| null         | não    | Detalhes da procuração, se houver                          |

---

## Objeto raiz — campos obrigatórios

| Campo                  | Tipo   | Obrig. | Descrição                                                                               |
|------------------------|--------|--------|-----------------------------------------------------------------------------------------|
| `tipo_documento`       | string | **sim**| Título literal do documento (ex.: `"CEDULA DE CREDITO COMERCIAL"`)                      |
| `data_assinatura`      | string | **sim**| Data de assinatura/lavratura da escritura                                               |
| `credor`               | object | **sim**| Credor (instituição financeira); ver tabela abaixo                                      |
| `divida_confessada`    | object | **sim**| Detalhes da dívida confessada; ver tabela abaixo                                        |
| `devedores_solidarios` | array  | **sim**| Devedores solidários PF (pode ser `[]`)                                                 |
| `garantias`            | array  | **sim**| Garantias oferecidas (pode ser array com um ou mais itens)                              |
| `fonte_documento_geral`| Fonte \| null | **sim** | Localização geral do documento (arquivo + âncora do título)                    |

---

## `credor` — Credor

| Campo          | Tipo            | Obrig. | Descrição                                           |
|----------------|-----------------|--------|-----------------------------------------------------|
| `nome`         | string          | **sim**| Razão social do credor                              |
| `cnpj`         | string \| null  | não    | CNPJ do credor                                      |
| `endereco`     | string \| null  | não    | Endereço do credor                                  |
| `representante`| object \| null  | não    | Representante do credor (nome, qualificacao, rg, cpf, endereco, fonte) |
| `fonte`        | Fonte \| null   | não    | Localização da informação do credor                 |

---

## `emitente_devedor` — Devedor principal / Emitente

`null` quando o documento não declara explicitamente o emitente/devedor.

| Campo                    | Tipo            | Obrig. | Descrição                                                                           |
|--------------------------|-----------------|--------|-------------------------------------------------------------------------------------|
| `nome`                   | string \| null  | não    | Nome/Razão social do emitente/devedor                                               |
| `cnpj`                   | string \| null  | não    | CNPJ do emitente/devedor                                                            |
| `endereco`               | string \| null  | não    | Endereço do emitente/devedor                                                        |
| `qualidade`              | string \| null  | não    | Rótulo textual (ex.: `"emitente"`, `"tomador"`)                                     |
| `representantes`         | array           | não    | Representantes da empresa emitente (RepresentanteEmpresa)                           |
| `representada_por_socios`| string \| null  | não    | Trecho literal de "retro qualificados" ou similar                                   |
| `fonte`                  | Fonte           | não    | Localização da informação                                                           |

> **Regra crítica:** nunca preencher a partir de `interveniente_garante`, `garantias`
> (matrícula/hipotecante) ou simples condição de "dono do imóvel". Ver agente.

---

## `devedores_solidarios[]` — Devedor Solidário (PF)

Apenas pessoas físicas. `devedores_solidarios: []` quando não há coobrigados PF.

| Campo            | Tipo            | Obrig. | Descrição                                    |
|------------------|-----------------|--------|----------------------------------------------|
| `nome`           | string          | **sim**| Nome completo do devedor solidário           |
| `qualificacao`   | string \| null  | não    | Qualificação completa                        |
| `rg`             | string \| null  | não    | Documento de identidade                      |
| `cpf`            | string \| null  | não    | CPF                                          |
| `endereco`       | string \| null  | não    | Endereço completo                            |
| `estado_civil`   | string \| null  | não    | Estado civil                                 |
| `representado_por`| string \| null | não    | Nome do representante legal                  |
| `fonte`          | Fonte \| null   | não    | Localização da informação                    |

---

## `interveniente_garante` — Interveniente Garante (PJ)

`null` quando ausente.

| Campo                    | Tipo            | Obrig. | Descrição                                                    |
|--------------------------|-----------------|--------|--------------------------------------------------------------|
| `nome`                   | string          | não    | Razão social da empresa garantidora                          |
| `cnpj`                   | string \| null  | não    | CNPJ da empresa                                              |
| `registro_jucesp`        | string \| null  | não    | Registro na Junta Comercial                                  |
| `endereco`               | string \| null  | não    | Endereço da empresa                                          |
| `comparece_na_qualidade_de`| string \| null| não    | Qualidade em que comparece (default: `"interveniente garante"`) |
| `representantes`         | array           | não    | Representantes/sócios signatários (RepresentanteEmpresa)     |
| `representada_por_socios`| string \| null  | não    | Trecho literal de "retro qualificados" ou similar            |
| `fonte`                  | Fonte \| null   | não    | Localização da informação                                    |

---

## `divida_confessada` — Dívida Confessada

| Campo                | Tipo   | Obrig. | Descrição                                    |
|----------------------|--------|--------|----------------------------------------------|
| `valor`              | string | **sim**| Valor da dívida confessada (literal)         |
| `data_posicao`       | string | **sim**| Data da posição do valor                     |
| `operacao_original`  | object | **sim**| Operação de crédito original; ver abaixo     |
| `forma_pagamento`    | object | **sim**| Forma de pagamento; ver abaixo               |
| `encargos_financeiros`| object | **sim**| Encargos financeiros; ver abaixo            |
| `fonte`              | Fonte \| null | não | Localização geral da dívida               |

### `divida_confessada.operacao_original`

| Campo              | Tipo            | Obrig. | Descrição                              |
|--------------------|-----------------|--------|----------------------------------------|
| `tipo`             | string          | **sim**| Tipo da operação                       |
| `numero`           | string          | **sim**| Número do contrato/operação            |
| `data_celebracao`  | string          | **sim**| Data de celebração do contrato original|
| `limite`           | string          | **sim**| Limite de crédito estabelecido         |
| `vencimento`       | string          | **sim**| Data de vencimento original            |
| `garantia_original`| string \| null  | não    | Garantia original da operação          |
| `fonte`            | Fonte \| null   | não    | Localização da informação              |

### `divida_confessada.forma_pagamento`

| Campo                    | Tipo            | Obrig. | Descrição                              |
|--------------------------|-----------------|--------|----------------------------------------|
| `valor_total_composicao` | string          | **sim**| Valor total da composição              |
| `data_posicao_composicao`| string          | **sim**| Data da posição da composição          |
| `pagamento_a_vista`      | string \| null  | não    | Valor do pagamento à vista             |
| `valor_remanescente`     | string          | **sim**| Valor remanescente a pagar             |
| `numero_prestacoes`      | string \| null  | não    | Número de prestações                   |
| `primeiro_vencimento`    | string          | **sim**| Data do primeiro vencimento            |
| `ultimo_vencimento`      | string          | **sim**| Data do último vencimento              |
| `fonte`                  | Fonte \| null   | não    | Localização da informação              |

### `divida_confessada.encargos_financeiros`

| Campo                   | Tipo            | Obrig. | Descrição                    |
|-------------------------|-----------------|--------|------------------------------|
| `indice_basico`         | string          | **sim**| Índice básico de correção    |
| `taxa_adicional_mensal` | string          | **sim**| Taxa adicional mensal        |
| `taxa_adicional_anual`  | string          | **sim**| Taxa adicional anual         |
| `fonte`                 | Fonte \| null   | não    | Localização da informação    |

---

## `garantias[]` — Garantia

| Campo                | Tipo            | Obrig. | Descrição                                                                        |
|----------------------|-----------------|--------|----------------------------------------------------------------------------------|
| `tipo`               | string (enum)   | **sim**| `"Hipotecária"` \| `"Cheques Custodiados"` \| `"Fiança"` \| `"Outras"`           |
| `descricao`          | string          | **sim**| Descrição detalhada da garantia                                                  |
| `grau`               | string \| null  | não    | Grau da hipoteca (ex.: `"TERCEIRO GRAU"`)                                        |
| `valor_venal`        | string \| null  | não    | Valor venal do bem dado em garantia                                              |
| `cadastro_municipal` | string \| null  | não    | Cadastro municipal do imóvel                                                     |
| `matricula`          | string \| null  | não    | Número da matrícula do imóvel                                                    |
| `registro`           | string \| null  | não    | Registro no cartório de imóveis                                                  |
| `interveniente`      | boolean \| null | não    | `true` se a hipoteca pertence ao interveniente garante                           |
| `hipoteca_anterior`  | object \| null  | não    | Hipoteca anterior: `credor`, `cedula_credito`, `valor`, `data_emissao`, `devedor`, `vencimento`, `registro` |
| `percentual_cobertura`| string \| null | não    | Percentual de cobertura (para cheques custodiados)                               |
| `fonte`              | Fonte \| null   | não    | Localização da informação da garantia                                            |

---

## Objeto raiz — campos complementares

| Campo                  | Tipo            | Obrig. | Descrição                                                            |
|------------------------|-----------------|--------|----------------------------------------------------------------------|
| `foro_eleito`          | string \| null  | não    | Foro eleito para dirimir controvérsias                               |
| `tabeliao_designado`   | object \| null  | não    | Tabelião que lavrou a escritura: `nome`, `cpf`, `fonte`              |
| `custas_emolumentos`   | object \| null  | não    | Custas/emolumentos (escritura pública): `serventuario`, `estado`, `reg_civil`, `ipesp`, `stas_casas`, `total`, `fonte` |
