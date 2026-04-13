# Guia de Integração — segmentador-jurídico no Pipeline juridico-cli

**Versão:** 1.1.0

---

## 1. Posição no Pipeline

```
PDF → convert → clean → [segmentador-jurídico] → curador-relevância → yaml-normalizador-jurídico → dispatcher → extr-* → json por peça
```

---

## 2. Contrato de Dados

### 2.1 Saída: Envelope de Processo

O segmentador produz um **Envelope de Processo** JSON:

```json
{
  "metadata": {
    "processo_id": "0001234-12.2025.8.26.0000",
    "total_pecas": 4,
    "gerado_por": "segmentador-juridico",
    "timestamp": "2026-04-08T10:30:00Z",
    "source_file": "processo_0001234.pdf",
    "total_pages": 42,
    "ocr_quality": "medium",
    "schema_version": "1.1.0"
  },
  "pecas": [ ... ]
}
```

Campos por peça: `piece_id`, `document_type`, `document_type_confidence`, `pages_start`,
`pages_end`, `pages_total`, `title`, `summary`, `impacto_sentenca_proposto`, `text_excerpt`,
`text`, `anchors` (array de `{label, page}`), `observacoes`, `source_file`, `source_path`,
`source_sha256`, `process_group_id`, `origin_piece_index`, `relevancia_estimada`,
`confianca_classificacao`, `sinais_relevancia`, `flags`, `data_documento`, `autor`.

Schema completo: `assets/output-schema.json`.

### 2.2 Entregando ao `curador-relevancia`

O curador consome o Envelope de Processo diretamente:

```python
# segmentador → curador
curador_recebe = envelope_segmentador  # {metadata, pecas[]}
# Curador preserva metadata, enriquece cada peça com campos curatoriais
```

---

## 3. Validação Pós-Segmentação

```bash
python skills/segmentador-juridico/scripts/validate_output.py resultado_seg.json --verbose
```

---

## 4. Troubleshooting

| Problema | Causa Provável | Solução |
|----------|----------------|---------|
| `total_pecas ≠ len(pecas)` | Bug no preenchimento | Calcular `total_pecas = len(pecas)` |
| `piece_id` fora do padrão | Geração manual de IDs | Sequência `peca_001`, `peca_002`... |
| `nao_classificado` sem `observacoes` | Fallback não aplicado | Sempre preencher `observacoes` |
| `anchors` como array de strings | Formato legado | Usar `[{label, page}]` |
| `text` ausente | Apenas `text_excerpt` produzido | Produzir texto completo da peça |

---

## 5. Dependências

| Dependência | Uso | Instalação |
|-------------|-----|------------|
| Python ≥ 3.10 | Scripts de validação | Sistema |
| `jsonschema` | Validação formal | `pip install jsonschema` |
