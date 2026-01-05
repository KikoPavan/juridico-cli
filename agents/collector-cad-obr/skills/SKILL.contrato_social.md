---
name: contrato_social
agent: collector-cad-obr
description: |
  Extrai dados estruturados de Contrato Social (constituição/alteração) com foco em:
  - qualificação da empresa (razão social, CNPJ, NIRE, registro)
  - quadro societário (sócios, quotas, integralização)
  - administração (administradores, poderes, limitações)
  - cláusulas sobre garantias/ônus/oneração de bens
  - imóveis integralizados/incorporados ao capital social para cruzamento com escrituras (matrícula, valores, ônus/dívidas)
version: 0.3
target_schema: schemas/contrato_social.schema.json
document_types:
  - contrato_social
key_fields:
  - razao_social
  - cnpj
  - socios
  - quotas
  - administradores
  - capital_social_total
  - imoveis_integralizados
  - data_assinatura
required_anchors: true
validation_rules:
  - "Literalidade: não inferir dados societários ou imobiliários."
  - "Fonte/âncora obrigatória para cada imóvel e para cada valor (Cr$/R$)."
---

# SKILL: Contrato Social (com imóveis integralizados)

## 1) Identificação e dados cadastrais
Preencher, quando constarem:
- `razao_social`, `nome_fantasia`, `cnpj`, `nire`
- `junta_comercial`, `numero_registro`, `data_registro`
- `tipo_societario`

## 2) Capital e quotas
- `capital_social_total` e `capital_moeda` (literal)
- `integralizacao_descricao` (texto literal/curto se houver cláusula explicando a forma de integralização)
- `quotas` e `socios` conforme o schema (sem inferência).

## 3) Administração
Extrair:
- `administradores` (nome, qualificação/papel, poderes se explícitos)
- `regras_administracao` e `limitacoes_ato_administracao` (texto literal resumido)
- Cláusulas relevantes: `clausulas_*` existentes no schema.

## 4) Imóveis integralizados/incorporados (CRÍTICO para cruzamento com escrituras)
Quando houver seção listando imóveis (ex.: “imóveis a seguir elencados”, “matrícula nº ...”, “anexo ...”),
preencher `imoveis_integralizados[]` com **um item por imóvel**.

### 4.1) Campos mínimos por imóvel
- `matricula_numero` (ex.: “7.546”, “907”, etc.)
- `descricao` (resumo fiel do texto, mantendo natureza do bem, área/local, confrontações quando essenciais)
- `localizacao` (endereço/cidade quando constar)
- Valores (quando constarem):
  - `valor_venal_original` (ex.: “Cr$ ...”)
  - `valor_atribuido` (ex.: “R$ ...”)
  - `valor_avaliacao_original` / `valor_avaliacao` quando o texto trouxer avaliação.
- `onus_ou_dividas_mencionadas[]`: registrar **apenas menções explícitas** de ônus, hipotecas, arrendamentos,
  responsabilidades solidárias ou dívidas vinculadas ao imóvel (texto literal curto).
- `observacoes`: incluir observações explícitas (ex.: “constituto possessório”, “posse direta até ...”, etc.)
- `fonte`: sempre com `arquivo_md` e `ancora` (usar o marcador de página existente no .md, como `[[PÁGINA X]]` ou `<!-- PÁGINA X -->`).

### 4.2) Regras de consistência
- Se houver múltiplos valores para o mesmo imóvel (valor venal + valor atribuído + avaliação), não substituir: preencher campos distintos.
- Se o texto disser “ônus vincados ... são de responsabilidade solidária...”, registrar em `onus_ou_dividas_mencionadas`
  e/ou `observacoes`, mas **não inventar** quais seriam os ônus.

## 5) Assinaturas e data
Preencher `data_assinatura` quando constar (e sua âncora).

## 6) Observações
Se houver partes ilegíveis, registrar em `observacoes_extracao` (ou campo equivalente no schema) de forma objetiva.
