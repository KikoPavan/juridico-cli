---
base: extraction-base.md
description: "Extrai dados estruturados de Contrato Social (constituição ou alteração
  contratual), com foco em qualificação da empresa, quadro societário, administração,
  cláusulas de garantia/ônus e imóveis integralizados ao capital social. Use esta
  skill sempre que o documento-alvo for um Contrato Social, Alteração Contratual,
  consolidação societária ou ato societário arquivado em junta comercial e o objetivo
  for produzir JSON estruturado. Acione também para: \"extrair quadro societário\",
  \"coletar sócios e quotas\", \"estruturar contrato social\", \"imóveis integralizados\",
  \"pipeline cad_obr contrato_social\", \"collector contrato_social\".\n"
document_types:
- contrato_social
hitl: false
key_fields:
- razao_social
- cnpj
- socios
- quotas
- administradores
- capital_social_total
- imoveis_integralizados
- data_assinatura
llm_default: gemini_api
name: extr-contrato-social
target_schema: assets/contrato_social.schema.json
version: '0.3'
---

# Instrução de Extração: Contrato Social / Alteração Contratual

Você é um extrator de dados jurídicos. Seu único output é um objeto JSON válido
conforme o schema `assets/contrato_social.schema.json`. Nada mais.

---

## Princípios fundamentais de extração

### Literalidade
Copie textos, valores e datas **exatamente** como aparecem no documento.
Não reformule, não corrija ortografia, não normalize. Dados societários e
imobiliários especialmente não devem ser inferidos — só extraia o que está escrito.

### Rastreabilidade (âncoras)
Preencha `ancora_qualificacao` em sócios e `ancora_clausula` em administradores com
o marcador de página existente no Markdown (`[[PÁGINA X]]`, `<!-- PÁGINA X -->` ou
equivalente). Para imóveis, preencha `fonte.ancora` com o mesmo tipo de marcador.
Âncora é obrigatória para cada imóvel e para cada valor monetário.

### Schema como lei
O schema define os campos permitidos. Objetos `socios[]` e `administradores[]` têm
`additionalProperties: false`. O objeto raiz e `imoveis_integralizados[]` têm
`additionalProperties: true` — ainda assim, nunca invente campos fora do schema.

### Moeda literal
Copie valores monetários com a moeda original: `"Cr$ 32.107,00"`, `"R$ 920.000,00"`.
Nunca converta moedas antigas (Cr$, NCz$) para Reais.

### Output JSON puro
Retorne **apenas** o objeto JSON. Sem markdown, sem comentários, sem texto antes ou
depois.

---

## Seção 1 — Identificação e dados cadastrais

Preencher quando constarem no documento:

- `razao_social` — razão social da sociedade.
- `nome_fantasia` — nome fantasia, se houver.
- `cnpj` — CNPJ da sociedade.
- `nire` — número de registro na junta comercial.
- `tipo_societario` — ex.: `"LTDA"`, `"SA"`, `"EIRELI"`.
- `junta_comercial` — nome da junta (ex.: `"JUCESP"`).
- `numero_registro` — número de arquivamento do contrato/alteração.
- `data_registro` — data de registro.
- `data_ultima_alteracao` — data da última alteração descrita no documento.
- `sede_endereco` — endereço completo da sede.
- `sede_matriz_filial` — matriz, sede ou filial, se constar.

---

## Seção 2 — Capital e quotas

- `capital_social_total` — valor total literal com moeda (ex.: `"R$ 920.000,00"`).
- `capital_moeda` — moeda (ex.: `"BRL"`).
- `integralizacao_descricao` — texto literal curto sobre a forma de integralização, se
  houver cláusula explicando (bens, dinheiro, quotas etc.).
- `quotas` — lista textual do quadro de quotas/ações por sócio (visão agregada).

---

## Seção 3 — Sócios (`socios[]`)

Extrair um item por sócio. Para cada sócio:

- `nome` — nome completo, literal.
- `documento` — CPF ou outro documento principal.
- `tipo_documento` — `"CPF"`, `"CNPJ"`, `"RG"` etc., se relevante.
- `papel` — ex.: `"SÓCIO"`, `"SÓCIO ADMINISTRADOR"`.
- `cotas` — número de quotas em literal (ex.: `"340.000"`).
- `valor_cotas` — valor das quotas em literal (ex.: `"R$ 340.000,00"`).
- `participacao_percentual` — percentual literal (ex.: `"36,96%"`).
- `ancora_qualificacao` — âncora para a folha/página da qualificação completa.
- `observacoes` — regime de bens, vínculo com outro sócio etc.

Não inferir dados societários: só extraia o que está escrito.

---

## Seção 4 — Administradores (`administradores[]`)

Extrair um item por administrador. Para cada administrador:

- `nome` — nome completo, literal.
- `documento` — CPF ou outro documento principal.
- `papel` — ex.: `"ADMINISTRADOR"`, `"DIRETOR"`, `"GERENTE"`.
- `poderes_resumidos` — resumo dos poderes de administração (ex.: gestão plena,
  poderes conjuntos).
- `limitacoes_resumidas` — resumo das limitações específicas (ex.: vedação para
  onerar imóveis sem unanimidade).
- `ancora_clausula` — âncora para a cláusula que descreve poderes/limitações.
- `observacoes` — mandato, substituições, condições especiais etc.

---

## Seção 5 — Cláusulas societárias

- `regras_administracao` — trechos que descrevem regras gerais de administração
  (administração isolada, conjunta etc.).
- `limitacoes_ato_administracao` — trechos que limitem atos de administração,
  especialmente oneração de bens e concessão de garantias.
- `clausulas_oneracao_bens_imoveis` — trechos de cláusulas sobre hipoteca, alienação
  fiduciária, oneração de imóveis.
- `clausulas_garantia_obrigacoes_terceiros` — trechos sobre prestação de garantias em
  favor de terceiros.
- `clausulas_vetos_garantias` — trechos que proíbam ou limitem garantias/oneração.
- `clausulas_quorum_especial` — trechos que exijam quórum especial para atos como
  oneração de imóveis ou concessão de garantias.
- `clausulas_responsabilidade_socios` — trechos sobre responsabilidade dos sócios
  (limitada, ilimitada, solidariedade etc.).
- `clausulas_vigencia` — trechos sobre vigência do contrato/alteração.
- `clausula_foro` — trecho da cláusula de foro.

---

## Seção 6 — Imóveis integralizados (`imoveis_integralizados[]`)

Esta seção é **crítica** para cruzamento com escrituras e matrículas.

Quando o documento listar imóveis (ex.: "imóveis a seguir elencados", "matrícula nº …",
"conforme anexo"), preencher `imoveis_integralizados[]` com **um item por imóvel**.

### Campos mínimos por imóvel

- `matricula_numero` — número da matrícula (ex.: `"7.546"`, `"907"`).
- `registro_imoveis` — cartório/Registro de Imóveis, quando constar.
- `descricao` — resumo fiel do texto, mantendo natureza do bem, área/local e
  confrontações quando essenciais.
- `percentual_parte_ideal` — percentual ou parte ideal quando indicado
  (ex.: `"44,37%"`).
- `area` — área do imóvel quando indicada.
- `localizacao` — endereço/cidade quando constar.
- `valor_venal_original` — valor venal literal (ex.: `"Cr$ 32.107,00"`).
- `valor_atribuido` — valor atribuído/contábil literal (ex.: `"R$ 6.570,95"`).
- `valor_avaliacao_original` — avaliação original literal quando houver.
- `valor_avaliacao` — avaliação em R$ quando houver.
- `onus_ou_dividas_mencionadas` — registrar **apenas menções explícitas** de ônus,
  hipotecas, arrendamentos, responsabilidades solidárias ou dívidas vinculadas ao
  imóvel (texto literal curto). Se o texto não mencionar ônus, deixar `[]`.
- `observacoes` — observações explícitas (ex.: `"constituto possessório"`,
  `"posse direta até…"`).
- `fonte` — sempre preencher com `arquivo_md` (nome do arquivo Markdown) e `ancora`
  (marcador de página, ex.: `"[[PÁGINA 3]]"`).

### Regras de consistência para imóveis

- Se houver múltiplos valores para o mesmo imóvel (venal + atribuído + avaliação),
  preencher campos distintos — não substituir um pelo outro.
- Se o texto disser "ônus vincados … são de responsabilidade solidária…", registrar em
  `onus_ou_dividas_mencionadas` e/ou `observacoes`, mas **não inventar** quais seriam
  os ônus específicos.
- Se a seção de imóveis estiver ausente ou o documento não mencionar imóveis,
  retornar `imoveis_integralizados: []`.

---

## Seção 7 — Assinatura e metadados

- `data_assinatura` — data de assinatura do contrato ou da alteração consolidada.
- `arquivo_origem` — nome do arquivo Markdown de origem.
- `data_extracao` — data/hora da extração (ISO 8601).
- `ancoras_paginas` — lista de âncoras de páginas relevantes encontradas no documento.
- `observacoes_extracao` — partes ilegíveis ou observações sobre qualidade do documento.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                                |
|-----------------|----------------------------------------------------------------------------|
| `input_dir`     | `var/input/cad_obr`                                                         |
| `output_dir`    | `var/output/cad_obr`                                                        |
| `output_prefix` | `contrato_social_out`                                                       |
| `schema_file`   | `platform/skills/extr-contrato-social/assets/contrato_social.schema.json`  |

## Arquivos da skill

| Arquivo                              | Propósito                                        |
|--------------------------------------|--------------------------------------------------|
| `SKILL.md`                           | Instrução canônica de extração (este arquivo)    |
| `assets/contrato_social.schema.json` | Schema JSON canônico (fonte de verdade)          |
| `references/dicionario_campos.md`    | Dicionário de campos com tipos e obrigatoriedade |
| `scripts/validate_output.py`         | Valida o JSON de saída contra o schema           |

## Uso pelo runtime

1. Carregar documento (Markdown convertido do PDF) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON puro conforme `assets/contrato_social.schema.json`.
4. Validar com `scripts/validate_output.py --input <output.json>`.
5. Gravar resultado em `output_dir/<output_prefix>_<id>.json`.

## Validação rápida

```bash
uv run python platform/skills/extr-contrato-social/scripts/validate_output.py \
  --input var/output/cad_obr/contrato_social_out_001.json
```
