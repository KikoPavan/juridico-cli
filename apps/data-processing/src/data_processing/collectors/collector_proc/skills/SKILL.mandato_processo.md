---
name: mandato_processo
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/mandato_processo.schema.json"
document_types:
  - mandato_processo
key_fields:
  - process_number
  - mandante
  - mandatario
  - escopo
  - poderes
  - data
  - local
  - restricoes_ou_limitacoes
  - assinantes
  - anchors
validation_rules:
  - literalidade
  - ancoragem_em_poderes_e_escopo
  - nao_inferir_relacao_mandataria
  - preservar_texto_de_clausulas
---

# SKILL — mandato_processo

## Finalidade
Extrair, de um instrumento de mandato (ou termo semelhante), os elementos essenciais **quando explicitamente presentes**:
- mandante (quem confere poderes),
- mandatário (quem recebe poderes),
- escopo/objeto do mandato,
- poderes/cláusulas,
- data/local/assinaturas,
- restrições/limitações,
com **âncoras fortes em poderes e escopo**.

## Regras específicas (além do CORE)

### 1) Identificação mínima
- Se houver número do processo no texto, preencher `process_number` com âncora.
- Não inventar identificação do processo se não estiver escrita.

### 2) Mandante e mandatário
- Preencher `mandante` e `mandatario` somente se o texto identificar claramente, com âncora.
- Se houver qualificação (CPF/CNPJ, RG, endereço etc.), manter literal (em `qualification` quando aplicável) e ancorar.
- Não inferir relação mandatária por contexto; precisa estar descrita.

### 3) Escopo/objeto — regra crítica
- `escopo` deve conter itens literais que descrevam o objeto/alcance do mandato (cláusulas), com âncora por item.
- Separar por itens quando o texto estiver enumerado ou quando houver blocos distinguíveis.
- Não reescrever nem “explicar” o escopo: manter trechos literais curtos.

### 4) Poderes — regra crítica
- `poderes` deve conter **itens literais** (cláusulas/poderes) com âncora própria.
- Separar poderes quando o texto for enumerado (itens, alíneas, incisos) ou quando houver blocos distinguíveis.
- Só classificar `power_type` (quando existir no schema) se o texto indicar explicitamente (“gerais”, “especiais”); caso contrário, usar apenas `text`.

### 5) Data e local
- `data` e `local` apenas quando estiverem explicitamente no documento, com âncora.
- Não deduzir data por contexto externo.

### 6) Restrições / limitações
- Registrar cláusulas de limitação, prazo, validade, ressalvas, condições **somente se escritas**.
- Inserir como itens em `restricoes_ou_limitacoes`, com âncora por item.

### 7) Assinaturas / assinantes
- Se houver assinaturas nominadas, registrar em `assinantes` com âncora.
- Se o documento disser “assinado eletronicamente” sem nomes, não inventar.

### 8) Coerência
- Não misturar conteúdo de petição/contestação/decisão dentro do mandato.
- Se houver referência a “foro em geral” ou expressões equivalentes, manter literal (não expandir significado).

### 9) Consolidação (quando o schema for consolidated)
- Unir listas preservando âncoras.
- Divergências materiais (mandante/mandatário/poderes incompatíveis) devem ir para `conflicts` no schema consolidated (não apagar).
