---
name: procuracao
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/procuracao.schema.json"
document_types:
  - procuracao
key_fields:
  - process_number
  - outorgante
  - outorgados
  - poderes
  - data
  - local
  - restricoes_ou_limitacoes
  - assinantes
  - anchors
validation_rules:
  - literalidade
  - ancoragem_em_poderes
  - nao_inferir_poderes
  - nao_inventar_partes
  - preservar_texto_de_clausulas
---

# SKILL — procuracao

## Finalidade
Extrair, de uma procuração, os elementos essenciais **quando explicitamente presentes**:
- outorgante (quem concede poderes),
- outorgado(s) (quem recebe poderes),
- poderes/cláusulas,
- data/local/assinaturas,
- restrições/limitações,
com **âncoras fortes nos poderes**.

## Regras específicas (além do CORE)

### 1) Identificação mínima
- Se houver número do processo no texto, preencher `process_number` com âncora.
- Não inventar identificação do processo se não estiver escrito.

### 2) Outorgante e outorgado(s)
- Preencher `outorgante` somente se estiver identificado no texto, com âncora.
- `outorgados`: registrar cada outorgado identificado, com âncora por pessoa (ou por bloco se vierem agrupados, desde que o `quote` seja suficiente).
- Se houver qualificação (CPF/CNPJ, RG, endereço, estado civil etc.), manter literal (em `qualification` quando aplicável) e ancorar.

### 3) Poderes — regra crítica
- `poderes` deve conter **itens literais** (cláusulas/poderes) com âncora própria.
- Separar poderes quando o texto for enumerado (itens, alíneas, incisos) ou quando houver blocos distinguíveis (“poderes gerais”, “poderes especiais”).
- Só preencher `power_type` quando o próprio texto indicar explicitamente (“gerais”, “especiais”); caso contrário, use apenas `text`.

### 4) Data e local
- `data` e `local` apenas quando estiverem explicitamente no documento, com âncora.
- Não deduzir data pelo contexto (ex.: capa do processo).

### 5) Restrições / limitações
- Registrar cláusulas de limitação, prazo, validade, ressalvas, condições e observações **somente se escritas**.
- Inserir como itens em `restricoes_ou_limitacoes`, com âncora por item.

### 6) Assinaturas / assinantes
- Se houver assinaturas nominadas, registrar em `assinantes` com âncora.
- Se o documento disser “assinado eletronicamente” sem nomes, não inventar.

### 7) Coerência
- Não misturar conteúdo de petição/contestação/decisão na procuração.
- Se a procuração mencionar poderes “para o foro em geral” ou similares, manter literal (não “expandir” o significado).

### 8) Consolidação (quando o schema for consolidated)
- Unir listas preservando âncoras.
- Se houver divergências materiais (ex.: outorgados diferentes, poderes incompatíveis), registrar em `conflicts` no schema consolidated (não apagar).
