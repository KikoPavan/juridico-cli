---
project_name: juridico-cli
user_name: Kiko
date: 2026-04-06
sections_completed: ['technology_stack', 'directory_structure', 'code_conventions', 'runtime', 'registries', 'pipelines', 'dependencies', 'non_operational_artifacts']
existing_patterns_found: 12
---

# Project Context — juridico-cli

Resumo técnico do estado observável do projeto. Baseado em leitura direta dos arquivos em 2026-04-06.

---

## Stack

| Componente | Versão / Fonte | Observação |
|---|---|---|
| Python | >= 3.12 | `pyproject.toml` |
| LLM remoto | `google-genai>=0.3.3` | Gemini via API |
| LLM local | llama.cpp em Docker | imagem `ghcr.io/ggml-org/llama.cpp:server`, opt-in via profile `local-llm` |
| PDF | `pymupdf>=1.26.6`, `pdfplumber>=0.11.7`, `pypdf>=6.9.2` | 3 libs de PDF coexistem |
| OCR | `pytesseract>=0.3.13`, `pdf2image>=1.17.0`, `pillow>=12.0.0` | OCR local + Gemini OCR para páginas escaneadas |
| Vector store | `qdrant-client>=1.16.2` | Qdrant v1.16.0 em Docker |
| Embeddings | `sentence-transformers>=5.2.3` | Modelo implícito 768 dims (cosine) |
| CLI | `typer>=0.20.0`, `rich>=14.2.0` | Framework CLI principal |
| Validação | `jsonschema>=4.25.1` | Draft202012Validator |
| LangGraph | `langgraph>=1.0.5`, `langchain-core>=1.2.6` | Presentes, uso não confirmado no código ativo |
| Dados | `duckdb>=1.4.3`, `pandas>=3.0.1` | Presentes |
| Misc | `markitdown>=0.1.3`, `pyyaml>=6.0.3`, `python-dotenv>=1.0.0`, `chardet>=5.2.0`, `reportlab>=4.4.10` | |
| Dev | `pytest>=9.0.2`, `ruff>=0.14.10`, `types-pyyaml>=6.0.12.20250915` | |

Gerenciador de pacotes: **uv** (`uv.lock` presente).

---

## Estrutura de Diretórios

```
juridico-cli/
├── apps/data-processing/          # Módulo operacional único
│   ├── src/data_processing/
│   │   ├── cli.py                 # CLI Typer (5 comandos)
│   │   ├── extractor.py           # DataExtractorApp V1.1
│   │   ├── orchestrator/          # PipelineRunner + stage_router
│   │   ├── converters/            # markdown_engine + gemini_ocr
│   │   ├── cleaners/              # LegalDocCleaner
│   │   ├── collectors/            # collector_cad_obr + collector_proc
│   │   ├── rule_analysis/         # GeradorDeRegras
│   │   ├── validation/            # Schema validation
│   │   └── loaders/               # IndexRegistry, json_store, qdrant_loader
│   └── tests/
├── platform/
│   ├── skill-runtime/             # Dispatcher + bundle_loader + registries YAML
│   ├── skills/                    # 15 skills (SKILL.md + assets/ + references/ + scripts/)
│   ├── memory-and-experiences/    # mem0_adapter.py + experience_rewriter.py
│   └── continuous-learning/       # .gitkeep
├── packages/
│   ├── shared-llm/                # LLMClient (Gemini + local + dummy)
│   ├── shared-schemas/            # 6 schemas JSON com anchoring
│   ├── shared-core/               # .gitkeep
│   ├── shared-legal/              # .gitkeep
│   └── shared-utils/              # .gitkeep
├── infra/
│   ├── docker/docker-compose.yml  # Qdrant + llama.cpp
│   ├── qdrant/config.yaml
│   └── env/.env.example
├── var/                           # input/, staging/, output/, logs/, cache/, artifacts/, backups/
├── pipelines/                     # Legado (cad_obr/, ingest/)
├── agents/                        # Legado congelado (8 subdirs)
├── scripts/                       # 15 scripts utilitários
├── docs/architecture/             # Documento mestre + estado real consolidado
└── pyproject.toml
```

### Diretórios fora da estrutura canônica (legado ou auxiliares)

`base_juridica/`, `data/`, `outputs/`, `input/`, `logs/`, `artifacts/`, `backup/`, `backups/`, `tools/`, `templates/`, `prompts/`, `policies/`, `mcp-server-cad_obr/`, `docs_iplt/`, `manual_User/`, `arq-js/`, `arq-md/`, `.agent/` (tooling de terceiros, ~1500 arquivos).

---

## Convenções de Código

### Imports
- **stdlib primeiro**, **terceiros segundo**, **locais terceiro** (observado no código existente).
- Imports locais dentro de funções (lazy import) são usados para evitar carga desnecessária: `from .extractor import DataExtractorApp` dentro de comandos Typer.
- Dynamic loading de módulos via `importlib.util.spec_from_file_location` é o padrão para carregar `skill_dispatcher.py` e `bundle_loader.py` — **não há importação direta via pacote Python**.

### Nomenclatura
- **Arquivos**: `snake_case.py` (ex: `stage_router.py`, `clean_legal_docs.py`).
- **Classes**: `PascalCase` (ex: `PipelineRunner`, `DataExtractorApp`, `LegalDocCleaner`).
- **Funções/métodos**: `snake_case` (ex: `run_convert_stage`, `run_extraction`).
- **Variáveis**: `snake_case` (ex: `input_path`, `collector_name`).
- **Diretórios de skill**: `kebab-case` (ex: `extr-contrato-social`, `md-clean-markdown`).
- **Diretórios Python**: `snake_case` (ex: `rule_analysis`, `markdown_engine`).

### Estrutura de módulos
- Cada submódulo em `data_processing/` tem seu próprio `__init__.py`.
- CLI usa **lazy import** dentro de cada comando `@app.command()` — os imports ficam dentro da função, não no topo do arquivo.
- Dataclasses são usadas para contratos de resultado (`ConversionResult`, `PipelineResult`, etc).

### Type hints
- `pathlib.Path` preferido sobre `str` para caminhos em código novo (`stage_router.py`, `pipeline_runner.py`).
- `str` ainda usado em código mais antigo (`extractor.py`).
- Type hints com `typing.List`, `typing.Dict`, `typing.Optional` (sintaxe pré-3.10 em alguns arquivos).
- `Literal` usado para union de strings tipadas (`CollectorName = Literal["cad_obr", "proc"]`).

### Linting
- **Ruff** configurado com `line-length = 88`, mas **todas as regras ignoradas** (`ignore = ["ALL"]`).
- Não há formatação automática ativa no momento.

### Testes
- `pytest` configurado como dev dependency.
- Testes em `apps/data-processing/tests/` e `tests/test_smoke_syntax.py`.
- Sem evidência de CI/CD configurado.

### Commits
- README.md declara: código em **inglês**, commits em **inglês** (Conventional Commits), comunicação em **pt-BR**.

---

## Runtime Principal

### Skill Dispatcher (`platform/skill-runtime/skill_dispatcher.py`)

Ponto único de despacho. Fluxo:

1. Recebe `bundle_id` (ex: `extr-contrato-social`)
2. Busca configuração em `skill_registry.yaml`
3. Resolve profile LLM em `llm_registry.yaml`
4. `BundleLoader` carrega `SKILL.md` (frontmatter YAML + body) + injeta `_shared/extraction-base.md` + schema JSON local
5. Retorna dict: `{system_prompt, skill_config, llm_profile, bundle_id}`

### Bundle Loader (`platform/skill-runtime/bundle_loader.py`)

- Entry point canônico: `SKILL.md`
- Parseia frontmatter YAML entre delimitadores `---`
- Injeta `_shared/extraction-base.md` como regra transversal (prefixo ao body)
- Carrega `schema.json` local se existir
- API dupla: `load_bundle()` retorna `(prompt, frontmatter)`; `load_bundle_payload()` retorna dict consolidado

### Dynamic module loading

O projeto **não usa imports Python diretos** entre `apps/` e `platform/`. O carregamento é feito via `importlib.util.spec_from_file_location` com caminhos relativos. Isso significa que:

- Skills e runtime são carregados dinamicamente por caminho de arquivo
- Não há verificação estática de tipos entre módulos carregados dinamicamente
- Erros de import só aparecem em runtime

### DataExtractorApp (`apps/data-processing/src/data_processing/extractor.py`)

- Usa `SkillDispatcher` via dynamic loading
- Lê de `var/input/md/`, escreve em `var/output/`
- **Usa `DummyLLMClient`** como cliente LLM — retorna dados mock, não chama API real

---

## Registries

### `skill_registry.yaml` — 13 skills registradas

| Skill | Profile | Schema |
|---|---|---|
| extr-contrato-social | high_reasoning | contrato_social.schema.json |
| extr-escritura-imovel | large_context | escritura_imovel.schema.json |
| extr-escritura-hipotecaria | high_reasoning | escritura_hipotecaria.schema.json |
| extr-cabecalho-processo | fast_extraction | cabecalho_processo.schema.json |
| extr-mandato-processo | high_reasoning | mandato_processo.schema.json |
| extr-processo | large_context | processo.schema.json |
| extr-contestacao-processo | high_reasoning | contestacao_processo.schema.json |
| extr-decisao-processo | large_context | decisao_processo.schema.json |
| extr-peticao-processo | high_reasoning | peticao_processo.schema.json |
| extr-procuracao | fast_extraction | procuracao.schema.json |
| pdf-to-md | local_preprocessing | — |
| md-clean-markdown | local_preprocessing | — |
| md-frontmatter-yaml | local_preprocessing | — |

**Skills no disco mas não registradas:** `jus-breve`, `jus-diagnose`

### `llm_registry.yaml` — 2 execution classes, 4 profiles

| Execution class | Provider | Models |
|---|---|---|
| gemini_api | gemini (API) | gemini-2.5-flash (1M ctx), gemini-2.5-pro (1M ctx) |
| llama_cpp_local | llama_cpp (Docker) | llama-3.2-3b-instruct (128k ctx) |

| Profile | Model | Uso |
|---|---|---|
| high_reasoning | gemini-2.5-pro | Tarefas jurídicas complexas |
| fast_extraction | gemini-2.5-flash | Extrações padronizadas |
| large_context | gemini-2.5-flash | Documentos integrais |
| local_preprocessing | llama-3.2-3b-instruct | Pré-processamento local |

Fallback: `gemini-2.5-flash`

---

## Pipelines

### Pipeline `data-processing` (6 etapas)

```
convert → clean → analyze → collect → validate → load
```

| Etapa | Implementação | Descrição |
|---|---|---|
| **convert** | `stage_router.run_convert_stage()` | PDF→Markdown via PyMuPDF + Gemini OCR para páginas escaneadas (< 150 chars) |
| **clean** | `LegalDocCleaner.clean_batch()` | Limpeza de Markdown |
| **analyze** | `GeradorDeRegras.analisar_diretorio()` | Detecção de frases repetidas (min 2 ocorrências, min 25 chars) |
| **collect** | `run_collect_stage()` | Dispatch para `collector_cad_obr` ou `collector_proc` |
| **validate** | Interno a cada collector | Validação de schema/contrato |
| **load** | `IndexRegistry.register()` + `json_store` | Persistência + update do índice |

### Comandos CLI

```
data-processing run      # Pipeline completo
data-processing convert  # Só conversão
data-processing clean    # Só limpeza
data-processing analyze  # Só análise
data-processing extract  # Extração via skill (bundle -b + input -i)
```

### Pipeline genérico (3 skills)

```
pdf-to-md → md-clean-markdown → md-frontmatter-yaml
```

Skills criadas e registradas, profile `local_preprocessing`. Execução via skill dispatcher.

---

## Dependências Instaladas

Todas listadas em `pyproject.toml` e travadas em `uv.lock`.

**Runtime (22):** markitdown, google-genai, pdf2image, pdfplumber, pymupdf, typer, rich, jsonschema, langgraph, langchain-core, duckdb, qdrant-client, sentence-transformers, chardet, pypdf, reportlab, pytesseract, pillow, pandas, pyyaml, python-dotenv

**Dev (3):** pytest, ruff, types-pyyaml

**Dependências ausentes no pyproject.toml mas importadas em código:**
- `mem0` — importada em `platform/memory-and-experiences/mem0_adapter.py`
- `turboquant` — importada em `platform/memory-and-experiences/mem0_adapter.py`

---

## Artefatos Ausentes ou Não Operacionais

| Artefato | Estado | Observação |
|---|---|---|
| `mem0_adapter.py` | Presente, não executável | Importa `mem0` e `turboquant` — dependências não instaladas |
| `experience_rewriter.py` | Presente, stub trivial | 4 linhas, sem integração real |
| TurboQuant | Ausente | Nenhum código ou diretório encontrado |
| RLM | Ausente | Nenhum código ou diretório encontrado |
| `apps/legal-research/` | Ausente | Módulo previsto no documento mestre, não criado |
| `shared-core/` | Vazio | `.gitkeep` apenas |
| `shared-legal/` | Vazio | `.gitkeep` apenas |
| `shared-utils/` | Vazio | `.gitkeep` apenas |
| `DataExtractorApp` | Presente, usa LLM dummy | `DummyLLMClient` — não integra com Gemini API real |
| `platform/continuous-learning/` | Vazio | `.gitkeep` apenas — expansão futura prevista |
| 10 de 15 skills | Sem scripts de validação | Depende 100% do LLM sem validação automatizada |

---

## Regras Não Óbvias para Agentes

1. **Runtime não é importável via Python packages** — `skill_dispatcher.py` e `bundle_loader.py` são carregados via `importlib.util` com caminho de arquivo. Não crie `__init__.py` em `platform/skill-runtime/` sem necessidade explícita.

2. **SKILL.md é o entry point canônico** — todo skill bundle é resolvido pelo arquivo `SKILL.md`. Frontmatter YAML entre `---` é parseado automaticamente. O body é concatenado com `_shared/extraction-base.md`.

3. **Lazy imports no CLI** — comandos Typer fazem imports dentro da função, não no topo do arquivo. Siga esse padrão para evitar carga desnecessária de módulos.

4. **3 libs de PDF coexistem** — `pymupdf`, `pdfplumber` e `pypdf` estão instaladas. `pymupdf` (fitz) é a usada no conversor principal.

5. **Path vs str** — código novo usa `pathlib.Path`; código antigo usa `str`. Funções de stage router esperam `Path`. `extractor.py` usa `str`.

6. **LangGraph e LangChain estão instalados mas seu uso não é confirmado** no código ativo. Não assumir que estão integrados.

7. **Ruff ignora todas as regras** (`ignore = ["ALL"]`). Não esperar feedback de linting automático.
