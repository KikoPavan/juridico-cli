## Agents
1. collector-cad_obr
```bash
uv run python3 agents/collector-cad_obr/main.py agents/collector-cad_obr/config.yaml
```

1. collector-proc
```bash
uv run python3 agents/collector-proc/main.py agents/collector-proc/config.yaml
```

1. pipelines/cad_obr
1.1. monetary
1.2. normalize
1.3. reconciler
1.4. evidence_pack

2. firac-cli
```bash
uv run python3 agents/firac-cli/main.py agents/firac-cli/config.yaml
```

## ingest

1. **pdf_convert**
1.1. bj_doutrina # conversão PDF para MD
```bash
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_doutrina --mode md_only
```

1.2. bj_juris_stj # conversão PDF para MD
```bash
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_juris_stj --mode md_only
```

1.3. bj_leis # conversão PDF para MD
```bash
uv run python pipelines/ingest/pdf_convert/run.py --profile bj_leis --mode md_only
# normalização
uv run python pipelines/ingest/pdf_convert/profiles/bj_leis/normalize_md.py \
  --in outputs/ingest/bj_leis/01_md --inplace
```

1. **md_rag** # Gerar RAG, RAW, QA e QA e LOGS

# bj_doutrina
```bash
uv run python pipelines/ingest/md_rag/run.py --profile bj_doutrina
```

# bj_juris_stj
```bash
uv run python pipelines/ingest/md_rag/run.py --profile bj_juris_stj
```

# bj_leis
```bash
uv run python pipelines/ingest/md_rag/run.py --profile bj_leis
```
