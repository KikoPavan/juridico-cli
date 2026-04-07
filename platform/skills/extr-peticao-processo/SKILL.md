---
base: extraction-base.md
description: "Extrai dados estruturados de petições judiciais (inicial, incidental,
  manifestação, emenda): identificação da peça, partes, fatos, fundamentos, pedidos
  e provas. Use esta skill sempre que o documento for uma petição inicial, emenda à
  inicial, manifestação, petição intermediária ou qualquer peça postulatória. Acione
  também para: \"extrair petição\", \"estruturar pedidos\", \"coletar fatos e fundamentos\",
  \"pipeline collector-proc peticao\", \"valor da causa\".\n"
document_types:
- peticao_processo
hitl: false
key_fields:
- process_number
- parties
- representations
- peticao_identification
- valor_da_causa
- fatos
- fundamentos
- provas_e_requerimentos
- pedidos
llm_default: gemini_api
name: extr-peticao-processo
target_schema: assets/peticao_processo.schema.json
version: 0.2.0
---

# Instrução de Extração: Petição Judicial

Seu único output é um objeto JSON conforme `assets/peticao_processo.schema.json`.
Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

---

## Regras específicas

### 1) Identificação mínima
- Se houver número do processo, preencher `process_number` como AnchoredString com âncora.
- Se houver título/cabeçalho da peça (ex.: "PETIÇÃO INICIAL", "EMENDA À INICIAL",
  "MANIFESTAÇÃO"), preencher `peticao_identification` com `value` + `anchors`.
- Não inventar tipo de petição se não estiver explícito.

### 2) Partes e representantes (somente se constar)
- `parties`: incluir apenas se o texto trouxer partes identificadas.
- `role`: só classificar quando o texto indicar; caso contrário `role = outro` + `role_raw`.
- `representations`: advogados/OAB apenas quando constarem, com âncora.

### 3) Valor da causa (quando constar)
- Capturar como AnchoredString com texto literal em `valor_da_causa`.
- Não converter moeda, não calcular, não normalizar.

### 4) Fatos e fundamentos — itens curtos, literais e separados
- Se o texto tiver seções ("DOS FATOS", "DO DIREITO", "DA FUNDAMENTAÇÃO"), criar
  itens separados em `fatos` e `fundamentos`.
- Cada item (`AnchoredTextItem`) deve ter `text` literal curto + `anchors` próprias.
- Não resumir criativamente; não adicionar conclusões.
- `label` opcional: rótulo curto da seção (ex.: "Dos Fatos", "Do Direito").

### 5) Pedidos — regra crítica
- `pedidos` deve ser a parte mais estruturada:
  - Um item por pedido quando o texto for enumerado (a), b), I, II, "requer", "pede").
  - Cada pedido (`Pedido`) deve ter `text` literal + `anchors` próprias.
- Não transformar pedidos implícitos em explícitos.

### 6) Provas e requerimentos
- Capturar menções explícitas a provas, documentos, diligências, intimações, perícias.
- Itens literais curtos em `provas_e_requerimentos`, com âncora por item.

### 7) Schema anyOf
- Obrigatório ao menos um de: `pedidos`, `fatos`, `fundamentos`, `valor_da_causa`, `parties`.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                               |
|-----------------|---------------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                           |
| `output_dir`    | `var/output/proc`                                                          |
| `output_prefix` | `peticao_proc_out`                                                         |
| `schema_file`   | `platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json`|

## Arquivos da skill

| Arquivo                                                  | Propósito                                   |
|----------------------------------------------------------|---------------------------------------------|
| `SKILL.md`                                               | Instrução canônica de extração (este arquivo)|
| `assets/peticao_processo.schema.json`                    | Schema 1:1                                  |
| `assets/peticao_processo.consolidated.schema.json`       | Schema consolidado                          |
| `references/dicionario_campos.md`                        | Dicionário de campos                        |
| `scripts/validate_output.py`                             | Validação contra o schema                   |

## Uso pelo runtime

1. Carregar documento (Markdown) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON conforme `assets/peticao_processo.schema.json`.
4. Validar: `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.
