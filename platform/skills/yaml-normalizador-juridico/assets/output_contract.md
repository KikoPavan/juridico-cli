# Contrato I/O — yaml-normalizador-juridico

**Versão:** 1.0.0
**Skill upstream:** `curador-relevancia`
**Skill downstream:** `dispatcher-skill`

---

## 1. Entrada

A skill recebe um payload JSON único (ou um array de payloads) representando as peças já
curadas pelo `curador-relevancia`.

### 1.1 Campos obrigatórios

| Campo                        | Tipo      | Garantia de presença  |
|-----------------------------|-----------|----------------------|
| `piece_id`                  | string    | Sempre presente      |
| `document_type`             | string    | Sempre presente      |
| `acao_curatorial`           | enum      | Sempre presente      |
| `modo_aplicado`             | string    | Sempre presente      |
| `justificativa_curta`       | string    | Sempre presente      |
| `impacto_processual`        | enum      | Sempre presente      |
| `impacto_sentenca_confirmado` | boolean | Sempre presente      |
| `prioridade`                | enum      | Sempre presente      |
| `compressao_sugerida`       | enum      | Sempre presente      |
| `encaminhamento`            | string    | Sempre presente      |
| `audit_trail`               | array     | Sempre presente      |
| `text`                      | string    | Sempre presente      |
| `anchors`                   | array     | Sempre presente      |
| `pages_start`               | integer   | Sempre presente      |
| `pages_end`                 | integer   | Sempre presente      |
| `source_file`               | string    | Sempre presente      |
| `source_path`               | string    | Sempre presente      |
| `source_sha256`             | string    | Sempre presente      |
| `process_group_id`          | string    | Sempre presente      |
| `origin_piece_index`        | integer   | Sempre presente      |

### 1.2 Campos opcionais (enriquecimento)

| Campo             | Tipo            | Comportamento se ausente              |
|-------------------|-----------------|--------------------------------------|
| `title`           | string ou null  | Usar `null` no frontmatter           |
| `document_date`   | string ou null  | Usar `null` no frontmatter           |
| `parties_raw`     | array ou null   | Usar `[]` em `parties_normalized`    |
| `court`           | string ou null  | Usar `null` no frontmatter           |
| `judge`           | string ou null  | Usar `null` no frontmatter           |

---

## 2. Saída

Para cada peça **não marcada como `remover`**, a skill produz **um arquivo `.md`** com a
seguinte estrutura:

```
---
<frontmatter YAML>
---

<texto da peça>
```

### 2.1 Nome do arquivo de saída

```
{process_group_id}__{piece_id}.md
```

Exemplo: `proc-2024-0042__peca-001-peticao.md`

### 2.2 Campos do frontmatter — obrigatórios

| Campo                | Origem                         | Tipo      | Permite null? |
|---------------------|-------------------------------|-----------|---------------|
| `piece_id`          | Input direto                  | string    | Não           |
| `document_type`     | Input direto                  | string    | Não           |
| `skill_key`         | Mapeado via routing_map.yaml  | string    | Não           |
| `source_file`       | Input direto                  | string    | Não           |
| `source_path`       | Input direto                  | string    | Não           |
| `source_sha256`     | Input direto                  | string    | Não           |
| `pages_start`       | Input direto                  | integer   | Não           |
| `pages_end`         | Input direto                  | integer   | Não           |
| `process_group_id`  | Input direto                  | string    | Não           |
| `origin_piece_index`| Input direto                  | integer   | Não           |
| `acao_curatorial`   | `acao_curatorial` do input    | string    | Não           |
| `priority`          | `prioridade` do input         | string    | Não           |
| `impacto_processual`| Input direto                  | string    | Não           |
| `impacto_sentenca_confirmado`  | `impacto_sentenca_confirmado` | boolean   | Não           |
| `review_status`     | Derivado de `acao_curatorial` | enum      | Não           |
| `language`          | Padrão `pt-BR`                | string    | Não           |
| `created_by_skill`  | Constante                     | string    | Não           |
| `status`            | Derivado de `acao_curatorial` | enum      | Não           |
| `normalized_at`     | Timestamp de execução         | datetime  | Não           |

### 2.3 Campos do frontmatter — recomendados/opcionais

| Campo                | Origem                         | Tipo           | Permite null? |
|---------------------|-------------------------------|----------------|---------------|
| `title`             | Input opcional                | string         | Sim           |
| `document_date`     | Input opcional (normalizado)  | string ISO8601 | Sim           |
| `parties_normalized`| Derivado de `parties_raw`     | array string   | Sim (`[]`)    |
| `court`             | Input opcional                | string         | Sim           |
| `judge`             | Input opcional                | string         | Sim           |
| `tags`              | Derivado de `document_type`   | array string   | Sim (`[]`)    |
| `notes`             | `justificativa_curta`         | string         | Sim           |

---

## 3. Mapeamento de `acao_curatorial` para campos de status

| `acao_curatorial` | `review_status`   | `status`       | Gera arquivo? |
|-------------------|-------------------|----------------|---------------|
| `manter`          | `approved`        | `ready`        | ✅ Sim         |
| `comprimir`       | `approved`        | `ready`        | ✅ Sim         |
| `revisar`         | `pending_review`  | `needs_review` | ✅ Sim         |
| `remover`         | —                 | —              | ❌ Não         |

---

## 4. Garantias da skill

- O `audit_trail` do input é sempre preservado integralmente no corpo do artefato como
  bloco YAML comentado ou campo extra; a trilha da normalização é **acrescentada**, não substituída.
- O texto da peça nunca é editado além de sanitização de whitespace excessivo.
- `created_by_skill` é sempre `yaml-normalizador-juridico` — nunca alterável via input.
- `skill_key` é sempre derivada do `routing_map.yaml` — nunca inventada.

## 5. Limitações conhecidas

- A skill não valida a autenticidade dos metadados de origem (SHA-256, datas).
- A normalização de `parties_normalized` é heurística; nomes compostos podem precisar de revisão manual.
- Tipos documentais não listados no `routing_map.yaml` resultam em `skill_key: REVISAR_MANUAL`.
