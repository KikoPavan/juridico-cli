---
name: segmentador-juridico
version: "1.1.0"
skill_type: "llm"
description: >
  Leitor e Segmentador Jurídico estrutural: interpreta saída Markdown do pipeline convert/clean,
  identifica e delimita automaticamente as "peças lógicas" dentro de processos judiciais, autos
  digitalizados ou lotes documentais heterogêneos, e retorna um Envelope de Processo JSON
  ({metadata, pecas[]}) estruturado e pronto para consumo pelas próximas etapas do pipeline
  (curador-relevância, yaml-normalizador-jurídico, dispatcher de skill, extr-*).
  Use esta skill sempre que o usuário mencionar: segmentação de processo, identificar peças
  processuais, separar documentos jurídicos, classificar partes de um processo, rotear peças
  para skills especializadas, preparar acervo jurídico para extração.
  Pipeline: PDF → convert → clean → **segmentador-jurídico** → curador-relevância →
  yaml-normalizador-jurídico → dispatcher → extr-* → json por peça.
input_stage: "clean_markdown"
output_stage: "segmented_pieces"
tags:
  - segmentacao
  - classificacao
  - documento-juridico
  - pecas-processuais
  - pipeline
guardrails:
  - "Nunca inventar peças sem evidência textual"
  - "Dúvida → nao_classificado com observacoes"
  - "Rastreabilidade obrigatória por âncora de página"
  - "Nunca colapsar processo inteiro em peça única se há separação lógica"
  - "Respeitar schema output-schema.json v1.1.0"
---

# Segmentador Jurídico

## Papel no Pipeline

```
PDF → convert → clean → [segmentador-jurídico] → curador-relevância → yaml-normalizador-jurídico → dispatcher → extr-* → json por peça
```

Esta skill é a **terceira etapa** do pipeline `juridico-cli`. Recebe Markdown limpo com marcadores
de página e retorna um **Envelope de Processo** JSON — `{metadata, pecas[]}` — com peças lógicas
classificadas, rastreáveis e prontas para curadoria.

---

## Entrada Esperada

- **Markdown limpo** produzido pelo `clean` (encoding corrigido, ruído reduzido)
- **Marcadores de página** no formato: `<!-- page: N -->` ou `---\n**Página N**\n---`
- **Metadados opcionais** em YAML front matter: `source_file`, `total_pages`, `ocr_quality`

---

## Processo de Segmentação

### 1. Detecção de Âncoras

Varrer o documento em busca de sinais primários (alta confiança) e secundários (suporte):

**Sinais Primários:**
- Cabeçalhos formais: `PETIÇÃO INICIAL`, `CONTESTAÇÃO`, `RÉPLICA`, `SENTENÇA`, `DESPACHO`
- Fórmulas de endereçamento: `EXCELENTÍSSIMO`, `MERITÍSSIMO`, `MM. JUIZ`
- Termos de encerramento: `Nesses termos, pede deferimento`, `Publique-se. Intime-se.`
- Marcadores de autuação: `PROCESSO Nº`, `AUTOS Nº`, `PROTOCOLO Nº`

**Sinais Secundários:**
- Quebras de página + cabeçalho em maiúsculas
- Referências a partes processuais: `REQUERENTE`, `REQUERIDO`, `AUTOR`, `RÉU`
- Datas isoladas em linha com formatação `DD/MM/AAAA`
- Assinaturas e qualificações OAB

### 2. Classificação de Tipo

Aplicar o **Dicionário de Tipos** (ver `references/variable-dictionary.md`) por correspondência
de âncoras, contexto e posição no documento:

| Confiança | Critério |
|-----------|----------|
| `high` | 2+ sinais primários convergentes |
| `medium` | 1 sinal primário + 1+ secundário |
| `low` | apenas sinais secundários |
| `nao_classificado` | nenhum sinal suficiente ou contradição |

### 3. Delimitação de Fronteiras

- **Início:** primeira âncora primária detectada para a peça
- **Fim:** página anterior ao início da próxima peça (ou fim do documento)
- **Sobreposição:** quando ambígua, marcar ambas as peças com `observacoes` explicativa

### 4. Extração de Campos por Peça

Para cada peça identificada, extrair todos os campos definidos em `assets/output-schema.json`.
Inclusive: `text` (texto completo), `anchors` (array de `{label, page}`), campos de proveniência
(`source_file`, `source_path`, `source_sha256`, `process_group_id`, `origin_piece_index`) e
campos de análise (`relevancia_estimada`, `confianca_classificacao`, `sinais_relevancia`, `flags`).

---

## Regras Obrigatórias

1. **Não inventar peças.** Só criar entrada no JSON se houver evidência textual.
2. **Dúvida → `nao_classificado`.** Sempre com `observacoes` justificando.
3. **Rastreabilidade obrigatória.** Todo campo deve ter âncora de página verificável.
4. **Nunca colapsar o processo inteiro** em uma peça única se houver separação lógica identificável.
5. **OCR imperfeito:** tolerar ruído textual; usar sinais estruturais quando texto for ilegível.
6. **Compatibilidade:** o JSON de saída (Envelope de Processo) deve validar contra `assets/output-schema.json`.
7. **Foco:** segmentar e classificar. Não extrair campos jurídicos finais — isso é tarefa das `extr-*`.
8. **Âncoras como objetos:** produzir `anchors` como array de `{label, page}`, nunca como array de strings.
9. **Texto completo:** produzir `text` com o conteúdo integral da peça, não apenas `text_excerpt`.

---

## Saída: Envelope de Processo

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
  "pecas": [
    {
      "piece_id": "peca_001",
      "document_type": "peticao_inicial",
      "document_type_confidence": "high",
      "pages_start": 1,
      "pages_end": 18,
      "pages_total": 18,
      "title": "Petição Inicial — Ação de Cobrança",
      "summary": "Petição inicial de ação de cobrança...",
      "impacto_sentenca_proposto": "Peça fundante da pretensão autoral.",
      "text_excerpt": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...",
      "text": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO...\n[texto completo da peça]",
      "anchors": [
        { "label": "cabecalho", "page": 1 },
        { "label": "PETIÇÃO INICIAL", "page": 1 },
        { "label": "pede deferimento", "page": 18 }
      ],
      "observacoes": null,
      "source_file": "processo_0001234.pdf",
      "source_path": "/data/processos/2025/sp/processo_0001234.pdf",
      "source_sha256": "a3f5e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3",
      "process_group_id": "proc-2025-0001",
      "origin_piece_index": 0,
      "relevancia_estimada": 0.98,
      "confianca_classificacao": 0.99,
      "sinais_relevancia": ["objeto_processual", "pedido_expresso", "valor_causa"],
      "flags": { "prova_documental": false, "decisao_judicial": false },
      "data_documento": "2024-08-15",
      "autor": "Dr. Pedro Souza OAB/SP 654321"
    }
  ]
}
```

Seguido de **resumo técnico em Markdown** (ver seção abaixo).

---

## Resumo Técnico (Markdown — após o JSON)

Após o JSON, sempre incluir bloco Markdown com:

```markdown
## Resumo Técnico de Segmentação

### Lógica de Segmentação
[Como as fronteiras foram detectadas neste documento]

### Critérios de Classificação
[Quais sinais determinaram cada tipo]

### Regras de Fallback Aplicadas
[Se houve OCR ruim, ambiguidade, peças sem sinal primário]

### Limitações Identificadas
[Páginas ilegíveis, peças sobrepostas, incertezas remanescentes]
```

---

## Tratamento de Casos Especiais

| Situação | Conduta |
|----------|---------|
| OCR com >30% de ruído em uma página | Usar sinais estruturais; registrar em `observacoes` |
| Peça sem título explícito | Inferir título a partir do tipo + partes identificadas |
| Documento com apenas 1 peça | Retornar array com 1 elemento; não omitir JSON |
| Peças aninhadas | Criar peça filha com `piece_id` sufixado (`_a`, `_b`) |
| Tipo ambíguo | Usar o de maior confiança; registrar alternativa em `observacoes` |
| Sem marcadores de página | Estimar páginas por densidade textual; `ocr_quality: unknown` |

---

## Arquivos de Referência

- `references/tech-doc.md` — Documentação técnica detalhada
- `references/variable-dictionary.md` — Dicionário de tipos, variáveis e âncoras
- `assets/output-schema.json` — Schema JSON formal (v1.1.0)
- `assets/example-input.md` — Exemplo de entrada
- `assets/example-output.json` — Exemplo de saída completa (Envelope de Processo)
- `scripts/validate_output.py` — Validador da saída contra o schema
- `scripts/integration-guide.md` — Guia de integração no pipeline
