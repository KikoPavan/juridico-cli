## apps/data-processing (novo — monorepo)

### Pipeline unificado

```bash
# Pipeline completo (clean → analyze → collect → validate → load)
uv run python apps/data-processing/src/data_processing/cli.py run \
  --input <dir_md> --collector <cad_obr|proc>

# Etapa isolada: limpeza jurídica
uv run python apps/data-processing/src/data_processing/cli.py clean \
  --input <dir_md> --output var/staging

# Etapa isolada: análise de regras
uv run python apps/data-processing/src/data_processing/cli.py analyze \
  --input var/staging --output var/staging
```

### Collectors (nova localização)

```bash
# collector-cad_obr
uv run python3 apps/data-processing/src/data_processing/collectors/collector_cad_obr/main.py

# collector-proc
uv run python3 apps/data-processing/src/data_processing/collectors/collector_proc/main.py
```

### Testes

```bash
uv run pytest apps/data-processing/tests/ -v
```

---

## Agents (legado — mantido durante migração)
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
uv run python3 agents/firac-cli/main.py --config agents/firac-cli/config.yaml
```
ou
```bash
uv run python3 agents/firac-cli/main.py run \
  --config-path agents/firac-cli/config.yaml \
  --processo "outputs/processo/01_collector/collector_out_processo_consolidated.json" \
  --evidence "outputs/cad_obr/05_evidence/dataset_v1/evidence_out.json" \
  --law-pack "outputs/legal/law_pack_v1.json"
```

---
# law-cli
```bash
uv run python3 agents/law-cli/main.py run \
  --processo "outputs/processo/01_collector/collector_out_processo_consolidated.json" \
  --juntada  "outputs/juntada/01_collector/collector_out_juntada_procuracao_Juraci_para_Francisco.json"
```
---

```bash
uv run python3 -m py_compile agents/law-cli/main.py && echo "main.py compila OK"

uv run python3 agents/law-cli/main.py run \
  --processo "outputs/processo/01_collector/collector_out_processo_consolidated.json" \
  --juntada  "outputs/juntada/01_collector/collector_out_juntada_procuracao_Juraci_para_Francisco.json"
```
---

1. case-law-cli
```bash
uv run python3 agents/case-law-cli/main.py --config agents/case-law-cli/config.yaml
```

1. petition-cli
```bash
uv run python3 agents/petition-cli/main.py --config agents/petition-cli/config.yaml
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
