---
name: curador-relevancia
version: "1.1.0"
skill_type: "llm"
description: >
  Curadoria jurídica de relevância para pipelines de processamento de documentos legais brasileiros.
  Recebe o Envelope de Processo do segmentador-jurídico e produz o Envelope Curado — mesmo
  envelope com cada peça enriquecida com decisão curatorial, justificativa, prioridade,
  encaminhamento e audit_trail. NUNCA descartar peças silenciosamente.
  Ative para: curadoria de relevância, filtrar peças, reduzir ruído processual,
  priorizar documentos, classificar relevância, manter/resumir/remover peças,
  impacto decisório, preparar acervo para skills especializadas.
input_stage: "segmented_pieces"
output_stage: "curated_pieces"
tags:
  - curadoria
  - relevancia
  - filtro
  - priorizacao
  - pipeline
guardrails:
  - "Nunca descartar peças silenciosamente — toda remoção exige justificativa"
  - "Peças juridicamente sensíveis sempre manter"
  - "Incerteza → revisar"
  - "Texto original intocável"
  - "Peças com impacto_sentenca_confirmado: true sempre manter"
  - "Respeitar schema_saida.json v1.1.0"
  - "audit_trail sempre como array de AuditEntry"
---

# Curador de Relevância — `curador-relevancia`

## Posição no Pipeline

```
PDF → convert → clean → segmentador-jurídico
  → [curador-relevancia]            ← você está aqui
  → yaml-normalizador-jurídico → dispatcher → extr-* → json por peça
```

## O que faz

Recebe o **Envelope de Processo** (`{metadata, pecas[]}`) do segmentador-jurídico e produz o
**Envelope Curado** — mesma estrutura com cada peça enriquecida com:
- `acao_curatorial` (`manter`, `resumir`, `remover`, `revisar`)
- `justificativa_curta` (1–120 chars)
- `impacto_processual` (`nuclear`, `relevante`, `acessorio`, `irrelevante`)
- `prioridade` (integer 1–5)
- `compressao_sugerida` (`resumo_1p`, `cabecalho_apenas`, `metadado_apenas`, `null`)
- `encaminhamento` (skill_key destino ou `null`)
- `audit_trail` (array de AuditEntry)

O metadata original é preservado integralmente e enriquecido com: `modo_aplicado`, `duracao_ms`,
`versao_schema`, `gerado_por_curador`.

---

## Modos de Operação

| Modo        | Comportamento                                                                  |
|-------------|--------------------------------------------------------------------------------|
| `padrao`    | Curadoria completa: conservadora, fallback para `revisar` |
| `sintetico` | Curadoria agressiva: alto limiar de retenção, comprime acessórios |

Configurar via parâmetro `modo` na entrada (`metadata.modo_curadoria`) ou variável de ambiente
`CURADOR_MODO` (padrão: `padrao`).

---

## Entrada: Envelope de Processo

```json
{
  "metadata": { "processo_id", "total_pecas", "gerado_por", "timestamp", ... },
  "pecas": [
    { "piece_id", "document_type", "pages_start", "pages_end", "pages_total",
      "text", "anchors", "relevancia_estimada", ... }
  ]
}
```

Schema: `assets/schema_entrada.json`

---

## Saída: Envelope Curado

```json
{
  "metadata": {
    "processo_id": "...",
    "gerado_por": "segmentador-juridico",
    "modo_aplicado": "padrao",
    "duracao_ms": 312,
    "versao_schema": "1.1.0",
    "gerado_por_curador": "curador-relevancia",
    ...
  },
  "pecas": [
    {
      "piece_id": "peca_001",
      "document_type": "peticao_inicial",
      "...campos herdados do segmentador...": "",
      "acao_curatorial": "manter",
      "justificativa_curta": "Petição inicial define objeto processual.",
      "impacto_processual": "nuclear",
      "impacto_sentenca_confirmado": true,
      "prioridade": 1,
      "compressao_sugerida": null,
      "encaminhamento": "extr-peticao-processo",
      "modo_aplicado": "padrao",
      "audit_trail": [
        { "stage": "segmentador-juridico", "timestamp": "...", "action": "...", "notes": "..." },
        { "stage": "curador-relevancia", "timestamp": "...", "action": "decisao_curatorial_aplicada", "notes": "..." }
      ]
    }
  ]
}
```

Schema: `assets/schema_saida.json`

---

## Regras de Negócio

### Regras Universais (ambos os modos)

1. **Nunca descartar silenciosamente** — toda `acao_curatorial: remover` exige `justificativa_curta`.
2. **Preservar peças juridicamente sensíveis** — petições, contestações, sentenças, laudos periciais,
   procurações e documentos de prova **sempre** recebem `manter`.
3. **Incerteza → `revisar`** — confiança < 0.6 ou tipo null obrigam marcação como `revisar`.
4. **Texto original intocável** — a skill classifica relevância, nunca altera conteúdo.
5. **audit_trail como array** — cada skill acrescenta uma `AuditEntry` ao array.

### Modo `padrao`

- Mantém tudo acima de `relevancia_estimada ≥ 0.4`
- Resume peças acessórias longas (> 3 páginas)
- Remove apenas despachos de expediente com prazo expirado e certidões irrelevantes
- Fallback: `manter` para peças não classificadas por regra específica

### Modo `sintetico`

- Mantém apenas `relevancia_estimada ≥ 0.6` ou impacto nuclear
- Comprime acessórios para `cabecalho_apenas`
- Remove despachos, intimações e certidões abaixo do limiar
- Fallback: `resumir` para peças não classificadas

---

## Como Usar

### CLI

```bash
python scripts/curar.py \
  --entrada envelope_segmentacao.json \
  --saida envelope_curadoria.json \
  --modo padrao
```

### Validação

```bash
python scripts/validar_saida.py \
  --arquivo envelope_curadoria.json \
  --schema assets/schema_saida.json
```

---

## Arquivos desta Skill

```
curador-relevancia/
├── SKILL.md
├── scripts/
│   ├── curar.py                      ← engine principal
│   ├── regras.py                     ← motor de regras por modo
│   ├── validar_saida.py              ← validação do envelope curado
│   └── gerar_exemplo.py             ← gerador de exemplos
├── references/
│   ├── dicionario_variaveis.md
│   ├── regras_padrao.md
│   ├── regras_sintetico.md
│   ├── politica_fallback.md
│   └── integracao_pipeline.md
└── assets/
    ├── schema_entrada.json           ← Envelope de Processo (entrada)
    ├── schema_saida.json             ← Envelope Curado (saída)
    ├── exemplo_entrada.json
    └── exemplo_saida.json
```

---

## Limites de Segurança Jurídica

> Esta skill realiza classificação operacional de relevância — **não realiza análise jurídica de mérito**.
> A decisão final sobre o que preservar em acervos com valor probatório é sempre do operador jurídico.
