---
base: extraction-base.md
description: "Extrai e consolida o dossiê agregado de um processo judicial, compondo
  identificação, partes, representantes, linha do tempo e índice de peças a partir
  de múltiplas fontes 1:1. Use esta skill sempre que o objetivo for montar a visão
  completa/consolidada de um caso a partir de outputs individuais de outras skills.
  Acione também para: \"dossiê do processo\", \"consolidar processo\", \"pipeline
  collector-proc processo\", \"montar caso\", \"aggregar peças processuais\".\n"
document_types:
- processo
hitl: false
key_fields:
- process_number
- court
- comarca
- vara
- classe
- assunto
- parties
- representations
- documentos_referenciados
- anchors
llm_default: gemini_api
name: extr-processo
target_schema: assets/processo.schema.json
version: 0.2.0
---

# Instrução de Extração: Consolidação do Dossiê do Processo

Você é um extrator de consolidação de dados processuais. Seu único output é um objeto
JSON válido conforme o schema `assets/processo.schema.json`.

Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

> **Atenção:** este schema é um agregador/índice. Não é extração 1:1 de uma peça
> específica. Campos devem ser preenchidos somente se explicitamente presentes nas
> fontes recebidas.

---

## Finalidade
Gerar a visão dossiê do processo quando o `document_type` for `processo`.
Este tipo é agregador/índice: captura identificação, partes, representantes e
referências úteis **somente se estiverem explicitamente no texto recebido**.

---

## Regras específicas

### 1) Identificação do processo (prioridade máxima)
- Se houver número do processo, capture como `process_number` com âncora.
- Se houver tribunal/foro/comarca/vara/classe/assunto, capture cada item com âncora
  própria dentro de `header_summary`.
- **Não inventar** número, classe, assunto, vara, comarca. Se não estiver escrito, omita.

### 2) Partes — sem inferência
- Liste partes em `parties` somente se constarem no texto.
- Para `role`, só classifique quando o texto indicar explicitamente.
- Se o rótulo for diferente, use `role = outro` e preencha `role_raw` com texto literal.
- Qualificação (CPF/CNPJ, RG, endereço, estado civil etc.): manter literal e ancorar.

### 3) Representação (advogados/OAB) — somente quando constar
- Vincule advogado a parte somente se o texto permitir (ex.: "Advogado do Autor: …").
- OAB deve ser literal; se não houver, não preencher.

### 4) Índice de documentos (`document_index`)
- Para cada peça detectada, criar um item em `document_index`:
  - `document_type`, `source_id`, `source_sha256`, `anchors` (obrigatórios).
  - `title`, `md_filename`, `document_date` quando explícitos.

### 5) Linha do tempo (`timeline`)
- Opcional. Capturar eventos explícitos com `event_type`, `description` e `anchors`.
- Não inferir eventos. Usar `event_type = outro` + `event_type_raw` quando não couber
  nos tipos definidos.

### 6) Âncoras
- Identificação, partes e referências de documentos devem ter âncoras.
- Evite âncoras genéricas para múltiplos fatos: prefira 1 âncora por fato.

### 7) Coerência
- Não misturar conteúdo de outros `document_type` dentro deste JSON.
- Campos `sources`, `merge_meta` e `conflicts` são obrigatórios pelo schema.
- Se não houver conflitos detectados, retornar `conflicts: []`.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                     |
|-----------------|------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                 |
| `output_dir`    | `var/output/proc`                                                |
| `output_prefix` | `processo_out`                                                   |
| `schema_file`   | `platform/skills/extr-processo/assets/processo.schema.json`     |

## Arquivos da skill

| Arquivo                           | Propósito                                        |
|-----------------------------------|--------------------------------------------------|
| `SKILL.md`                        | Instrução canônica de extração (este arquivo)    |
| `assets/processo.schema.json`     | Schema JSON canônico (fonte de verdade)          |
| `references/dicionario_campos.md` | Dicionário de campos com tipos e obrigatoriedade |
| `scripts/validate_output.py`      | Valida o JSON de saída contra o schema           |

## Uso pelo runtime

1. Receber outputs 1:1 das demais skills (cabecalho, peticao, contestacao, decisao etc.).
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON conforme `assets/processo.schema.json`.
4. Validar com `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.

## Validação rápida

```bash
uv run python platform/skills/extr-processo/scripts/validate_output.py \
  --input var/output/proc/processo_out_001.json
```
