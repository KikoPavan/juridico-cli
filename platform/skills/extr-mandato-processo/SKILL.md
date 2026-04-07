---
base: extraction-base.md
description: "Extrai dados estruturados de instrumentos de mandato judicial: mandante,
  mandatário, escopo/objeto, poderes, data, local, restrições e assinantes. Use esta
  skill sempre que o documento for um instrumento de mandato, termo de nomeação ou
  documento similar que confira poderes no âmbito de um processo. Acione também para:
  \"extrair mandato\", \"estruturar poderes do mandato\", \"coletar escopo do mandato\",
  \"pipeline collector-proc mandato\".\n"
document_types:
- mandato_processo
hitl: false
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
llm_default: gemini_api
name: extr-mandato-processo
target_schema: assets/mandato_processo.schema.json
version: 0.2.0
---

# Instrução de Extração: Instrumento de Mandato

Seu único output é um objeto JSON conforme `assets/mandato_processo.schema.json`.
Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

---

## Regras específicas

### 1) Identificação mínima
- `process_number` como AnchoredString, somente se escrito.
- Não inventar identificação do processo.

### 2) Mandante e mandatário
- Preencher `mandante` e `mandatario` somente quando identificados claramente, com âncora.
- Se houver qualificação (CPF/CNPJ, RG, endereço), manter literal em `qualification`.
- Não inferir relação mandatária por contexto.

### 3) Escopo — regra crítica
- `escopo` deve conter itens literais com o objeto/alcance do mandato, com âncora por item.
- Separar quando o texto for enumerado ou houver blocos distinguíveis.
- Não reescrever: manter trechos literais curtos.

### 4) Poderes — regra crítica
- `poderes`: itens literais com âncora própria por item.
- Separar quando enumerado (itens, alíneas, incisos).
- `power_type` somente quando o texto indicar explicitamente ("gerais", "especiais").

### 5) Data e local
- `data` e `local` apenas quando explícitos, com âncora.

### 6) Restrições e assinantes
- `restricoes_ou_limitacoes`: cláusulas explícitas de limitação/prazo/validade, com âncora.
- `assinantes`: nomes explicitamente nominados, com âncora.

### 7) Schema anyOf
- Obrigatório ao menos um de: `poderes`, `escopo`, `mandante`, `mandatario`.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                              |
|-----------------|--------------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                          |
| `output_dir`    | `var/output/proc`                                                         |
| `output_prefix` | `mandato_proc_out`                                                        |
| `schema_file`   | `platform/skills/extr-mandato-processo/assets/mandato_processo.schema.json` |

## Arquivos da skill

| Arquivo                                              | Propósito                                   |
|------------------------------------------------------|---------------------------------------------|
| `SKILL.md`                                           | Instrução canônica de extração (este arquivo)|
| `assets/mandato_processo.schema.json`                | Schema 1:1                                  |
| `assets/mandato_processo.consolidated.schema.json`   | Schema consolidado                          |
| `references/dicionario_campos.md`                    | Dicionário de campos                        |
| `scripts/validate_output.py`                         | Validação                                   |

## Uso pelo runtime

1. Carregar documento (Markdown) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON conforme `assets/mandato_processo.schema.json`.
4. Validar: `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.
