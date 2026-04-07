---
base: extraction-base.md
description: "Extrai dados estruturados de decisões judiciais, sentenças, acórdãos
  e despachos: tipo, data, decisor, relatório, fundamentação, dispositivo, resultado
  e determinações. Use esta skill sempre que o documento for uma sentença, decisão
  interlocutória, acórdão, despacho ou qualquer pronunciamento jurisdicional. Acione
  também para: \"extrair sentença\", \"estruturar dispositivo\", \"coletar fundamentação\",
  \"resultado da decisão\", \"pipeline collector-proc decisao\".\n"
document_types:
- decisao_processo
hitl: false
key_fields:
- process_number
- decision_type
- decision_date
- decisor
- relatorio
- fundamentacao
- dispositivo
- outcome
- determinacoes
llm_default: gemini_api
name: extr-decisao-processo
target_schema: assets/decisao_processo.schema.json
version: 0.2.0
---

# Instrução de Extração: Decisão Judicial

Seu único output é um objeto JSON conforme `assets/decisao_processo.schema.json`.
Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

---

## Regras específicas

### 1) Identificação mínima
- `process_number` como AnchoredString, somente se escrito.
- `decision_type`: preencher somente se o texto indicar (ex.: "SENTENÇA", "DECISÃO",
  "DESPACHO", "ACÓRDÃO"). Se não indicar, usar `value = outro` + `value_raw` literal.

### 2) Data e decisor (quando constar)
- `decision_date`: somente quando explícita (AnchoredDate).
- `decisor`: preencher com o que estiver explícito (nome, órgão, tribunal, cargo),
  com âncora. `anyOf`: precisa ao menos de `name`, `orgao_julgador` ou `tribunal`.

### 3) Relatório / fundamentação / dispositivo
- Seções claras ("RELATÓRIO", "FUNDAMENTAÇÃO", "DISPOSITIVO") viram itens separados.
- `dispositivo` — ancoragem forte: cada DispositivoItem deve ter âncora própria.
  Separar quando o texto for enumerado (I, II, alíneas, "defiro/indefiro").
- Manter trechos literais; não reescrever o dispositivo.

### 4) Outcome (resultado) — somente se explícito
- Preencher `outcome` somente quando o texto afirmar explicitamente (ex.: "defiro",
  "indefiro", "julgo procedente").
- Se ambíguo: omitir ou usar `value = outro` + `value_raw`.

### 5) Determinações
- Intimações, prazos, expedição de ofícios, perícias, remessas: itens literais com
  âncora em `determinacoes`.

### 6) Schema anyOf
- Obrigatório ao menos um de: `dispositivo`, `outcome`, `decision_date`, `decisor`,
  `fundamentacao`.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                              |
|-----------------|--------------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                          |
| `output_dir`    | `var/output/proc`                                                         |
| `output_prefix` | `decisao_proc_out`                                                        |
| `schema_file`   | `platform/skills/extr-decisao-processo/assets/decisao_processo.schema.json` |

## Arquivos da skill

| Arquivo                                             | Propósito                                   |
|-----------------------------------------------------|---------------------------------------------|
| `SKILL.md`                                          | Instrução canônica de extração (este arquivo)|
| `assets/decisao_processo.schema.json`               | Schema 1:1                                  |
| `assets/decisao_processo.consolidated.schema.json`  | Schema consolidado                          |
| `references/dicionario_campos.md`                   | Dicionário de campos                        |
| `scripts/validate_output.py`                        | Validação                                   |

## Uso pelo runtime

1. Carregar documento (Markdown) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON conforme `assets/decisao_processo.schema.json`.
4. Validar: `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.
