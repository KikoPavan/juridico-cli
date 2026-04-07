> [!NOTE]
> **DOCUMENTO AUXILIAR OPERACIONAL**
> Descreve os estágios dos pipelines de processamento. Complementa, mas não substitui, o documento canônico da arquitetura.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Pipelines de Processamento de Dados — juridico-cli

Descreve todos os processos de conversão, limpeza e extração do repositório: o que cada etapa faz, de onde consome dados e o que produz.

---

## Visão Geral

O repositório possui **dois grupos de pipelines**:

| Grupo | Localização | Propósito |
|---|---|---|
| **data-processing** | `apps/data-processing/` | Documentos jurídicos do caso (processo, juntadas, imóveis) |
| **ingest** (legado) | `pipelines/ingest/` | Base jurídica (jurisprudência, leis, doutrina) para RAG |

Os dois grupos são independentes mas compartilham o mesmo repositório e ambiente.

---

## 1. Pipeline `apps/data-processing`

### Entrada e saída por etapa

```
[PDFs brutos]
      │
      ▼
┌─────────────────────────────────────────────┐
│  Etapa 1 — convert (PDF → Markdown)         │
│  Input : qualquer diretório com *.pdf       │
│  Output: var/input/md/*.md                  │
│  Formato: [[Pág. N]] por página             │
└─────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  Etapa 2 — clean (limpeza jurídica)         │
│  Input : var/input/md/*.md                  │
│  Output: var/staging/*_clean.md             │
│  Remove: cabeçalhos, rodapés, firmas, refs  │
└─────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  Etapa 3 — analyze (análise de regras)      │
│  Input : var/staging/*.md                   │
│  Output: var/staging/regras_propostas.txt   │
│  Gera  : frases repetidas para revisão      │
└─────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  Etapa 4 — collect (extração LLM)           │
│  Input : data/**/*.md  (collector_proc)     │
│          data/cad_obr/**/*.md (cad_obr)     │
│  Output: outputs/processo/01_collector/     │
│          outputs/juntada/01_collector/      │
│          outputs/cad_obr/01_collector/      │
└─────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  Etapa 5 — validate (validação de schema)   │
│  Executada dentro de cada job do collector  │
│  JSON Schema Draft 2020-12                  │
└─────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│  Etapa 6 — load (persistência + índice)     │
│  Output: var/artifacts/index_registry.json  │
└─────────────────────────────────────────────┘
```

### Comandos CLI

```bash
# Pipeline completo (etapas 2–6; etapa 1 separada)
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli run \
  --input var/input/md \
  --collector <proc|cad_obr>

# Etapa 1 isolada — PDF → Markdown
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli convert \
  --input <dir_pdfs> \
  --output var/input/md

# Etapa 2 isolada — limpeza
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli clean \
  --input var/input/md \
  --output var/staging

# Etapa 3 isolada — análise de regras
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli analyze \
  --input var/staging \
  --output var/staging
```

---

### Etapa 1 — `convert` (PDF → Markdown)

**Módulo**: `apps/data-processing/src/data_processing/converters/`

#### Estratégia híbrida por página

Para cada página do PDF:

1. **PyMuPDF** extrai o texto nativo (rápido, sem custo de API).
2. Se o texto tiver **menos de 150 caracteres** → página escaneada detectada:
   - A página é renderizada como JPEG (200 DPI).
   - O JPEG é enviado ao **Gemini OCR** para transcrição.
3. O resultado é gravado com âncora de página: `[[Pág. N]]`.

#### Pré-requisito

| Cenário | Requisito |
|---|---|
| PDF digital (texto selecionável) | Nenhum |
| PDF escaneado (imagem) | `GEMINI_API_KEY` no `.env` |

Se `GEMINI_API_KEY` estiver ausente, páginas escaneadas são **puladas com aviso** (não geram erro).

#### Formato de saída

```markdown
[[Pág. 1]]
Texto da página 1...

[[Pág. 2]]
Texto da página 2...
```

#### Classes e arquivos

| Arquivo | Classe/Função | Papel |
|---|---|---|
| `converters/markdown_engine/engine.py` | `Engine`, `EngineIO`, `EngineMove` | Orquestração em lote (lista PDFs, calcula destino, executa callback) |
| `orchestrator/stage_router.py` | `_convert_one_hybrid()` | Callback híbrido PyMuPDF + Gemini |
| `converters/gemini_ocr/adapter.py` | `GeminiClientAdapter` | Adapta google-genai para interface OpenAI (compatível com MarkItDown) |
| `converters/gemini_ocr/page_ocr.py` | `ocr_page(image_path)` | Transcreve uma página via Gemini |

---

### Etapa 2 — `clean` (Limpeza Jurídica)

**Módulo**: `apps/data-processing/src/data_processing/cleaners/clean_legal_docs.py`
**Classe**: `LegalDocCleaner`

#### O que remove

| Categoria | Exemplos |
|---|---|
| Metadados de autenticação | "Para conferir o original...", "Este documento é cópia..." |
| Cabeçalhos de tribunal | Nome do tribunal, comarca, vara, juíza |
| Referências de página | "fls. 12", "p. 5", "(fls. 12/15)" |
| Cabeçalho do escritório | "AV. PINHEIRO MACHADO, 1201 \| CENTRO" |
| Rodapé do escritório | "BAGAGLI & MORENO ADVOCACIA", endereço, telefone |
| Assinaturas | Nome + número OAB |
| Excesso de espaço | 3+ quebras de linha, 2+ espaços consecutivos |

#### O que preserva

- Estrutura legal: `Art. N`, `§ N`, `Inciso X`, `Alínea a)`
- Conteúdo jurídico integral do documento
- Encoding corrigido (UTF-8, acentuação)

#### Input / Output

```
Input : <dir>/*.md  (ou *.txt)
Output: <dir_out>/<stem>_clean.md
```

---

### Etapa 3 — `analyze` (Análise de Regras)

**Módulo**: `apps/data-processing/src/data_processing/rule_analysis/analisador_de_regras.py`
**Classe**: `GeradorDeRegras`

#### O que faz

Varre todos os `.md` e `.txt` do diretório de entrada, conta linhas repetidas e gera um arquivo de regras propostas para revisão manual.

#### Parâmetros

| Parâmetro | Padrão | Significado |
|---|---|---|
| `min_ocorrencias` | 2 | Mínimo de repetições para sugerir remoção |
| `min_comprimento` | 25 | Mínimo de caracteres por linha |

#### Input / Output

```
Input : <dir>/**/*.md
Output: <dir_out>/regras_propostas.txt
```

Formato do arquivo de saída:

```
# PROPOSED CLEANING RULES
# Review and remove lines that should NOT be cleaned.

# [Found 15 times]
AV. PINHEIRO MACHADO, 1201 | CENTRO

# [Found 15 times]
CEP 18705.370 | AVARÉ | SP...
```

---

### Etapa 4 — `collect` (Extração LLM)

Dois collectors independentes, ambos baseados em Gemini. Cada um lê arquivos Markdown de `data/`, extrai estrutura em JSON e valida contra schema.

#### collector_proc — Documentos Processuais

**Config**: `apps/data-processing/src/data_processing/collectors/collector_proc/config.yaml`
**Modelo**: `gemini-2.0-flash` (temp 0.1)

##### Estrutura de input esperada

```
data/
├── processo/
│   └── **/*.md              # Documentos do processo (N:1 → consolidated)
└── juntada/
    ├── procuracao/
    │   └── **/*.md          # Procuração (1:1 por arquivo)
    ├── cabecalho_processo/
    │   └── **/*.md
    ├── peticao_processo/
    │   └── **/*.md
    ├── contestacao_processo/
    │   └── **/*.md
    ├── decisao_processo/
    │   └── **/*.md
    └── mandato_processo/
        └── **/*.md
```

##### Jobs e saídas

| Job | Input | Output | Modo |
|---|---|---|---|
| Juntada — procuracao | `data/juntada/procuracao/**/*.md` | `outputs/juntada/01_collector/collector_out_juntada_procuracao_<stem>.json` | 1:1 |
| Juntada — cabecalho | `data/juntada/cabecalho_processo/**/*.md` | `outputs/juntada/01_collector/collector_out_juntada_cabecalho_<stem>.json` | 1:1 |
| Juntada — peticao | `data/juntada/peticao_processo/**/*.md` | `outputs/juntada/01_collector/collector_out_juntada_peticao_<stem>.json` | 1:1 |
| Juntada — contestacao | `data/juntada/contestacao_processo/**/*.md` | `outputs/juntada/01_collector/collector_out_juntada_contestacao_<stem>.json` | 1:1 |
| Juntada — decisao | `data/juntada/decisao_processo/**/*.md` | `outputs/juntada/01_collector/collector_out_juntada_decisao_<stem>.json` | 1:1 |
| Juntada — mandato | `data/juntada/mandato_processo/**/*.md` | `outputs/juntada/01_collector/collector_out_juntada_mandato_<stem>.json` | 1:1 |
| Processo consolidated | `data/processo/**/*.md` | `outputs/processo/01_collector/collector_out_processo_consolidated.json` | N:1 |

##### Front-matter obrigatório nos arquivos MD

Os arquivos em `data/` precisam ter YAML front-matter:

```yaml
---
document_type: procuracao         # roteamento para skill/schema correto
skill_key: procuracao
target_schema: schemas/procuracao.schema.json
source_id: procuracao_Juraci_para_Francisco
source_sha256: <hash SHA256 do conteúdo>
source_filename: procuracao_Juraci_para_Francisco.md
language: pt-BR
created_at: 2026-01-15T00:00:00Z
case_id: 1234567-89.2020.8.26.0000  # opcional; agrupa para consolidação
---
```

---

#### collector_cad_obr — Documentos de Imóvel (CAD-OBR)

**Config**: `apps/data-processing/src/data_processing/collectors/collector_cad_obr/config.yaml`
**Modelo**: `gemini-2.5-flash` (temp 0.1, max 65536 tokens)

##### Estrutura de input esperada

```
data/
└── cad_obr/
    ├── escritura_imovel/
    │   └── **/*.md          # Escritura/matrícula do imóvel
    ├── contrato_social/
    │   └── **/*.md          # Contrato social da empresa
    └── escritura_hipotecaria/
        └── **/*.md          # Escritura hipotecária
```

##### Jobs e saídas

| Job | Input | Output | Modo |
|---|---|---|---|
| Escritura de imóvel | `data/cad_obr/escritura_imovel/**/*.md` | `outputs/cad_obr/01_collector/escritura_imovel/collector_out_escritura_imovel_<stem>.json` | 1:1 |
| Contrato social | `data/cad_obr/contrato_social/**/*.md` | `outputs/cad_obr/01_collector/contrato_social/collector_out_contrato_social_<stem>.json` | 1:1 |
| Escritura hipotecária | `data/cad_obr/escritura_hipotecaria/**/*.md` | `outputs/cad_obr/01_collector/escritura_hipotecaria/collector_out_escritura_hipotecaria_<stem>.json` | 1:1 |

---

### Etapa 6 — `load` (Índice de Auditoria)

**Módulo**: `apps/data-processing/src/data_processing/loaders/index_registry.py`
**Arquivo**: `var/artifacts/index_registry.json`

Registra cada execução:

```json
{
  "source_id": "var/input/md",
  "collector": "proc",
  "output_path": "outputs/...",
  "status": "ok",
  "processed_at": "2026-03-22T..."
}
```

---

## 2. Pipeline `pipelines/ingest` (Base Jurídica)

Pipeline **separado** que converte e indexa a biblioteca jurídica (leis, jurisprudência, doutrina) para uso em RAG. Não faz parte do fluxo de documentos do caso.

### pdf_convert — PDF → Markdown (por perfil)

**Entry**: `pipelines/ingest/pdf_convert/run.py`

Três perfis, cada um com regras específicas de normalização:

| Perfil | Input | Output | Especificidade |
|---|---|---|---|
| `bj_doutrina` | `input/base_juridica/bj_doutrina/input_pdfs/` | `outputs/ingest/bj_doutrina/01_md/` | Textos doutrinários |
| `bj_juris_stj` | `input/base_juridica/bj_juris_stj/input_pdfs/` | `outputs/ingest/bj_juris_stj/01_md/` | Jurisprudência STJ com seções canônicas |
| `bj_leis` | `input/base_juridica/bj_leis/00_pdf/` | `outputs/ingest/bj_leis/01_md/` | Leis com normalização de artigos |

```bash
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_juris_stj --mode md_only

# bj_leis requer normalização extra após conversão
uv run python pipelines/ingest/pdf_convert/profiles/bj_leis/normalize_md.py \
  --in outputs/ingest/bj_leis/01_md --inplace
```

### md_rag — Markdown → Chunks RAG

**Entry**: `pipelines/ingest/md_rag/run.py`

Consome os `.md` produzidos pelo `pdf_convert` e gera chunks para indexação vetorial (Qdrant).

| Artefato | Caminho | Conteúdo |
|---|---|---|
| Raw JSON | `outputs/ingest/<perfil>/02_json/raw/<stem>.raw.json` | Listagem de páginas + metadados |
| RAG chunks | `outputs/ingest/<perfil>/02_json/rag/<stem>.rag.json` | Seções + chunks com referência de página |
| QA pairs | `outputs/ingest/<perfil>/03_report/qa/<stem>.qa.json` | Dataset de perguntas e respostas |
| Report | `outputs/ingest/<perfil>/03_report/logs/<stem>.md_rag.report.md` | Log de processamento |

```bash
uv run python pipelines/ingest/md_rag/run.py --profile bj_juris_stj
```

Seções canônicas do perfil `bj_juris_stj`:

| Seção | Política de chunk |
|---|---|
| EMENTA | `SINGLE` — um chunk inteiro |
| VOTO | `AUTO` — chunks de 800–1500 chars |
| TERMO_DE_JULGAMENTO | `AUTO` — chunks de 500–1500 chars |
| AUTUACAO | `AUTO` — chunks de 500–1500 chars |

---

## 3. Mapa de Diretórios

### Input

```
data/                            # Documentos do caso (alimentam collectors)
├── processo/**/*.md
├── juntada/
│   ├── procuracao/**/*.md
│   ├── cabecalho_processo/**/*.md
│   ├── peticao_processo/**/*.md
│   ├── contestacao_processo/**/*.md
│   ├── decisao_processo/**/*.md
│   └── mandato_processo/**/*.md
└── cad_obr/
    ├── escritura_imovel/**/*.md
    ├── contrato_social/**/*.md
    └── escritura_hipotecaria/**/*.md

input/base_juridica/             # PDFs da biblioteca jurídica (alimentam ingest)
├── bj_doutrina/input_pdfs/
├── bj_juris_stj/input_pdfs/
└── bj_leis/00_pdf/
```

### Intermediário

```
var/
├── input/md/                    # MDs convertidos (saída do convert, entrada do clean)
└── staging/                     # MDs limpos + regras propostas (saída do clean/analyze)
```

### Output Final

```
outputs/
├── processo/01_collector/       # Extração do processo consolidada
├── juntada/01_collector/        # Extração das juntadas (1 JSON por arquivo)
├── cad_obr/01_collector/        # Extração dos documentos de imóvel
├── ingest/
│   ├── bj_juris_stj/02_json/    # Chunks RAG de jurisprudência
│   ├── bj_doutrina/02_json/     # Chunks RAG de doutrina
│   └── bj_leis/02_json/         # Chunks RAG de leis
└── legal/
    └── law_pack_v1.json          # Pacote normativo (entrada do firac-cli e law-cli)

var/artifacts/
└── index_registry.json          # Auditoria de execuções
```

---

## 4. Dependências entre Pipelines

```
[PDFs do caso]
      │
      │  convert (data-processing)
      ▼
[var/input/md/]
      │
      │  clean + analyze (data-processing)
      ▼
[var/staging/]
      │
      │  Os collectors leem data/ diretamente (não var/staging/)
      │  Os MDs em data/ devem ser copiados/movidos manualmente ou
      │  produzidos por outro processo (ex: convert salvo diretamente em data/)
      ▼
[collect → validate → load]
      │
      ▼
[outputs/processo/, outputs/juntada/, outputs/cad_obr/]
      │
      │  Entrada dos agentes downstream
      ▼
[firac-cli, law-cli, case-law-cli, petition-cli]

---

[PDFs da biblioteca jurídica]
      │
      │  pipelines/ingest/pdf_convert (separado)
      ▼
[outputs/ingest/*/01_md/]
      │
      │  pipelines/ingest/md_rag
      ▼
[outputs/ingest/*/02_json/rag/]  →  Qdrant (indexação vetorial)
      │
      ▼
[case-law-cli usa Qdrant para busca semântica]
```

---

## 5. Observações Importantes

### Alimentando os collectors

Os collectors leem de `data/`, não de `var/staging/`. Para alimentar um job:

1. Converta o PDF: `cli.py convert --input <dir_pdf> --output var/input/md`
2. Limpe se necessário: `cli.py clean --input var/input/md`
3. Mova o MD limpo para a subpasta correta de `data/`:
   - `data/juntada/procuracao/` para procurações
   - `data/processo/` para documentos do processo
   - `data/cad_obr/escritura_imovel/` para escrituras
4. Adicione o YAML front-matter ao arquivo MD (obrigatório)
5. Execute o collector: `cli.py run --input var/input/md --collector proc`

### PDFs escaneados

O conversor híbrido detecta páginas escaneadas automaticamente (< 150 chars extraídos). A variável `GEMINI_API_KEY` deve estar definida no `.env` para que o OCR funcione. Sem ela, páginas escaneadas são ignoradas com aviso.

### Aviso `Both GOOGLE_API_KEY and GEMINI_API_KEY are set`

A biblioteca `google-genai` prioriza `GOOGLE_API_KEY` quando ambas estão definidas. Para evitar o aviso, remova `GOOGLE_API_KEY` do `.env` e mantenha apenas `GEMINI_API_KEY`.
