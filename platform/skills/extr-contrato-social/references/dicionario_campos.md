# Dicionário de Campos — contrato_social.schema.json

Derivado de `assets/contrato_social.schema.json`.
Legenda: **Obrig.** = obrigatório dentro do objeto pai; **Tipo** inclui `null` quando permitido.
O objeto raiz e `imoveis_integralizados[]` têm `additionalProperties: true`.
Os objetos `socios[]` e `administradores[]` têm `additionalProperties: false`.

---

## Objeto raiz — metadados de extração

| Campo                  | Tipo            | Obrig. | Descrição                                                        |
|------------------------|-----------------|--------|------------------------------------------------------------------|
| `id_documento`         | string \| null  | não    | Identificador interno único do documento estruturado             |
| `tipo_documento`       | string \| null  | não    | Tipo lógico (ex.: `"CONTRATO_SOCIAL"`, `"ALTERACAO_CONTRATUAL"`) |
| `arquivo_origem`       | string \| null  | não    | Nome do arquivo Markdown de origem                               |
| `hash_origem`          | string \| null  | não    | Hash SHA256 do arquivo original para cadeia de custódia          |
| `data_extracao`        | string \| null  | não    | Data/hora da extração (ISO 8601 se possível)                     |
| `ancoras_paginas`      | array \| null   | não    | Âncoras de páginas relevantes (ex.: `"[[Folha 3]]"`)             |
| `fonte_sistema`        | string \| null  | não    | Sistema que gerou o Markdown (ex.: `"pdf_legal_br"`)             |
| `observacoes_extracao` | string \| null  | não    | Observações sobre partes ilegíveis ou qualidade da extração      |

---

## Objeto raiz — dados da empresa

| Campo                    | Tipo            | Obrig. | Descrição                                                              |
|--------------------------|-----------------|--------|------------------------------------------------------------------------|
| `razao_social`           | string \| null  | não    | Razão social da sociedade                                              |
| `nome_fantasia`          | string \| null  | não    | Nome fantasia, se houver                                               |
| `cnpj`                   | string \| null  | não    | CNPJ da sociedade                                                      |
| `nire`                   | string \| null  | não    | Número de registro na junta comercial                                  |
| `tipo_societario`        | string \| null  | não    | Tipo societário (ex.: `"LTDA"`, `"SA"`, `"EIRELI"`)                    |
| `junta_comercial`        | string \| null  | não    | Nome da junta (ex.: `"JUCESP"`)                                        |
| `numero_registro`        | string \| null  | não    | Número de registro/arquivamento do contrato/alteração                  |
| `data_registro`          | string \| null  | não    | Data de registro do contrato/alteração                                 |
| `data_ultima_alteracao`  | string \| null  | não    | Data da última alteração contratual descrita                           |
| `sede_endereco`          | string \| null  | não    | Endereço completo da sede                                              |
| `sede_matriz_filial`     | string \| null  | não    | Indicação de matriz, sede ou filial                                    |
| `objeto_social`          | string \| null  | não    | Objeto social principal (texto; itens podem ser separados por `;`)     |

---

## Objeto raiz — capital e quotas

| Campo                      | Tipo            | Obrig. | Descrição                                                                              |
|----------------------------|-----------------|--------|----------------------------------------------------------------------------------------|
| `capital_social_total`     | string \| null  | não    | Valor total literal com moeda (ex.: `"R$ 920.000,00"`)                                 |
| `capital_moeda`            | string \| null  | não    | Moeda do capital (ex.: `"BRL"`)                                                        |
| `integralizacao_descricao` | string \| null  | não    | Texto literal curto sobre forma de integralização (bens, dinheiro, quotas etc.)        |
| `quotas`                   | array \| null   | não    | Lista textual do quadro de quotas/ações por sócio (visão agregada)                     |

---

## `socios[]` — Sócio (additionalProperties: false)

| Campo                    | Tipo            | Obrig. | Descrição                                                                |
|--------------------------|-----------------|--------|--------------------------------------------------------------------------|
| `nome`                   | string \| null  | não    | Nome completo do sócio                                                   |
| `documento`              | string \| null  | não    | CPF ou outro documento principal                                         |
| `tipo_documento`         | string \| null  | não    | Tipo de documento (`"CPF"`, `"CNPJ"`, `"RG"` etc.)                       |
| `papel`                  | string \| null  | não    | Papel (ex.: `"SÓCIO"`, `"SÓCIO ADMINISTRADOR"`)                          |
| `cotas`                  | string \| null  | não    | Número de quotas em literal (ex.: `"340.000"`)                           |
| `valor_cotas`            | string \| null  | não    | Valor das quotas em literal (ex.: `"R$ 340.000,00"`)                     |
| `participacao_percentual`| string \| null  | não    | Percentual literal (ex.: `"36,96%"`)                                     |
| `ancora_qualificacao`    | string \| null  | não    | Âncora para a folha/página da qualificação completa (ex.: `"[[Folha 2]]"`) |
| `observacoes`            | string \| null  | não    | Regime de bens, vínculo com outro sócio etc.                             |

---

## `administradores[]` — Administrador (additionalProperties: false)

| Campo                   | Tipo            | Obrig. | Descrição                                                                   |
|-------------------------|-----------------|--------|-----------------------------------------------------------------------------|
| `nome`                  | string \| null  | não    | Nome completo do administrador                                              |
| `documento`             | string \| null  | não    | CPF ou outro documento principal                                            |
| `papel`                 | string \| null  | não    | Papel/cargo (ex.: `"ADMINISTRADOR"`, `"DIRETOR"`, `"GERENTE"`)              |
| `poderes_resumidos`     | string \| null  | não    | Resumo dos poderes (ex.: gestão plena, poderes conjuntos)                   |
| `limitacoes_resumidas`  | string \| null  | não    | Resumo das limitações (ex.: vedação para onerar imóveis sem unanimidade)    |
| `ancora_clausula`       | string \| null  | não    | Âncora para a cláusula de poderes/limitações (ex.: `"[[Folha 5]]"`)         |
| `observacoes`           | string \| null  | não    | Mandato, substituições, condições especiais etc.                            |

---

## Objeto raiz — cláusulas societárias

| Campo                                   | Tipo            | Obrig. | Descrição                                                                                   |
|-----------------------------------------|-----------------|--------|---------------------------------------------------------------------------------------------|
| `regras_administracao`                  | string \| null  | não    | Regras gerais de administração (administração isolada, conjunta etc.)                       |
| `limitacoes_ato_administracao`          | string \| null  | não    | Limitações a atos de administração; oneração de bens e concessão de garantias               |
| `clausulas_oneracao_bens_imoveis`       | array \| null   | não    | Trechos sobre hipoteca, alienação fiduciária e oneração de imóveis                          |
| `clausulas_garantia_obrigacoes_terceiros`| array \| null  | não    | Trechos sobre prestação de garantias em favor de terceiros                                  |
| `clausulas_vetos_garantias`             | array \| null   | não    | Trechos que proíbam ou limitem garantias/oneração                                           |
| `clausulas_quorum_especial`             | array \| null   | não    | Trechos com quórum especial (ex.: oneração de imóveis, garantias)                           |
| `clausulas_responsabilidade_socios`     | string \| null  | não    | Trechos sobre responsabilidade dos sócios (limitada, ilimitada, solidariedade)              |
| `clausulas_vigencia`                    | string \| null  | não    | Trechos sobre vigência do contrato/alteração                                                |
| `clausula_foro`                         | string \| null  | não    | Trecho da cláusula de foro                                                                  |
| `data_assinatura`                       | string \| null  | não    | Data de assinatura do contrato ou da alteração consolidada                                  |

---

## `imoveis_integralizados[]` — Imóvel Integralizado (additionalProperties: true)

| Campo                         | Tipo            | Obrig. | Descrição                                                                                    |
|-------------------------------|-----------------|--------|----------------------------------------------------------------------------------------------|
| `matricula_numero`            | string \| null  | não    | Número da matrícula do imóvel (ex.: `"7.546"`)                                               |
| `registro_imoveis`            | string \| null  | não    | Cartório/Registro de Imóveis, quando constar                                                 |
| `descricao`                   | string \| null  | não    | Resumo fiel do texto, mantendo natureza, área/local e confrontações essenciais               |
| `percentual_parte_ideal`      | string \| null  | não    | Percentual/parte ideal quando indicado (ex.: `"44,37%"`)                                     |
| `area`                        | string \| null  | não    | Área do imóvel quando indicada                                                               |
| `localizacao`                 | string \| null  | não    | Endereço/cidade quando constar                                                               |
| `valor_venal_original`        | string \| null  | não    | Valor venal literal com moeda original (ex.: `"Cr$ 32.107,00"`)                              |
| `valor_atribuido`             | string \| null  | não    | Valor atribuído/contábil literal (ex.: `"R$ 6.570,95"`)                                      |
| `valor_avaliacao_original`    | string \| null  | não    | Avaliação original literal quando houver                                                     |
| `valor_avaliacao`             | string \| null  | não    | Avaliação em R$ quando houver                                                                |
| `onus_ou_dividas_mencionadas` | array\<string\> | não    | Menções explícitas de ônus, hipotecas, arrendamentos ou dívidas (literal curto); default `[]`|
| `observacoes`                 | string \| null  | não    | Observações explícitas (ex.: `"constituto possessório"`)                                     |
| `fonte`                       | object          | não    | Origem no documento para rastreabilidade                                                     |
| `fonte.arquivo_md`            | string \| null  | não    | Nome do arquivo Markdown de origem                                                           |
| `fonte.ancora`                | string \| null  | não    | Âncora de página (ex.: `"[[PÁGINA 3]]"`)                                                     |

> **Nota âncoras:** âncora é obrigatória por instrução para cada imóvel e para cada
> valor monetário, mesmo que o campo `fonte` não marque como `required` no schema.
