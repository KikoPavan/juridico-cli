## Context

A função `_needs_ocr` em `convert_pdf_to_md.py` decide se uma página deve ser processada por PaddleOCR. Ela aplica dois critérios:

1. Contagem de caracteres após remoção de boilerplate (`< MIN_CHARS_FOR_TEXT`).
2. Proporção de caracteres imprimíveis (`< MIN_PRINTABLE_RATIO`).

O caso do `28_30_certidão.pdf` evidencia uma lacuna: o PDF tem camada textual com caracteres suficientes e imprimíveis, mas o texto está corrompido — palavras grudadas, espaçamento ausente, tokens incoerentes. Nenhum dos critérios atuais cobre esse padrão.

## Goals / Non-Goals

**Goals:**
- Adicionar uma função de pontuação de qualidade textual que identifique texto com palavras grudadas ou espaçamento anormal.
- Integrar essa pontuação em `_needs_ocr` como terceiro critério de fallback para OCR.
- Registrar no log/report por página o motivo do roteamento (`low_chars`, `low_printable`, `low_quality`, `pymupdf`, `ocr`).

**Non-Goals:**
- Não usar ML, classificadores ou LLMs para avaliação de qualidade.
- Não modificar `md-clean-markdown`, `md-frontmatter-yaml` ou `platform/skill-runtime`.
- Não iniciar qualquer extração jurídica ou estruturada.
- Não alterar a lógica de boilerplate (`_strip_boilerplate`) ou o limiar `MIN_CHARS_FOR_TEXT`.

## Decisions

### Decisão 1: Métricas heurísticas de qualidade textual

**Escolha:** Usar densidade de espaços e distribuição de comprimento de tokens como indicadores de texto corrompido.

**Métricas da função `_text_quality_score(text: str) -> float`:**
- **space_density**: caracteres por espaço (`len(text) / (spaces + 1)`). Prosa portuguesa normal: 5–10 chars/espaço. Texto grudado: >>15.
- **long_word_ratio**: proporção de "tokens" (split por espaço) com comprimento > 20 chars. Texto corrompido tende a ter alta proporção de tokens anormalmente longos.
- Score composto: `1.0 - clamp(long_word_ratio * peso_a + space_density_penalty * peso_b)`.

**Por que não usar entropy ou n-grams:** adiciona dependência de corpus de referência ou biblioteca NLP. Heurísticas de espaçamento são robustas, sem dependência externa, e diretamente observáveis no padrão do bug reportado.

**Alternativa considerada:** Verificar a proporção de transições maiúscula→minúscula sem espaço (indicativo de gluing). Descartada por ser frágil para siglas e acrônimos jurídicos frequentes.

### Decisão 2: Constante de limiar separada

**Escolha:** Introduzir `MIN_TEXT_QUALITY = 0.45` como constante explícita no topo do arquivo, ao lado de `MIN_CHARS_FOR_TEXT` e `MIN_PRINTABLE_RATIO`.

**Por quê:** Facilita calibração independente sem alterar outras decisões; segue o padrão já adotado no arquivo.

### Decisão 3: Log de motivo de roteamento

**Escolha:** `_needs_ocr` retornará uma tupla `(bool, str)` — flag e motivo (`"low_chars"`, `"low_printable"`, `"low_quality"`, `"ok"`). O chamador em `_extract_pymupdf` usará o motivo no log e no report.

**Alternativa considerada:** Adicionar variável global de contexto. Descartada — tupla é explícita e sem estado compartilhado.

### Decisão 4: Sem alteração no critério de boilerplate

O `_strip_boilerplate` permanece inalterado. A nova pontuação de qualidade opera sobre o texto **após** a remoção de boilerplate, na mesma posição que os critérios atuais.

## Risks / Trade-offs

- **Falso positivo em texto técnico legítimo**: documentos com muitas siglas longas ou URLs podem pontuar mal. Mitigação: calibrar `MIN_TEXT_QUALITY` com pelo menos 5 fixtures reais antes de definir o valor final.
- **Falso negativo em texto corrompido específico**: a heurística de espaços não cobre todos os tipos de corrupção (ex.: caracteres especiais intercalados). Aceitável para o escopo desta change; extensões futuras podem adicionar métricas.
- **OCR desnecessário degrada performance**: se o limiar for baixo demais, páginas válidas serão enviadas ao PaddleOCR, aumentando o tempo de processamento. Mitigação: threshold conservador (0.45) e teste de regressão com PDFs conhecidamente bons.

## Open Questions

- Valor final de `MIN_TEXT_QUALITY` depende de validação com fixtures reais. O valor `0.45` é ponto de partida; a task de implementação deve incluir step de calibração com pelo menos o caso `certidão.pdf` e um PDF digital limpo.
