---
name: escritura_hipotecaria
agent: collector-cad-obr
description: |
  Extrai dados estruturados de instrumentos de hipoteca (escritura pública) e de
  contratos bancários/cédulas com garantia hipotecária (hipoteca cedular).
  Regras críticas:
  - Identificar e preencher o DEVEDOR PRINCIPAL/EMITENTE (PJ ou PF) em `emitente_devedor`
    quando o texto trouxer "emitida por", "emitente", "devedor", "tomador" etc.
  - Quando uma empresa listar representantes apenas pelo nome e disser "retro qualificados",
    reutilizar a qualificação/representação já extraída em outras seções (ex.: `devedores_solidarios`).
version: 1.2
target_schema: schemas/escritura_hipotecaria.schema.json
document_types:
  - escritura_hipotecaria
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
required_anchors: true
validation_rules:
  - "Literalidade: não inferir partes, valores, prazos ou poderes."
  - "Fonte obrigatória (arquivo_md + ancora) para partes e cláusulas-chave."
---

# SKILL: Hipoteca (Escritura / Contrato Bancário / Cédula)

## 0) Identificação do tipo dentro do mesmo schema
Este schema cobre dois padrões comuns:
1) **Escritura pública de hipoteca/confissão de dívida** (cartório, livro/folhas, tabelião etc.)
2) **Contrato bancário / cédula** com **garantia hipotecária** (ex.: "CEDULA DE CREDITO ...", "hipoteca cedular", "emitida por ...")

Sempre preencha `tipo_documento` com o título literal do documento (ex.: "CEDULA DE CREDITO COMERCIAL", "ESCRITURA PÚBLICA DE HIPOTECA").

## 1) Credor
Preencher `credor` com:
- nome (e demais dados se existirem: CNPJ/endereço)
- `fonte` com `arquivo_md` e `ancora` (use o marcador de página que existir no .md, por exemplo `[[PÁGINA X]]` ou `<!-- PÁGINA X -->`)

## 2) Emitente / Devedor principal (CRÍTICO)
Preencher `emitente_devedor` quando o texto indicar explicitamente:
- "emitida por <PJ>"
- "emitente"
- "devedor"
- "tomador"

### 2.1) Como extrair
- `nome`: razão social ou nome completo literal.
- `cnpj`: se houver no texto.
- `endereco`: se houver no texto.
- `qualidade`: usar o rótulo literal quando aparecer (ex.: "emitente").
- `representantes`: se o documento listar signatários/sócios pela empresa emitente, incluir em `representantes`
  (somente nome + flags de procuração quando explícitas).
- `representada_por_socios`: se houver trecho do tipo "representada por ... retro qualificados", copiar literal.


### 2.2) Regra anti-erro (NÃO confundir garantidor/proprietário com devedor)
- **NUNCA** preencher `emitente_devedor` a partir de `interveniente_garante`, `garantias` (descrição do imóvel/matrícula),
  ou da simples condição de “dono do imóvel/hipotecante/interveniente garante”.
- Se o documento **não** declarar claramente quem é o emitente/devedor (não houver “emitente”, “devedor”, “tomador”,
  “mutuário”, “emitida por ...” ou equivalente), então `emitente_devedor` deve ser **null**.
  Isso é esperado em alguns instrumentos/escrituras onde a dívida é descrita, mas o tomador/emitente não é repetido no trecho da hipoteca.
- O objetivo é permitir que o reconciler cruze este documento com o contrato bancário/cédula que efetivamente identifica o emitente.

Regra: **não duplicar a empresa emitente dentro de `devedores_solidarios`**. Se não existirem PFs como coobrigados/avalistas, `devedores_solidarios` deve ser `[]`.

## 3) Devedores solidários / Avalistas / Garantidores (PF)
Preencher `devedores_solidarios` apenas com pessoas físicas que o texto caracterize como coobrigadas/avalistas/garantidoras
(ex.: "devedor solidário", "por aval ao emitente", "fiador", "garantidor", "interveniente garantidor (PF)", etc).

Para cada item:
- `nome`, `qualificacao`, `rg`, `cpf`, `endereco`, `estado_civil` (quando constarem)
- `representado_por`: somente se o texto indicar representação (ex.: "representado por ...")
- `fonte` com `arquivo_md` + `ancora`

## 4) Regra de representação “retro qualificados” (empresa)
Quando a empresa (`interveniente_garante` ou `emitente_devedor`) listar representantes apenas por nome e disser algo como:
- "retro qualificados"
- "já qualificados"
- "conforme qualificação acima"

Então:
- mantenha o nome em `representantes[].nome`
- e, se existir um item correspondente em `devedores_solidarios` com `representado_por`, replique:
  - `assinatura_por_procuracao: true`
  - `procurador: <representado_por>`
  - `detalhes_da_procuracao`: se houver detalhe textual no mesmo trecho; se não, `null`

Se não houver correspondência, não inventar procuração.

## 5) Dívida confessada
Preencher `divida_confessada` com:
- valor principal (literal)
- vencimento/prazo/parcelas/juros/correção (somente se explícitos)
- `fonte` com `arquivo_md` + `ancora`

## 6) Garantias
Preencher `garantias` (hipoteca cedular / descrição do imóvel / matrícula / cartório / grau / registros), quando constar.
Atenção: se houver múltiplas garantias ou múltiplos imóveis, manter a lista.

## 7) Fonte geral
`fonte_documento_geral` deve referenciar o arquivo e a âncora do título/início do documento.
