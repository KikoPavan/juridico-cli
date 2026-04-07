---
base: extraction-base.md
description: "Extrai dados estruturados de contestações judiciais: identificação da
  peça, partes, preliminares, mérito/impugnações, provas e pedidos finais. Use esta
  skill sempre que o documento for uma contestação, resposta, impugnação ou peça
  defensiva. Acione também para: \"extrair contestação\", \"coletar preliminares\",
  \"estruturar mérito da defesa\", \"pedidos finais da contestação\", \"pipeline
  collector-proc contestacao\".\n"
document_types:
- contestacao_processo
hitl: false
key_fields:
- process_number
- parties
- representations
- contestacao_identification
- preliminares
- merito
- provas_e_requerimentos
- pedidos_finais
llm_default: gemini_api
name: extr-contestacao-processo
target_schema: assets/contestacao_processo.schema.json
version: 0.2.0
---

# Instrução de Extração: Contestação Judicial

Seu único output é um objeto JSON conforme `assets/contestacao_processo.schema.json`.
Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

---

## Regras específicas

### 1) Identificação mínima
- Se houver número do processo, preencher `process_number` como AnchoredString.
- Se houver título ("CONTESTAÇÃO", "RESPOSTA", "IMPUGNAÇÃO"), preencher
  `contestacao_identification` com `value` + `anchors`.
- Não deduzir tipo de contestação.

### 2) Partes e representantes (somente se constar)
- `parties`: incluir apenas se identificadas; usar `role = outro` + `role_raw` quando
  o rótulo for diferente.
- `representations`: advogados/OAB apenas quando constarem.

### 3) Preliminares (quando existirem)
- Se o texto tiver seção "PRELIMINAR(ES)" ou equivalente, criar itens em `preliminares`.
- Cada `Argumento` deve ter `text` literal curto + `anchors` próprias.
- Não criar preliminares implícitas.

### 4) Mérito / impugnações
- Se o texto tiver seção "MÉRITO", "NO MÉRITO", "IMPUGNAÇÃO", criar itens em `merito`.
- Cada `Argumento` deve ter `text` literal curto + `anchors` próprias.
- Não transformar alegações em conclusões jurídicas.

### 5) Provas e requerimentos
- Itens literais em `provas_e_requerimentos` com âncora por item.

### 6) Pedidos finais
- `pedidos_finais`: um item por pedido quando possível, com âncora.
- Não inferir pedidos não escritos.

### 7) Schema anyOf
- Obrigatório ao menos um de: `preliminares`, `merito`, `pedidos_finais`.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                                   |
|-----------------|-------------------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                               |
| `output_dir`    | `var/output/proc`                                                              |
| `output_prefix` | `contestacao_proc_out`                                                         |
| `schema_file`   | `platform/skills/extr-contestacao-processo/assets/contestacao_processo.schema.json` |

## Arquivos da skill

| Arquivo                                                    | Propósito                                   |
|------------------------------------------------------------|---------------------------------------------|
| `SKILL.md`                                                 | Instrução canônica de extração (este arquivo)|
| `assets/contestacao_processo.schema.json`                  | Schema 1:1                                  |
| `assets/contestacao_processo.consolidated.schema.json`     | Schema consolidado                          |
| `references/dicionario_campos.md`                          | Dicionário de campos                        |
| `scripts/validate_output.py`                               | Validação                                   |

## Uso pelo runtime

1. Carregar documento (Markdown) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON conforme `assets/contestacao_processo.schema.json`.
4. Validar: `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.
