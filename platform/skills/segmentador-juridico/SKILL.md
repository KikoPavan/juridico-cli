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

### 4. Descritores Compactos por Peça

Para cada peça identificada, retornar somente decisões compactas: `piece_id` (ou índice lógico),
`document_type`, `document_type_confidence`, limites de página canônicos ou aliases, `title` ou
`text_excerpt`, `relevancia_estimada`, anchors compactos e `process_number`, `event` e
`document_code` quando disponíveis. O runtime Python preenche texto integral, proveniência e
demais campos obrigatórios a partir do Markdown original antes da validação final.

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
9. **Não copiar texto completo:** nunca produzir `text`, `text_content` ou outro campo com a íntegra
   da peça; o modelo deve devolver apenas os descritores compactos usados para segmentação.

---

## Saída compacta do LLM

```json
{
  "pecas": [
    {
      "piece_id": "peca_001",
      "document_type": "peticao_inicial",
      "document_type_confidence": "high",
      "pages_start": 1,
      "pages_end": 18,
      "title": "Petição Inicial — Ação de Cobrança",
      "text_excerpt": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...",
      "anchors": [
        { "label": "cabecalho", "page": 1 },
        { "label": "PETIÇÃO INICIAL", "page": 1 },
        { "label": "pede deferimento", "page": 18 }
      ],
      "relevancia_estimada": 0.98
    }
  ]
}
```

Retorne somente o objeto JSON compacto, sem Markdown ou explicações adicionais.

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
