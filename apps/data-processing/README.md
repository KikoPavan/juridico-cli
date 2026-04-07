# data-processing

App responsável pela conversão, limpeza, análise de regras, extração estruturada e carga de documentos jurídicos.

## Pipeline interno

```
entrada bruta → conversão (converters/) → limpeza jurídica (cleaners/)
  → análise de regras (rule_analysis/) → collector especializado (collectors/)
  → validação (validation/) → persistência (loaders/)
```

## Execução

```bash
# Pipeline completo
uv run python apps/data-processing/src/data_processing/cli.py run \
  --input <arquivo_ou_diretório> --collector <cad_obr|proc>

# Etapa isolada: conversão
uv run python apps/data-processing/src/data_processing/cli.py convert --input <dir_pdf>

# Etapa isolada: limpeza
uv run python apps/data-processing/src/data_processing/cli.py clean --input <dir_md>
```

## Testes

```bash
uv run pytest apps/data-processing/tests/
```

## Estrutura

```
src/data_processing/
├── cli.py                  # Entrada CLI (Typer)
├── orchestrator/           # Orquestração e roteamento de etapas
├── converters/             # Conversão PDF → Markdown
│   └── markdown_engine/    # Engine reutilizado de pipelines/ingest/
├── cleaners/               # Limpeza jurídica (LegalDocCleaner)
├── rule_analysis/          # Análise de regras estruturais (GeradorDeRegras)
├── collectors/             # Agentes LLM de extração estruturada
│   ├── collector_cad_obr/  # (migrado de agents/collector-cad_obr — Sprint S5)
│   └── collector_proc/     # (migrado de agents/collector-proc — Sprint S5)
├── validation/             # Validação de schemas e contratos
├── loaders/                # Persistência em JSON, DuckDB, Qdrant
└── contracts/              # JSON Schemas dos contratos entre etapas
```
