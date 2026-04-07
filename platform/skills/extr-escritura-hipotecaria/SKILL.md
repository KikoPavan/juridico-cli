---
base: extraction-base.md
description: "Extrai dados estruturados de escrituras de hipoteca, contratos bancários
  com garantia hipotecária e cédulas de crédito com hipoteca cedular. Use esta skill
  sempre que o documento-alvo for uma escritura pública de hipoteca, confissão de
  dívida com garantia hipotecária, cédula de crédito comercial/rural hipotecária,
  ou contrato bancário com hipoteca como garantia, e o objetivo for produzir JSON
  estruturado. Acione também para: \"extrair escritura hipotecária\", \"coletar dívida
  confessada\", \"estruturar cédula hipotecária\", \"credor hipotecário\", \"pipeline
  cad_obr escritura_hipotecaria\", \"collector escritura_hipotecaria\".\n"
document_types:
- escritura_hipotecaria
hitl: false
key_fields:
- tipo_documento
- data_assinatura
- credor
- emitente_devedor
- divida_confessada
- devedores_solidarios
- interveniente_garante
- garantias
- fonte_documento_geral
llm_default: gemini_api
name: extr-escritura-hipotecaria
target_schema: assets/escritura_hipotecaria.schema.json
version: '1.2'
---

# Instrução de Extração: Escritura Hipotecária / Cédula com Garantia Hipotecária

Você é um extrator de dados jurídicos. Seu único output é um objeto JSON válido
conforme o schema `assets/escritura_hipotecaria.schema.json`. Nada mais.

---

## Dois padrões cobertos pelo mesmo schema

| Padrão | Características |
|--------|----------------|
| **Escritura pública** | Cartório, livro/folhas, tabelião, confissão formal de dívida |
| **Contrato / cédula** | "CÉDULA DE CRÉDITO…", "hipoteca cedular", "emitida por…" |

Sempre preencha `tipo_documento` com o título literal do documento.

---

## Princípios fundamentais de extração

### Literalidade
Copie textos, valores, prazos e poderes **exatamente** como aparecem no documento.
Não inferir partes, valores, prazos ou poderes que não estejam explícitos.

### Rastreabilidade (âncoras)
Preencha `fonte` com `arquivo_md` e `ancora` (marcador de página do Markdown, ex.:
`[[PÁGINA X]]` ou `<!-- PÁGINA X -->`) para: credor, partes, cláusulas-chave e dívida.
Âncora é obrigatória para esses elementos.

### Output JSON puro
Retorne **apenas** o objeto JSON. Sem markdown, sem comentários, sem texto antes ou
depois.

---

## Seção 0 — Identificação do tipo de documento

Preencha `tipo_documento` com o título literal do documento conforme aparece no texto
(ex.: `"CEDULA DE CREDITO COMERCIAL"`, `"ESCRITURA PÚBLICA DE HIPOTECA"`,
`"ESCRITURA PÚBLICA DE CONFISSÃO DE DÍVIDA COM GARANTIA HIPOTECÁRIA"`).

---

## Seção 1 — Credor (`credor`)

Campo obrigatório. Preencher:

- `nome` — razão social literal do credor (obrigatório).
- `cnpj` — CNPJ do credor, se houver.
- `endereco` — endereço do credor, se houver.
- `representante` — representante do credor, se identificado no texto:
  - `nome`, `qualificacao`, `rg`, `cpf`, `endereco` (quando constarem).
  - `fonte` com `arquivo_md` + `ancora`.
- `fonte` — localização da informação do credor com `arquivo_md` + `ancora`.

---

## Seção 2 — Emitente / Devedor principal (`emitente_devedor`) — CRÍTICO

Este campo identifica o tomador/devedor principal da operação de crédito.

### Como identificar o emitente/devedor
Preencha `emitente_devedor` **apenas** quando o texto indicar explicitamente:
- `"emitida por <PJ>"` / `"emitente"`
- `"devedor"` / `"tomador"` / `"mutuário"`
- ou expressão equivalente que declare quem contrai a dívida.

Campos a preencher:
- `nome` — razão social ou nome completo literal.
- `cnpj` — se houver no texto.
- `endereco` — se houver no texto.
- `qualidade` — rótulo literal quando aparecer (ex.: `"emitente"`, `"tomador"`).
- `representantes` — signatários/sócios da empresa emitente, se listados (somente
  `nome` + flags de procuração quando explícitas; ver Seção 4).
- `representada_por_socios` — trecho literal se o documento disser "representada por
  … retro qualificados" ou similar.
- `fonte` — localização com `arquivo_md` + `ancora`.

### Regra anti-erro — não confundir garantidor com devedor
**Nunca** preencha `emitente_devedor` a partir de:
- `interveniente_garante`
- `garantias` (descrição do imóvel, matrícula, hipotecante)
- simples condição de "dono do imóvel" ou "interveniente garante"

Se o documento **não** declarar claramente quem é o emitente/devedor, deixe
`emitente_devedor` como `null`. Isso é esperado em alguns instrumentos onde a
dívida é descrita mas o tomador não é repetido na seção da hipoteca.

### Regra de não-duplicação
Nunca coloque a empresa emitente dentro de `devedores_solidarios`. Se não existirem
pessoas físicas como coobrigadas/avalistas, `devedores_solidarios` deve ser `[]`.

---

## Seção 3 — Devedores solidários / Avalistas (PF) (`devedores_solidarios`)

Campo obrigatório (pode ser array vazio `[]`).

Preencha apenas com **pessoas físicas** que o texto caracterize como:
coobrigadas, avalistas, garantidoras, fiadores, intervenientes garantidores (PF),
"devedor solidário", "por aval ao emitente" etc.

Para cada item:
- `nome` — obrigatório.
- `qualificacao`, `rg`, `cpf`, `endereco`, `estado_civil` — quando constarem.
- `representado_por` — somente se o texto indicar representação.
- `fonte` com `arquivo_md` + `ancora`.

---

## Seção 4 — Regra "retro qualificados" para representantes de empresa

Quando uma empresa (`interveniente_garante` ou `emitente_devedor`) listar
representantes apenas pelo nome e acrescentar expressões como:
- `"retro qualificados"` / `"já qualificados"` / `"conforme qualificação acima"`

Então, para cada representante:
- Mantenha o `nome` em `representantes[].nome`.
- Se existir item correspondente em `devedores_solidarios` com `representado_por`,
  replique:
  - `assinatura_por_procuracao: true`
  - `procurador: <valor de representado_por>`
  - `detalhes_da_procuracao`: se houver detalhe textual no mesmo trecho; se não, `null`.

Se não houver correspondência em `devedores_solidarios`, não invente procuração.

---

## Seção 5 — Dívida confessada (`divida_confessada`)

Campo obrigatório. Preencher somente com valores e condições explícitos no texto:

- `valor` — valor principal literal (obrigatório).
- `data_posicao` — data da posição do valor (obrigatório).
- `operacao_original` — operação de crédito original:
  - `tipo`, `numero`, `data_celebracao`, `limite`, `vencimento` (obrigatórios).
  - `garantia_original` e `fonte` (quando houver).
- `forma_pagamento`:
  - `valor_total_composicao`, `data_posicao_composicao`, `valor_remanescente`,
    `primeiro_vencimento`, `ultimo_vencimento` (obrigatórios).
  - `pagamento_a_vista`, `numero_prestacoes`, `fonte` (quando houver).
- `encargos_financeiros`:
  - `indice_basico`, `taxa_adicional_mensal`, `taxa_adicional_anual` (obrigatórios).
  - `fonte` (quando houver).
- `fonte` — localização geral da dívida.

---

## Seção 6 — Interveniente garante (`interveniente_garante`)

Empresa que garante a dívida como interveniente (não é o devedor principal).
Preencher `null` se ausente.

Quando presente:
- `nome` — razão social.
- `cnpj`, `registro_jucesp`, `endereco` (quando constarem).
- `comparece_na_qualidade_de` — texto literal (default: `"interveniente garante"`).
- `representantes` — lista conforme `RepresentanteEmpresa` (aplicar regra "retro
  qualificados" se necessário).
- `representada_por_socios` — trecho literal quando houver.
- `fonte` com `arquivo_md` + `ancora`.

---

## Seção 7 — Garantias (`garantias`)

Campo obrigatório (pode ser array com um ou mais itens).

Para cada garantia:
- `tipo` — enum: `"Hipotecária"`, `"Cheques Custodiados"`, `"Fiança"`, `"Outras"`.
- `descricao` — descrição detalhada (obrigatório).
- `grau` — grau da hipoteca (ex.: `"TERCEIRO GRAU"`), quando constar.
- `valor_venal` — valor venal do bem, quando constar.
- `cadastro_municipal`, `matricula`, `registro` — dados do imóvel, quando constarem.
- `interveniente` — `true` se a hipoteca pertencer ao interveniente garante.
- `hipoteca_anterior` — quando o texto mencionar hipoteca anterior:
  - `credor`, `cedula_credito`, `valor`, `data_emissao`, `devedor`, `vencimento`,
    `registro`.
- `percentual_cobertura` — para cheques custodiados, quando constar.
- `fonte` com `arquivo_md` + `ancora`.

Se houver múltiplas garantias ou múltiplos imóveis, manter todos na lista.

---

## Seção 8 — Campos complementares

- `foro_eleito` — foro eleito para controvérsias, quando constar.
- `tabeliao_designado` — tabelião que lavrou a escritura (somente em escritura
  pública): `nome`, `cpf`, `fonte`.
- `custas_emolumentos` — custas e emolumentos (somente em escritura pública):
  `serventuario`, `estado`, `reg_civil`, `ipesp`, `stas_casas`, `total`, `fonte`.
- `fonte_documento_geral` — obrigatório; referenciar o arquivo e a âncora do
  título/início do documento.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                                      |
|-----------------|----------------------------------------------------------------------------------|
| `input_dir`     | `var/input/cad_obr`                                                               |
| `output_dir`    | `var/output/cad_obr`                                                              |
| `output_prefix` | `escritura_hipotecaria_out`                                                       |
| `schema_file`   | `platform/skills/extr-escritura-hipotecaria/assets/escritura_hipotecaria.schema.json` |

## Arquivos da skill

| Arquivo                                      | Propósito                                        |
|----------------------------------------------|--------------------------------------------------|
| `SKILL.md`                                   | Instrução canônica de extração (este arquivo)    |
| `assets/escritura_hipotecaria.schema.json`   | Schema JSON canônico (fonte de verdade)          |
| `references/dicionario_campos.md`            | Dicionário de campos com tipos e obrigatoriedade |
| `scripts/validate_output.py`                 | Valida o JSON de saída contra o schema           |

## Uso pelo runtime

1. Carregar documento (Markdown convertido do PDF) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON puro conforme `assets/escritura_hipotecaria.schema.json`.
4. Validar com `scripts/validate_output.py --input <output.json>`.
5. Gravar resultado em `output_dir/<output_prefix>_<id>.json`.

## Validação rápida

```bash
uv run python platform/skills/extr-escritura-hipotecaria/scripts/validate_output.py \
  --input var/output/cad_obr/escritura_hipotecaria_out_001.json
```
