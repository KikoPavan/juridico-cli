---
name: pdf-to-md
description: >
  Converte arquivos PDF textuais de qualquer domínio em Markdown bruto,
  preservando ao máximo a estrutura original do documento (títulos, listas,
  blocos de texto, marcadores de página) sem interpretar, classificar ou
  enriquecer o conteúdo. Use esta skill sempre que o usuário quiser converter
  um PDF para Markdown como primeira etapa de um pipeline documental, preparar
  PDFs para processamento posterior, ou mencionar termos como "converter PDF",
  "extrair texto de PDF", "pdf para markdown", "primeira etapa do pipeline",
  "transformar PDF em texto estruturado" — mesmo que não diga "pdf-to-md"
  explicitamente.
profile: local_preprocessing
version: 1.0.0
---

# pdf-to-md

Converte um arquivo PDF em Markdown bruto, preservando a estrutura
observável do documento para uso em etapas posteriores de um pipeline.

Esta skill é **agnóstica de domínio**: funciona para relatórios, manuais,
artigos, formulários, documentos administrativos, técnicos, corporativos
ou qualquer outro tipo de PDF textual.

---

## O que esta skill faz

- Recebe 1 arquivo PDF por execução
- Converte o conteúdo para um arquivo `.md`
- Preserva a ordem do conteúdo página a página
- Mapeia títulos e subtítulos detectados para headings Markdown
- Preserva listas quando detectáveis
- Insere anchors `[[Pág. N]]` entre páginas (configurável)
- Usa PaddleOCR como fallback para páginas escaneadas ou de baixa densidade textual
- Remove boilerplate e localizadores da contagem e exige 30 caracteres úteis por página
- Força fallback OCR quando boilerplate ou localizadores dominam o texto nativo
- Penaliza OCR composto apenas ou predominantemente por localizadores judiciais
- Emite opcionalmente um `conversion_report.md` com diagnóstico da conversão

## O que esta skill NÃO faz

- Não interpreta o conteúdo do documento
- Não classifica o domínio ou tema do PDF
- Não resume, não extrai entidades, não faz inferência
- Não insere YAML frontmatter
- Não realiza limpeza semântica especializada
- Não remove conteúdo sem critério explícito
- Não inventa dados ausentes no PDF original

---

## Contrato de entrada

| Parâmetro      | Tipo   | CLI flag        | Obrig.  | Descrição                                      |
|----------------|--------|-----------------|---------|------------------------------------------------|
| `input_pdf`    | `str`  | `--input`       | ✅      | Caminho absoluto ou relativo do PDF            |
| `output_md`    | `str`  | `--output`      | ✅      | Caminho do arquivo `.md` de saída              |
| `page_markers` | `bool` | `--no-markers`  | ❌      | Inserir `[[Pág. N]]` (padrão: ativo)           |
| `verbose`      | `bool` | `--verbose`     | ❌      | Log detalhado por página (padrão: desligado)   |
| `report`       | `bool` | `--report`      | ❌      | Gerar `conversion_report.md` (padrão: não)    |
| `engine`       | `str`  | `--engine`      | ❌      | Motor: `auto` \| `pdfminer` \| `pymupdf`       |

→ Especificação completa: [`assets/output_contract.md`](assets/output_contract.md)

---

## Contrato de saída

**Saída principal:**
```
<output_md>   → arquivo .md bruto convertido
```

**Saída auxiliar (se `--report`):**
```
conversion_report.md  → diagnóstico da conversão, no mesmo diretório de saída
```

→ Regras de conversão: [`assets/conversion_rules.md`](assets/conversion_rules.md)

---

## Fluxo de execução

```
PDF de entrada
     │
     ▼
[convert_pdf_to_md.py]
     │  motor: pymupdf → pdfminer (fallback automático)
     │
     ├─ extrai texto por página (PyMuPDF)
     ├─ remove boilerplate/localizadores da avaliação de texto útil
     ├─ avalia densidade textual (MIN_CHARS=30, PRINTABLE_RATIO=0.6)
     │    ├─ texto suficiente → usa texto nativo
     │    └─ texto insuficiente ou dominado por metadados → renderiza página → PaddleOCR
     ├─ avalia qualidade pós-OCR e registra `ocr_preprocessed`, `ocr_raw` ou `low_ocr_quality`
     ├─ insere `[[judicial_locator: ...]]` (ou marcador legado quando aplicável)
     ├─ detecta e mapeia headings → #, ##, ###
     ├─ preserva listas quando detectáveis
     └─ escreve <output_md>
          │
          ├─ (opcional) escreve conversion_report.md
          └─► [validate_output.py]  ← verifica contrato mínimo de saída
```

---

## Uso rápido (CLI)

```bash
# Conversão básica
python scripts/convert_pdf_to_md.py \
  --input  ~/devops/juridico-cli/var/input/pdf-to-md/documento.pdf \
  --output ~/devops/juridico-cli/var/output/pdf-to-md/documento.md

# Com relatório e log detalhado
python scripts/convert_pdf_to_md.py \
  --input  ~/devops/juridico-cli/var/input/pdf-to-md/documento.pdf \
  --output ~/devops/juridico-cli/var/output/pdf-to-md/documento.md \
  --report --verbose

# Executar exemplo de ponta a ponta
bash scripts/run_example.sh

# Empacotar a skill
bash scripts/package_skill.sh
```

---

## Scripts disponíveis

| Script                        | Descrição                                            |
|-------------------------------|------------------------------------------------------|
| `scripts/convert_pdf_to_md.py`| Conversor principal (CLI, determinístico, sem LLM)   |
| `scripts/validate_output.py`  | Valida o `.md` gerado contra o contrato de saída     |
| `scripts/run_example.sh`      | Teste ponta a ponta com documento de exemplo neutro  |
| `scripts/package_skill.sh`    | Empacota a skill em `.zip`                           |

---

## Posição no pipeline

```
[pdf-to-md]  →  [limpeza/normalização]  →  [extração/análise]
```

Esta skill é **exclusivamente pré-processamento de conversão**.
Etapas de limpeza, estruturação semântica ou extração de dados
pertencem às skills subsequentes.

Antes da extração JSON, o pipeline consumidor valida o documento completo com
limiar padrão configurável de 50 caracteres úteis. Documentos vazios ou apenas
com localizadores são interrompidos com `rejected: no_meaningful_content` e não
são enviados ao LLM; essa rejeição pertence ao consumidor, não ao conversor PDF.

---

## Limitações conhecidas

- PDFs escaneados sem PaddleOCR instalado resultam em páginas marcadas como `scanned_no_ocr`
- PDFs protegidos por senha não são suportados
- A detecção de títulos é heurística; documentos sem convenção tipográfica
  clara terão menos headings detectados
- Tabelas complexas são preservadas como texto plano (sem sintaxe de tabela MD)

---

## Referências internas

- [`assets/output_contract.md`](assets/output_contract.md)
- [`assets/conversion_rules.md`](assets/conversion_rules.md)
- [`references/dicionario_variaveis.md`](references/dicionario_variaveis.md)
- [`references/exemplo_entrada.md`](references/exemplo_entrada.md)
- [`references/exemplo_saida.md`](references/exemplo_saida.md)
