---
base: extraction-base.md
description: "Extrai dados estruturados de capa/cabeçalho de processo judicial: número
  do processo, tribunal, comarca, vara, classe, assunto, data de distribuição, partes
  e advogados. Use esta skill sempre que o documento for uma capa de processo, certidão
  de distribuição, ficha de autuação ou qualquer documento cujo objetivo seja identificar
  o processo. Acione também para: \"extrair capa do processo\", \"número do processo\",
  \"identificar tribunal e vara\", \"distribuição do processo\", \"pipeline collector-proc
  cabecalho\".\n"
document_types:
- cabecalho_processo
hitl: false
key_fields:
- process_number
- court
- comarca
- vara
- classe
- assunto
- distribution_date
- parties
- representations
- anchors
llm_default: gemini_api
name: extr-cabecalho-processo
target_schema: assets/cabecalho_processo.schema.json
version: 0.2.0
---

# Instrução de Extração: Capa/Cabeçalho do Processo

Você é um extrator de dados jurídicos. Seu único output é um objeto JSON válido
conforme `assets/cabecalho_processo.schema.json`.

Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

---

## Regras específicas

### 1) Identificação (prioridade máxima)
- Capture `process_number` somente se estiver escrito (como `AnchoredString` com âncora).
- Capture `court`, `comarca`, `vara`, `classe`, `assunto`, `distribution_date` quando
  existirem, cada qual como objeto com `value` + `anchors`.
- Não deduzir tribunal/vara/comarca pelo contexto; se não estiver, omita.

### 2) Partes (conforme aparecer no cabeçalho)
- Liste `parties` conforme o cabeçalho apresentar.
- Para `role`, só classifique como `autor`, `reu` etc. se o texto indicar explicitamente.
- Se o rótulo for diferente (ex.: "Requerente", "Agravado"):
  - `role = outro` e `role_raw` = rótulo literal.
- Qualificação (CPF/CNPJ, RG, endereço etc.): manter literal e ancorar.

### 3) Representantes/advogados (quando constar)
- Registre `representations` apenas quando o cabeçalho trouxer advogados/representantes.
- Não assumir vínculo de advogado com parte se não estiver explícito.
- OAB deve ser literal; se não constar, omitir.

### 4) Âncoras (exigência reforçada)
- Exija âncora em: número do processo, classe/assunto, partes.
- Evite âncora genérica para vários campos; prefira uma âncora por campo.
- Cada campo `AnchoredString` / `AnchoredDate` exige `{value, anchors}`.

### 5) Não reescrever
- Preserve grafia e termos do documento.
- Não normalizar criativamente (ex.: não transformar "Vara Cível" em enum inexistente).

### 6) Schema anyOf
- O schema exige ao menos um de: `process_number`, `parties`, `classe`, `assunto`.
- Se nenhum desses existir no texto, marque no JSON o máximo que foi encontrado.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                               |
|-----------------|---------------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                           |
| `output_dir`    | `var/output/proc`                                                          |
| `output_prefix` | `cabecalho_proc_out`                                                       |
| `schema_file`   | `platform/skills/extr-cabecalho-processo/assets/cabecalho_processo.schema.json` |

## Arquivos da skill

| Arquivo                                              | Propósito                                   |
|------------------------------------------------------|---------------------------------------------|
| `SKILL.md`                                           | Instrução canônica de extração (este arquivo)|
| `assets/cabecalho_processo.schema.json`              | Schema 1:1                                  |
| `assets/cabecalho_processo.consolidated.schema.json` | Schema consolidado                          |
| `references/dicionario_campos.md`                    | Dicionário de campos                        |
| `scripts/validate_output.py`                         | Validação contra o schema                   |

## Uso pelo runtime

1. Carregar documento (Markdown) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON conforme `assets/cabecalho_processo.schema.json`.
4. Validar: `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.
