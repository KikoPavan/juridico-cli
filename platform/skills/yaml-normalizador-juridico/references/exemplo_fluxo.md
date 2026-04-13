# Exemplo de Fluxo — yaml-normalizador-juridico no Pipeline

Este documento ilustra a jornada de uma peça desde a segmentação até a extração,
passando pela normalização YAML.

---

## Contexto

**Processo:** Ação de Cobrança — proc-2024-0042
**Arquivo:** `processo_1234567-89_2024_SP.pdf` (12 páginas, 3 peças)
**Peça:** Petição inicial (páginas 3–4)

---

## Etapa 1 — segmentador-juridico

**Input:** Markdown limpo
**Output:** Envelope de Processo `{metadata, pecas[]}`

```json
{
  "metadata": {
    "processo_id": "proc-2024-0042",
    "total_pecas": 3,
    "gerado_por": "segmentador-juridico",
    "source_file": "processo_1234567-89_2024_SP.pdf"
  },
  "pecas": [
    {
      "piece_id": "peca_001",
      "document_type": "peticao_inicial",
      "text": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...",
      "anchors": [{ "label": "cabecalho", "page": 3 }, { "label": "pedidos", "page": 4 }],
      "pages_start": 3, "pages_end": 4, "pages_total": 2,
      "source_sha256": "a3f5e2d1c0b9a8f7...",
      "process_group_id": "proc-2024-0042",
      "origin_piece_index": 0,
      "relevancia_estimada": 0.98
    }
  ]
}
```

---

## Etapa 2 — curador-relevancia

**Input:** Envelope de Processo
**Output:** Envelope Curado — mesmas peças com campos curatoriais

```json
{
  "metadata": {
    "gerado_por": "segmentador-juridico",
    "modo_aplicado": "padrao",
    "gerado_por_curador": "curador-relevancia"
  },
  "pecas": [
    {
      "piece_id": "peca_001",
      "...campos herdados...": "",
      "acao_curatorial": "manter",
      "justificativa_curta": "Peça fundamental — contém causa de pedir e pedidos.",
      "impacto_processual": "nuclear",
      "prioridade": 1,
      "encaminhamento": "extr-peticao-processo",
      "audit_trail": [
        { "stage": "segmentador-juridico", "action": "segmento_classificado" },
        { "stage": "curador-relevancia", "action": "decisao_curatorial_aplicada" }
      ]
    }
  ]
}
```

---

## Etapa 3 — yaml-normalizador-juridico ← VOCÊ ESTÁ AQUI

**Input:** Peça Curada Individual (`pecas[0]` extraída do envelope)
**Operações:**

1. Validar campos obrigatórios
2. Consultar `routing_map.yaml`: `peticao_inicial` → `extr-peticao-processo`
3. Calcular `review_status`: `manter` → `approved`
4. Gerar frontmatter YAML com PyYAML
5. Concatenar frontmatter + texto da peça
6. Persistir: `proc-2024-0042__peca_001.md`
7. Validar artefato gerado

**Output:** `proc-2024-0042__peca_001.md`

```markdown
---
piece_id: peca_001
document_type: peticao_inicial
skill_key: extr-peticao-processo
source_file: processo_1234567-89_2024_SP.pdf
source_sha256: a3f5e2d1c0b9a8f7...
pages_start: 3
pages_end: 4
process_group_id: proc-2024-0042
origin_piece_index: 0
acao_curatorial: manter
priority: 1
impacto_processual: nuclear
impacto_sentenca_confirmado: true
review_status: approved
language: pt-BR
created_by_skill: yaml-normalizador-juridico
status: ready
---

EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO...
```

---

## Etapa 4 — dispatcher-skill

Lê `skill_key` do frontmatter → roteia para `extr-peticao-processo`.

---

## Resumo do Fluxo

```
PDF → segmentador-juridico → [Envelope de Processo]
  → curador-relevancia → [Envelope Curado]
    → orquestrador extrai pecas[i]
      → yaml-normalizador-juridico → [peca_NNN.md com frontmatter]
        → dispatcher → extr-* → JSON com campos extraídos ✅
```

---

## Fallback — Tipo Não Classificado

Se `document_type` fosse `nao_classificado`:

```
routing_map.yaml: "nao_classificado" → skill_key: REVISAR_MANUAL
→ review_status: unroutable
→ status: needs_review
→ arquivo gerado com aviso explícito no frontmatter
```

O dispatcher detecta `skill_key: REVISAR_MANUAL` → fila de revisão humana, sem invocar `extr-*`.
