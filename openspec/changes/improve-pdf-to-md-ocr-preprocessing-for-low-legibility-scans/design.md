## Context

A skill `pdf-to-md` usa PyMuPDF para extração de texto nativo e cai para PaddleOCR quando a página não tem texto suficiente ou o texto tem qualidade baixa (`_text_quality_score < MIN_TEXT_QUALITY`). O caminho OCR atual renderiza a página como PNG e passa a imagem diretamente ao PaddleOCR sem qualquer pré-processamento. Para PDFs escaneados de baixa legibilidade — como a `procuração_Monica.pdf`, com digitalização manual, contraste pobre e possível inclinação — o resultado é texto inutilizável sem nenhum indicador de que a saída é ruim.

Pillow já é dependência declarada (`pillow>=12.0.0`). Não há OpenCV na matriz de versões do projeto.

## Goals / Non-Goals

**Goals:**

- Aplicar pré-processamento de imagem (escala de cinza, melhoria de contraste, binarização adaptativa) antes de invocar o PaddleOCR.
- Registrar em log o modo por página: `ocr_raw`, `ocr_preprocessed` ou `low_ocr_quality`.
- Verificar a qualidade do texto após OCR e marcar a página como `low_ocr_quality` quando o resultado permanece corrompido.
- Permitir comparação entre OCR sem e com pré-processamento via flag `--compare-ocr`.
- Preservar os marcadores `[[Pág. N]]` em todos os modos.
- Adicionar teste automatizado para o caminho `low_ocr_quality`.

**Non-Goals:**

- Deskew automático (requer OpenCV, ausente da matriz de versões).
- Alteração de `md-clean-markdown`, `md-frontmatter-yaml` ou `platform/skill-runtime`.
- Integração com outros engines OCR além do PaddleOCR.
- Extração jurídica estruturada.

## Decisions

### Decisão 1 — Usar apenas Pillow para pré-processamento

**Escolha:** Pillow (`PIL.Image`, `PIL.ImageFilter`, `PIL.ImageOps`).

**Alternativa descartada:** `opencv-python-headless` — mais poderoso para deskew e binarização adaptativa real, mas não está na matriz de versões do projeto e ampliaria o escopo.

**Motivo:** Pillow já é dependência declarada; permite conversão para escala de cinza, auto-contraste e limiar de binarização simples suficientes para melhorar legibilidade em escaneamentos com baixo contraste. Zero dependência nova.

### Decisão 2 — Pré-processamento sempre no caminho OCR

**Escolha:** O pré-processamento aplica-se a toda página que já entrou no caminho OCR (ou seja, após `_needs_ocr` retornar `True`). O OCR é executado sobre a imagem pré-processada. O modo é registrado como `ocr_preprocessed` quando pré-processamento foi aplicado com sucesso.

**Alternativa descartada:** Executar OCR primeiro sem pré-processamento e só re-executar com pré-processamento se a qualidade for ruim — duplicaria chamadas ao PaddleOCR e aumentaria o tempo de execução.

**Motivo:** Para scans de baixa qualidade, o pré-processamento sempre melhora ou mantém o resultado; o custo de executar duas vezes não se justifica para o caso geral.

### Decisão 3 — Flag `--compare-ocr` para diagnóstico

**Escolha:** Flag opcional `--compare-ocr` (ou variável `PDF_TO_MD_COMPARE_OCR=1`) que executa OCR também sobre a imagem raw (sem pré-processamento) e registra ambos os resultados no log de stderr para fins de comparação. Não afeta o output final.

**Motivo:** Permite diagnóstico e validação do benefício do pré-processamento sem tornar o fluxo principal mais lento.

### Decisão 4 — Placeholder `[low_ocr_quality]` para páginas irrecuperáveis

**Escolha:** Quando o resultado do OCR (com pré-processamento) tem `_text_quality_score < MIN_OCR_POST_QUALITY`, a página recebe o texto `[low_ocr_quality]` no output Markdown. O marcador `[[Pág. N]]` é preservado. O status da página é `low_ocr_quality`.

**Alternativa descartada:** Emitir o texto corrompido mesmo assim — o comportamento atual que queremos corrigir.

**Motivo:** É mais honesto e útil para downstream indicar explicitamente que a página não foi legível do que emitir texto inutilizável silenciosamente.

### Decisão 5 — Reutilizar `_text_quality_score` como avaliação pós-OCR

**Escolha:** O mesmo limiar `MIN_TEXT_QUALITY` (já existente) é usado para avaliar a qualidade do texto retornado pelo OCR. Uma constante separada `MIN_OCR_POST_QUALITY` pode ser definida se necessário para ajuste fino, mas começa com o mesmo valor.

**Motivo:** Evita proliferação de constantes e mantém critério consistente.

## Risks / Trade-offs

- **[Risco] Binarização pode degradar páginas com texto colorido ou fundo gradiente** → Mitigação: pré-processamento só ocorre para páginas que já precisam de OCR (baixa qualidade de texto nativo); páginas digitais não são afetadas.
- **[Risco] Placeholder `[low_ocr_quality]` resulta em página sem conteúdo útil** → Mitigação: é o comportamento correto — fingir sucesso com texto corrompido é pior do que sinalizar falha.
- **[Risco] `--compare-ocr` duplica chamadas ao PaddleOCR** → Mitigação: a flag é opcional e desativada por padrão; nunca ativa no fluxo de produção.
