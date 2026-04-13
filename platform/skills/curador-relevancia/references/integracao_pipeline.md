# Guia de Integração no Pipeline — Curador de Relevância

> Skill: curador-relevancia | Versão: 1.1.0

---

## 1. Posição no Pipeline

```
PDF → convert → clean → segmentador-jurídico
  → [curador-relevancia]   ← ESTA SKILL
  → yaml-normalizador-jurídico → dispatcher → extr-* → json por peça
```

---

## 2. Contrato de Interface

### Entrada: Envelope de Processo (do `segmentador-jurídico`)

- **Formato:** JSON `{metadata, pecas[]}`
- **Schema:** `assets/schema_entrada.json`

### Saída: Envelope Curado (para `yaml-normalizador-jurídico`)

- **Formato:** JSON `{metadata, pecas[]}` — mesmas peças enriquecidas com campos curatoriais
- **Schema:** `assets/schema_saida.json`
- **Metadata:** original preservado + campos adicionados (`modo_aplicado`, `duracao_ms`, `versao_schema`, `gerado_por_curador`)

---

## 3. CLI

```bash
python skills/curador-relevancia/scripts/curar.py \
  --entrada output/segmentacao/envelope.json \
  --saida   output/curadoria/envelope_curado.json \
  --modo    padrao
```

### Validação

```bash
python skills/curador-relevancia/scripts/curar.py \
  --entrada envelope.json \
  --saida   envelope_curado.json && \
python skills/curador-relevancia/scripts/validar_saida.py \
  --arquivo envelope_curado.json \
  --schema  skills/curador-relevancia/assets/schema_saida.json
```

---

## 4. API Python

```python
from skills.curador_relevancia.scripts.curar import CuradorRelevancia

curador = CuradorRelevancia(modo="padrao")
envelope_curado = curador.processar(envelope_segmentacao)
```

---

## 5. Como o Normalizador Consome a Saída

O `yaml-normalizador-jurídico` **não recebe o envelope** — recebe uma **peça curada individual**
extraída de `pecas[i]` pelo orquestrador:

```python
for peca in envelope_curado["pecas"]:
    if peca["acao_curatorial"] != "remover":
        # invocar normalizador com peca flat
        normalizar(peca)
```

---

## 6. Regras de Enriquecimento de Metadata

O curador **preserva integralmente** o metadata original e adiciona:

| Campo | Valor |
|-------|-------|
| `modo_aplicado` | Modo efetivamente aplicado |
| `duracao_ms` | Tempo de processamento |
| `versao_schema` | `"1.1.0"` |
| `gerado_por_curador` | `"curador-relevancia"` |

Nenhum campo original é sobrescrito.

---

## 7. Formato de `audit_trail`

Sempre **array de AuditEntry**:

```json
[
  { "stage": "segmentador-juridico", "timestamp": "...", "action": "segmento_classificado", "notes": "..." },
  { "stage": "curador-relevancia", "timestamp": "...", "action": "decisao_curatorial_aplicada", "notes": "..." }
]
```

Cada skill acrescenta sua entrada ao array.
