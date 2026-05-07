## Context

A skill `pdf-to-md` tem o código de integração PaddleOCR escrito em `convert_pdf_to_md.py` com lazy-loading (`_get_paddle_ocr()`). O PaddleOCR não está declarado em `pyproject.toml` nem instalado no ambiente. As dependências atuais incluem `pymupdf>=1.26.6` e `pillow>=12.0.0`, que são pré-requisitos do PaddleOCR. A versão do PaddleOCR está marcada como `A definir` na matriz de versões do projeto.

## Goals / Non-Goals

**Goals:**
- Declarar PaddleOCR como dependência de grupo opcional `ocr` em `pyproject.toml`
- Validar a compatibilidade operacional com Python 3.12 e registrar versão real
- Cobrir o caminho OCR com teste E2E determinístico na skill
- Atualizar documentação operacional para refletir estado validado

**Non-Goals:**
- Suporte a GPU (apenas CPU, alinhado ao perfil `local_preprocessing`)
- Migração do código de integração já existente em `convert_pdf_to_md.py`
- Alteração da lógica de heurística de densidade textual
- Integração com Gemini OCR ou outros motores

## Decisions

### Decisão 1: Grupo de dependência `ocr` (opcional), não dependência principal

PaddleOCR tem instalação pesada (~1 GB com modelos) e requer `paddlepaddle` como backend. Torná-la obrigatória bloquearia deploys onde OCR não é usado. A abordagem adotada é um grupo `[dependency-groups] ocr` no `pyproject.toml`, instalável com `uv sync --group ocr`.

**Alternativa considerada:** dependência principal — descartada pelo impacto no tempo de instalação e em ambientes sem uso OCR.

### Decisão 2: Versão do PaddleOCR a ser determinada pela validação, não pré-definida

A regra do projeto proíbe inventar versões. O fluxo correto é: instalar `paddleocr` sem pin, executar o teste E2E de validação, capturar a versão instalada, registrar em `project_version_matrix.md`. O pyproject.toml declarará `paddleocr>=2.7` como restrição mínima verificável.

### Decisão 3: Teste E2E via PNG sintético, sem PDF externo

O script `test_ocr_path.py` gera uma imagem PNG com texto via `Pillow` (já instalado), envia ao `_run_paddle_ocr()` e verifica que o texto retornado contém as palavras conhecidas. Isso elimina dependência de arquivo PDF externo e torna o teste reproduzível.

## Risks / Trade-offs

- [Risco: Compatibilidade Python 3.12] PaddleOCR 2.7.x com paddlepaddle ≥ 2.6.1 tem suporte Python 3.12 declarado, mas pode ter issues com dependências transitivas (e.g., `distutils` removido). → Mitigação: executar validação no ambiente real antes de fixar versão.

- [Risco: Tempo de primeiro download] PaddleOCR baixa modelos na primeira inicialização (~200 MB para `lang="pt"`). → Mitigação: documentar no `SKILL.md` e no runbook; o lazy-loading já presente evita isso em execuções sem páginas escaneadas.

- [Trade-off: `lang="pt"` vs `lang="en"`] O parâmetro atual usa `lang="pt"`, mas o modelo português no PaddleOCR é baseado em latin e tem qualidade inferior ao `en`. → Aceito como está; mudança de parâmetro é fora do escopo desta change.
