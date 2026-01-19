## 0) Ambiente e contexto do repo

**Gerado em:** 2026-01-11 11:38:56
**Repo:** /home/kiko/devops/juridico-cli
**Git root:** /home/kiko/devops/juridico-cli
**Branch:** main
**Último commit:** `fdabce87e85c869831a15c49221135bc1a371931`
**Data:** Sun Jan 11 10:55:19 2026 -0300
**Mensagem:** correções agentes
**Working tree sujo:** SIM

**Mudanças (porcelain):**

- `?? tools/`

---

## 1) Mapa estrutural (árvore resumida)

```text
- juridico-cli/
  - .agent/
    - .agent/rules/
      - .agent/rules/audit_and_plan.md
    - .agent/workflows/
  - .github/
    - .github/workflows/
      - .github/workflows/ci.yml
  - agents/
    - agents/case-law-cli/
      - agents/case-law-cli/adapters/
      - agents/case-law-cli/logs/
      - agents/case-law-cli/tests/
      - agents/case-law-cli/config.yaml
      - agents/case-law-cli/io.schema.json
      - agents/case-law-cli/main.py
      - agents/case-law-cli/precedent-finder-ext.toml
    - agents/collector-cad_obr/
      - agents/collector-cad_obr/skills/
      - agents/collector-cad_obr/config.yaml
      - agents/collector-cad_obr/io.schema.json
      - agents/collector-cad_obr/main.py
    - agents/collector-proc/
      - agents/collector-proc/skills/
      - agents/collector-proc/config.yaml
      - agents/collector-proc/io.schema.json
      - agents/collector-proc/main.py
    - agents/compliance-cli/
      - agents/compliance-cli/adapters/
      - agents/compliance-cli/logs/
      - agents/compliance-cli/tests/
      - agents/compliance-cli/config.yaml
      - agents/compliance-cli/io.schema.json
      - agents/compliance-cli/main.py
    - agents/firac-cli/
      - agents/firac-cli/skills/
      - agents/firac-cli/config.yaml
      - agents/firac-cli/io.schema.json
      - agents/firac-cli/main.py
    - agents/petition-cli/
      - agents/petition-cli/adapters/
      - agents/petition-cli/logs/
      - agents/petition-cli/tests/
      - agents/petition-cli/config.yaml
      - agents/petition-cli/io.schema.json
      - agents/petition-cli/main.py
    - agents/reconciler-cli/
      - agents/reconciler-cli/skills/
      - agents/reconciler-cli/config.yaml
      - agents/reconciler-cli/graph.py
      - agents/reconciler-cli/io.schema.json
      - agents/reconciler-cli/main.py
      - agents/reconciler-cli/nodes.py
      - agents/reconciler-cli/state.py
  - arq-js/
    - arq-js/1-monetary_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/2-collector_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/3-collector_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/4-collector_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/5-collector_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/5-collector_out_juntada_escritura_hipotecaria_176700529.json
    - arq-js/6-collector_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/6-collector_out_juntada_escritura_hipotecaria_176700529.json
    - arq-js/7-collector_out_juntada_escritura_hipotecaria_176700529.json
    - arq-js/8-collector_out_cad_obr_escritura_matricula_7.546.json
    - arq-js/8-collector_out_cad_obr_escritura_matricula_905.json
    - arq-js/8-collector_out_cad_obr_escritura_matricula_946.json
    - arq-js/cadeia_obrigacoes.json
    - arq-js/collector_out_cad_obr_escritura_matricula_7.013.json
    - arq-js/collector_out_cad_obr_escritura_matricula_905.json
    - arq-js/collector_out_cad_obr_escritura_matricula_946.json
    - arq-js/collector_out_juntada_contrato_social_jkmg_2002.json
    - arq-js/collector_out_juntada_contrato_social_JKMG_2002.json
    - arq-js/collector_out_juntada_contrato_social_jkmg_2003.json
    - arq-js/collector_out_juntada_contrato_social_pavao_supermercados_ltda_2001.json
    - arq-js/collector_out_juntada_processo_divida_ativa_funcafe.json
    - arq-js/collector_out_juntada_procuracao_juraci_para_francisco.json
    - arq-js/collector_out_processo_consolidado.json
    - arq-js/velha_collector_out_juntada_escritura_hipotecaria_176700529.json
  - arq-md/
    - arq-md/aditivo_contrato_hipoteca_176700530.md
    - arq-md/contrato_bancario_hipoteca_176700530.md
    - arq-md/contrato_bancario_hipoteca_176700634.md
    - arq-md/contrato_bancario_hipoteca_aditivo_176700530.md
    - arq-md/contrato_bancario_hipoteca_aditivo_176700634.md
    - arq-md/contrato_social_JKMG_2002.md
    - arq-md/Contrato_Social_JKMG_2003.md
    - arq-md/contrato_social_pavao_supermercados_ltda_2001.md
    - arq-md/escritura_hipotecaria_176700529.md
    - arq-md/escritura_matricula_7.013.md
    - arq-md/escritura_matricula_7.546.md
    - arq-md/escritura_matricula_905.md
    - arq-md/escritura_matricula_946.md
    - arq-md/peticao_processo_acao_execucao-B.B.md
    - arq-md/processo_divida_ativa_funcafe.md
    - arq-md/procuracao_Juraci_para_Francisco.md
    - arq-md/reconciler_relatorio.md
    - arq-md/SKILL.juntada.md
    - arq-md/v1_reconciler.md
    - arq-md/v2_reconciler.md
  - backup/
    - backup/snapshot_etapa_0/
      - backup/snapshot_etapa_0/agents/
      - backup/snapshot_etapa_0/prompts/
      - backup/snapshot_etapa_0/scripts/
      - backup/snapshot_etapa_0/.env
      - backup/snapshot_etapa_0/main.py
      - backup/snapshot_etapa_0/script.sh
  - base_juridica/
    - base_juridica/j.j/
      - base_juridica/j.j/leis/
      - base_juridica/j.j/publicações/
      - base_juridica/j.j/AIRESP-2038444-2024-06-12.pdf
      - base_juridica/j.j/ITA- RE_1.577.931 - GO.pdf
      - base_juridica/j.j/ITA-EDcl no AgRg no AGRAVO DE INSTRUMENTO Nº 1.268.297 - RS.pdf
      - base_juridica/j.j/ITA-RE_1.004.729 - MS.pdf
      - base_juridica/j.j/ITA-RE_1.076.571 - SP.pdf
      - base_juridica/j.j/ITA-RE_1.582.388 - PE.pdf
      - base_juridica/j.j/RE 1.814.643-SP-ITA.pdf
      - base_juridica/j.j/RE 1.836.584 - MG ITA.pdf
      - base_juridica/j.j/RECURSO ESPECIAL Nº 1.814.643.pdf
      - base_juridica/j.j/STJ_201301774047_tipo_integra_142581281.pdf
      - base_juridica/j.j/STJ_201803102280_tipo_integra_102676782.pdf
      - base_juridica/j.j/STJ_201902284420_tipo_integra_109463375.pdf
      - base_juridica/j.j/STJ_202100675025_tipo_integra_125929289.pdf
  - data/
    - data/cad_obr/
      - data/cad_obr/contrato_social/
      - data/cad_obr/escritura_hipotecaria/
      - data/cad_obr/escritura_imovel/
    - data/indices/
      - data/indices/Tabela_bacen_TR.csv
    - data/juntada/
    - data/processo/
    - data/context.json
    - data/contexto_relacoes.json
  - docs/
    - docs/antigravity/ 
      - docs/antigravity/implementation_plan.md
      - docs/antigravity/levantamento_completo.md
      - docs/antigravity/relatorio_auditoria.md
      - docs/antigravity/task.md
      - docs/antigravity/walkthrough.md
    - docs/spec_monetary_regras_cad_obr.md
  - docs_iplt/
    - docs_iplt/arquivos_processo/
      - docs_iplt/arquivos_processo/Contrato Social Pavão Supermercadfos Ltda.md
      - docs_iplt/arquivos_processo/Contrato_Social_JKMG_2002.md
      - docs_iplt/arquivos_processo/Contrato_Social_JKMG_2003.md
      - docs_iplt/arquivos_processo/DIV. ATIVA-FUNCAFE-DACAO PGTO.md
      - docs_iplt/arquivos_processo/escritura_hipoctecaria.md
      - docs_iplt/arquivos_processo/escritura_imovel.schema.json.md
      - docs_iplt/arquivos_processo/escritura_imovel_matricula_9.405.md
      - docs_iplt/arquivos_processo/escritura_imovel_matricula_946.md
      - docs_iplt/arquivos_processo/peticao_esqueleto.md
      - docs_iplt/arquivos_processo/processo número 0003453-81.2003.8.2.md
      - docs_iplt/arquivos_processo/procuracao_Juraci_para_Francisco.md
      - docs_iplt/arquivos_processo/relatorio_base.md
      - docs_iplt/arquivos_processo/Relatório_de_Progresso.md
    - docs_iplt/collector-cli_backup/
      - docs_iplt/collector-cli_backup/adapters/
      - docs_iplt/collector-cli_backup/logs/
      - docs_iplt/collector-cli_backup/tests/
      - docs_iplt/collector-cli_backup/config.yaml.md
      - docs_iplt/collector-cli_backup/doc-collector-ext.toml.md
      - docs_iplt/collector-cli_backup/io.schema.json.md
      - docs_iplt/collector-cli_backup/main.py.md
    - docs_iplt/juridico-cli.md
    - docs_iplt/Orientações_Específicas_por_Agente.md
    - docs_iplt/Projeto-descritivo-juridico.ia.md
    - docs_iplt/Recomendações_Finais_por_Agente.md
  - logs/
    - logs/collector/
  - mcp-server-cad_obr/
    - mcp-server-cad_obr/deterministic.py
    - mcp-server-cad_obr/pyproject.toml
    - mcp-server-cad_obr/rag_tools.py
    - mcp-server-cad_obr/server.py
  - outputs/
    - outputs/cad_obr/
      - outputs/cad_obr/01_collector/
      - outputs/cad_obr/02_normalize/
      - outputs/cad_obr/03_monetary/
      - outputs/cad_obr/04_reconciler/
    - outputs/juntada/
      - outputs/juntada/collector_out_juntada_contrato_bancario_hipoteca_176700530.json
      - outputs/juntada/collector_out_juntada_contrato_bancario_hipoteca_176700634.json
      - outputs/juntada/collector_out_juntada_contrato_bancario_hipoteca_aditivo_176700530.json
      - outputs/juntada/collector_out_juntada_contrato_bancario_hipoteca_aditivo_176700634.json
      - outputs/juntada/collector_out_juntada_contrato_social_JKMG_2002.json
      - outputs/juntada/collector_out_juntada_contrato_social_JKMG_2003.json
      - outputs/juntada/collector_out_juntada_contrato_social_pavao_supermercados_ltda_2001.json
      - outputs/juntada/collector_out_juntada_escritura_hipotecaria_176700529.json
      - outputs/juntada/collector_out_juntada_processo_divida_ativa_funcafe.json
      - outputs/juntada/collector_out_juntada_procuracao_Juraci_para_Francisco.json
    - outputs/new/
    - outputs/old/
      - outputs/old/collector_out_cad_obr_escritura_matricula_7.013.json
      - outputs/old/collector_out_cad_obr_escritura_matricula_7.546.json
      - outputs/old/collector_out_cad_obr_escritura_matricula_905.json
      - outputs/old/collector_out_cad_obr_escritura_matricula_946.json
      - outputs/old/monetary_out_cad_obr_escritura_matricula_7.546.json
      - outputs/old/monetary_out_cad_obr_escritura_matricula_905.json
    - outputs/processo/
      - outputs/processo/collector_out_processo_consolidado.json
    - outputs/.gitkeep
    - outputs/cadeia_obrigacoes.json
    - outputs/reconciler_relatorio.md
  - pipelines/
    - pipelines/cad_obr/
      - pipelines/cad_obr/monetary/
      - pipelines/cad_obr/normalize/
      - pipelines/cad_obr/reconciler/
      - pipelines/cad_obr/schemas/
    - pipelines/cad_obr.py
  - prompts/
    - prompts/.gitkeep
    - prompts/case-law.md
    - prompts/collector-cad_obr.md
    - prompts/collector-proc.md
    - prompts/collector.md
    - prompts/compliance.md
    - prompts/firac.md
    - prompts/petition.md
    - prompts/reconciler.md
  - schemas/
    - schemas/defs/
      - schemas/defs/common.schema.json
    - schemas/cabecalho_processo.consolidated.schema.json
    - schemas/cabecalho_processo.schema.json
    - schemas/cadeia_obrigacoes.schema.json
    - schemas/contestacao_processo.consolidated.schema.json
    - schemas/contestacao_processo.schema.json
    - schemas/contrato_social.json
    - schemas/decisao_processo.consolidated.schema.json
    - schemas/decisao_processo.schema.json
    - schemas/escritura_hipotecaria.schema.json
    - schemas/escritura_imovel.schema.json
    - schemas/mandato_processo.consolidated.schema.json
    - schemas/mandato_processo.schema.json
    - schemas/peticao_processo.consolidated.schema.json
    - schemas/peticao_processo.schema.json
    - schemas/processo.schema.json
    - schemas/procuracao.consolidated.schema.json
    - schemas/procuracao.schema.json
    - schemas/v1_procuracao.schema.json
  - scripts/
    - scripts/genai_adapter.py
    - scripts/precedent_finder.py
    - scripts/rag_service.py
    - scripts/setup_schemas.py
    - scripts/transcriber_util.py
  - templates/
    - templates/peticao_esqueleto.md
    - templates/regras_para_peticao_juridica.md
    - templates/relatorio_base.md
  - tests/
    - tests/test_smoke_syntax.py
  - tools/
    - tools/levantar_estado.py
  - .env
  - .gitignore
  - .python-version
  - debug.py
  - diff_hipotecas_onus.py
  - main.py
  - Plano_Arquitetura_alvo_projeto_juridico-cli.md
  - pyproject.toml
  - README.md
  - requirements.txt
  - ruff.toml
  - script.sh
  - test_deterministic_tools.py
  - test_genai.py
  - test_rag_tools.py
  - teste_debug.py
  - uv.lock
  - validate_collector_outputs.py
```

---

## 2) Inventário granular por agente (OK/FALTA/N/A)

| Agente | Path | config | io.schema | schemas/ | prompts | entrypoints | tests | docker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case-law-cli | agents/case-law-cli | OK | OK | FALTA | 1 | 1 | OK | 0 |
| collector-cad_obr | agents/collector-cad_obr | OK | OK | FALTA | 5 | 1 | FALTA | 0 |
| collector-proc | agents/collector-proc | OK | OK | FALTA | 9 | 1 | FALTA | 0 |
| compliance-cli | agents/compliance-cli | OK | OK | FALTA | 1 | 1 | OK | 0 |
| firac-cli | agents/firac-cli | OK | OK | FALTA | 3 | 1 | FALTA | 0 |
| petition-cli | agents/petition-cli | OK | OK | FALTA | 1 | 1 | OK | 0 |
| reconciler-cli | agents/reconciler-cli | OK | OK | FALTA | 3 | 1 | FALTA | 0 |
| mcp-server-cad_obr | mcp-server-cad_obr | FALTA | FALTA | FALTA | 0 | 0 | FALTA | 0 |

### case-law-cli
- **Pasta:** `agents/case-law-cli`
- **config:** `agents/case-law-cli/config.yaml`
**Trecho (config):**

```text
runtime:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192


---

  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192

rag:
  enabled: true
```
- **io.schema:** `agents/case-law-cli/io.schema.json`
**Trecho (io.schema):**

```text
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema IO do 'case-law-cli'",
  "description": "Define o contrato de dados para as entradas e saídas do agente 'case-law-cli'",
  "type": "object",
  "properties": {
    "inputs": {
      "type": "object",
      "properties": {
        "firac_report_path": {
          "type": "string",
          "description": "Caminho para o relatório FIRAC (fonte das teses).",
          "default": "../../outputs/relatorio_firac.md"
        },
        "theses": {
          "type": "array",
          "description": "Teses nucleares extraídas do FIRAC para busca.",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "firac_report_path",
        "theses"
      ]
    },
    "outputs": {
      "description": "Define a saída estruturada (MD) para os precedentes",
      "type": "object",
```
- **schemas/:** NÃO ENCONTRADO
- **prompts:** 1 arquivo(s)
  - `agents/case-law-cli/config.yaml`
- **entrypoints:**
  - `agents/case-law-cli/main.py`
    **Trecho (entrypoint):**

```text


def get_project_root():
    # Caminho: agents/case-law-cli/main.py -> agents/ -> root/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

- **tests:**
  - `agents/case-law-cli/tests`
- **docker:** NÃO ENCONTRADO

### collector-cad_obr
- **Pasta:** `agents/collector-cad_obr`
- **config:** `agents/collector-cad_obr/config.yaml`
**Trecho (config):**
runtime:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.1
  max_output_tokens: 65536
  agent_name: "collector-cad_obr"

---

  provider: gemini
  model: gemini-2.5-flash
  - **io.schema:** `agents/collector-cad_obr/io.schema.json`
**Trecho (io.schema):**
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/collector-cad_obr.io.schema.json",
  "title": "Contrato de I/O do agente collector-cad_obr",
  "description": "Schema para padronizar a requisição/opções de execução e o relatório de execução do collector-cad_obr. A saída estruturada POR DOCUMENTO é definida pelos schemas específicos referenciados em config.yaml (schemas/escritura_imovel.schema.json, schemas/contrato_social.schema.json, schemas/escritura_hipotecaria.schema.json).",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "agent": {
      "type": "string",
      "const": "collector-cad_obr",
      "description": "Identificador do agente."
    },
    "io_version": {
      "type": "string",
      "description": "Versão lógica do contrato de I/O (não confundir com version das skills).",
      "default": "collector-cad_obr-io-v1"
    },
    "inputs": {
      "type": "object",
      "additionalProperties": false,
      "description": "Parâmetros/overrides opcionais para execução do collector (o agente pode ignorar campos que não implemente).",
      "properties": {
        "config_path": {
          "type": "string",
          "description": "Caminho do config.yaml do collector-cad_obr.",
          "default": "agents/collector-cad_obr/config.yaml"
        },
        - **schemas/:** NÃO ENCONTRADO
- **prompts:** 5 arquivo(s)
  - `agents/collector-cad_obr/config.yaml`
  - `agents/collector-cad_obr/skills/SKILL.contrato_social.md`
  - `agents/collector-cad_obr/skills/SKILL.core.md`
  - `agents/collector-cad_obr/skills/SKILL.escritura_hipotecaria.md`
  - `agents/collector-cad_obr/skills/SKILL.escritura_imovel.md`
- **entrypoints:**
  - `agents/collector-cad_obr/main.py`
    **Trecho (entrypoint):**

```text

    model_name = "gemini-2.5-flash"

    client = genai.Client(api_key=api_key)
    generate_config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=65536,
```
- **tests:** NÃO ENCONTRADO
- **docker:** NÃO ENCONTRADO

### collector-proc
- **Pasta:** `agents/collector-proc`
- **config:** `agents/collector-proc/config.yaml`
**Trecho (config):**

```text

runtime:
  provider: "google"
  model: "gemini-2.0-flash"
  temperature: 0.1
  top_p: 0.95
  max_output_tokens: 8192

---

  model: "gemini-2.0-flash"
  temperature: 0.1
  top_p: 0.95
  max_output_tokens: 8192

paths:
  prompt_base: "agents/collector-proc/prompts/collector-proc.md"
```
- **io.schema:** `agents/collector-proc/io.schema.json`
**Trecho (io.schema):**

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://juridico-cli.local/agents/collector-proc/io.schema.json",
  "title": "collector-proc IO Envelope — v2",
  "description": "Contrato de entrada/saída do collector-proc. Valida envelope + payload por document_type e mode.",
  "type": "object",
  "required": [
    "agent_name",
    "agent_version",
    "job_id",
    "run_id",
    "created_at",
    "document_type",
    "mode",
    "status",
    "sources"
  ],
  "properties": {
    "agent_name": {
      "const": "collector-proc"
    },
    "agent_version": {
      "type": "string",
      "minLength": 1
    },
    "job_id": {
      "$ref": "../../schemas/defs/common.schema.json#/$defs/NonEmptyString"
    },
    "run_id": {
      "$ref": "../../schemas/defs/common.schema.json#/$defs/UUID"
```
- **schemas/:** NÃO ENCONTRADO
- **prompts:** 9 arquivo(s)
  - `agents/collector-proc/config.yaml`
  - `agents/collector-proc/skills/SKILL.cabecalho_processo.md`
  - `agents/collector-proc/skills/SKILL.contestacao_processo.md`
  - `agents/collector-proc/skills/SKILL.core.md`
  - `agents/collector-proc/skills/SKILL.decisao_processo.md`
  - `agents/collector-proc/skills/SKILL.mandato_processo.md`
  - `agents/collector-proc/skills/SKILL.peticao_processo.md`
  - `agents/collector-proc/skills/SKILL.processo.md`
  - `agents/collector-proc/skills/SKILL.procuracao.md`
- **entrypoints:**
  - `agents/collector-proc/main.py`
    **Trecho (entrypoint):**

```text

    model_name = "gemini-2.5-flash"

    client = genai.Client(api_key=api_key)
    generate_config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=65536,
```
- **tests:** NÃO ENCONTRADO
- **docker:** NÃO ENCONTRADO

### compliance-cli
- **Pasta:** `agents/compliance-cli`
- **config:** `agents/compliance-cli/config.yaml`
**Trecho (config):**

```text
runtime:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192


---

  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192

rag:
  enabled: true
```
- **io.schema:** `agents/compliance-cli/io.schema.json`
**Trecho (io.schema):**

```text
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema IO do 'compliance-cli'",
  "description": "Define o contrato de dados para as entradas e saídas do agente 'compliance-cli'",
  "type": "object",
  "properties": {
    "inputs": {
      "type": "object",
      "properties": {
        "peticao_esqueleto_path": {
          "type": "string",
          "description": "Caminho para a petição gerada",
          "default": "../../outputs/peticao_esqueleto.md"
        },
        "firac_report_path": {
          "type": "string",
          "description": "Caminho para o relatório FIRAC (base de auditoria)",
          "default": "../../outputs/relatorio_firac.md"
        }
      },
      "required": [
        "peticao_esqueleto_path",
        "firac_report_path"
      ]
    },
    "outputs": {
      "description": "Define a saída do checklist de compliance",
      "type": "object",
      "properties": {
        "checklist_out_path": {
```
- **schemas/:** NÃO ENCONTRADO
- **prompts:** 1 arquivo(s)
  - `agents/compliance-cli/config.yaml`
- **entrypoints:**
  - `agents/compliance-cli/main.py`
    **Trecho (entrypoint):**

```text
        return yaml.safe_load(f)


def main():
    try:
        config = load_config()
```
- **tests:**
  - `agents/compliance-cli/tests`
- **docker:** NÃO ENCONTRADO

### firac-cli
- **Pasta:** `agents/firac-cli`
- **config:** `agents/firac-cli/config.yaml`
**Trecho (config):**

```text
runtime:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192  # FIRAC pode precisar de respostas maiores


---

  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192  # FIRAC pode precisar de respostas maiores

rag:
  enabled: true
```
- **io.schema:** `agents/firac-cli/io.schema.json`
**Trecho (io.schema):**

```text
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema IO do 'firac-cli'",
  "description": "Define o contrato de dados para as entradas e saídas do agente 'firac-cli'",
  "type": "object",
  "properties": {
    "inputs": {
      "type": "object",
      "properties": {
        "collector_out_path": {
          "type": "string",
          "description": "Caminho para a coleta de fatos",
          "default": "../../outputs/collector_out.md"
        },
        "relatorio_base_path": {
          "type": "string",
          "description": "Caminho para o template do relatório base",
          "default": "../../templates/relatorio_base.md"
        }
      },
      "required": [
        "collector_out_path"
      ]
    },
    "outputs": {
      "description": "Define a saída do relatório FIRAC",
      "type": "object",
      "properties": {
        "relatorio_firac_path": {
          "type": "string",
```
- **schemas/:** NÃO ENCONTRADO
- **prompts:** 3 arquivo(s)
  - `agents/firac-cli/config.yaml`
  - `agents/firac-cli/skills/SKILL.acao_nulidade_garantia_hipotecaria.md`
  - `agents/firac-cli/skills/SKILL.core.md`
- **entrypoints:**
  - `agents/firac-cli/main.py`
    **Trecho (entrypoint):**

```text
        return yaml.safe_load(f)


def main():
    try:
        config = load_config()
```
- **tests:** NÃO ENCONTRADO
- **docker:** NÃO ENCONTRADO

### petition-cli
- **Pasta:** `agents/petition-cli`
- **config:** `agents/petition-cli/config.yaml`
**Trecho (config):**

```text
runtime:
  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192


---

  provider: gemini
  model: gemini-2.5-flash
  temperature: 0.0
  max_output_tokens: 8192

rag:
  enabled: true
```
- **io.schema:** `agents/petition-cli/io.schema.json`
**Trecho (io.schema):**

```text
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema IO do 'petition-cli'",
  "description": "Define o contrato de dados para as entradas e saídas do agente 'petition-cli'",
  "type": "object",
  "properties": {
    "inputs": {
      "type": "object",
      "properties": {
        "firac_report_path": {
          "type": "string",
          "description": "Caminho para o relatório FIRAC",
          "default": "../../outputs/relatorio_firac.md"
        },
        "jurisprudencia_path": {
          "type": "string",
          "description": "Caminho para os precedentes",
          "default": "../../outputs/jurisprudencia.md"
        },
        "peticao_template_path": {
          "type": "string",
          "description": "Caminho para o template da petição",
          "default": "../../templates/peticao_esqueleto.md"
        }
      },
      "required": [
        "firac_report_path",
        "jurisprudencia_path",
        "peticao_template_path"
      ]
```
- **schemas/:** NÃO ENCONTRADO
- **prompts:** 1 arquivo(s)
  - `agents/petition-cli/config.yaml`
- **entrypoints:**
  - `agents/petition-cli/main.py`
    **Trecho (entrypoint):**

```text
        return yaml.safe_load(f)


def main():
    try:
        config = load_config()
```
- **tests:**
  - `agents/petition-cli/tests`
- **docker:** NÃO ENCONTRADO

### reconciler-cli
- **Pasta:** `agents/reconciler-cli`
- **config:** `agents/reconciler-cli/config.yaml`
**Trecho (config):**

```text
runtime:
  provider: gemini
  mode: google.genai
  model: gemini-2.5-flash
  temperature: 0.0
  top_p: 0.95
  max_output_tokens: 8192

---

  model: gemini-2.5-flash
  temperature: 0.0
  top_p: 0.95
  max_output_tokens: 8192

paths:
  # Prompt base do reconciler
```
- **io.schema:** `agents/reconciler-cli/io.schema.json`
**Trecho (io.schema):**

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/reconciler.schema.json",
  "title": "Saída estruturada do agente reconciler-cli",
  "type": "object",
  "additionalProperties": true,
  "description": "Estrutura de saída do agente reconciler-cli, consolidando relações críticas entre obrigações, documentos de juntada e contexto do usuário.",
  "properties": {
    "versao": {
      "type": "string",
      "description": "Versão lógica do formato de saída (ex.: 'reconciler-v1')."
    },
    "gerado_em": {
      "type": ["string", "null"],
      "format": "date-time",
      "description": "Timestamp ISO 8601 da geração, se disponível."
    },
    "origem": {
      "type": ["object", "null"],
      "additionalProperties": true,
      "description": "Metadados sobre os arquivos de entrada utilizados pelo reconciler.",
      "properties": {
        "cadeias_arquivo": {
          "type": ["string", "null"],
          "description": "Caminho do arquivo de cadeia de obrigações (ex.: 'outputs/cadeia_obrigacoes.json')."
        },
        "monetary_dir": {
          "type": ["string", "null"],
          "description": "Diretório de onde foram lidos os arquivos do monetary-cli (ex.: 'outputs/cad_obr/02_monetary')."
        },
```
- **schemas/:** NÃO ENCONTRADO
- **prompts:** 3 arquivo(s)
  - `agents/reconciler-cli/config.yaml`
  - `agents/reconciler-cli/skills/SKILL.cadeia_obrigacoes_nulidade_hipoteca.md`
  - `agents/reconciler-cli/skills/SKILL.core.md`
- **entrypoints:**
  - `agents/reconciler-cli/main.py`
    **Trecho (entrypoint):**

```text
import argparse
import json
import sys
```
- **tests:** NÃO ENCONTRADO
- **docker:** NÃO ENCONTRADO

### mcp-server-cad_obr
- **Pasta:** `mcp-server-cad_obr`
- **config:** NÃO ENCONTRADO
- **io.schema:** NÃO ENCONTRADO
- **schemas/:** NÃO ENCONTRADO
- **prompts:** NÃO ENCONTRADO
- **entrypoints:** NÃO ENCONTRADO
- **tests:** NÃO ENCONTRADO
- **docker:** NÃO ENCONTRADO


---

## 3) Contratos de I/O (evidências em config/código)

* **case-law-cli**
**config:** `agents/case-law-cli/config.yaml`

```text
  provider: gemini\n  model: gemini-2.5-flash\n  temperature: 0.0\n  max_output_tokens: 8192\n\nrag:\n  enabled: true\n\n---\n\n\npaths:\n  prompt_file: prompts/case-law.md\n  input_relatorio_firac: outputs/relatorio_firac.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  output_jurisprudencia: outputs/jurisprudencia.md\n\n---\n\npaths:\n  prompt_file: prompts/case-law.md\n  input_relatorio_firac: outputs/relatorio_firac.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  output_jurisprudencia: outputs/jurisprudencia.md
```

**code:** `agents/case-law-cli/main.py`

```text
\n        # 1. Resolver caminhos\n        prompt_file = os.path.join(project_root, paths.get("prompt_file"))\n        firac_input = os.path.join(project_root, config["paths"]["input_file"])\n        juris_output = os.path.join(project_root, config["paths"]["output_file"])\n\n        # 2. Ler prompt\n\n---\n\n        # 1. Resolver caminhos\n        prompt_file = os.path.join(project_root, paths.get("prompt_file"))\n        firac_input = os.path.join(project_root, config["paths"]["input_file"])\n        juris_output = os.path.join(project_root, config["paths"]["output_file"])\n\n        # 2. Ler prompt\n        with open(prompt_file, "r", encoding="utf-8") as p:
```

* **collector-cad_obr**
**config:** `agents/collector-cad_obr/config.yaml`

```text
  provider: gemini\n  model: gemini-2.5-flash\n  temperature: 0.1\n  max_output_tokens: 65536\n  agent_name: "collector-cad_obr"\n\npaths:\n\n---\n\n  # --- REGRA 1: data/cad_obr/escritura_imovel -> Saída 1:1 (um JSON por arquivo) ---\n  - name: "Processamento escritura_imovel"\n    id: "cad_obr-escritura-imovel"\n    input_dir: "data/cad_obr/escritura_imovel"\n    output_dir: "outputs/cad_obr/01_collector/escritura_imovel"\n    output_prefix: "collector_out_escritura_imovel_"\n    skill_key: "escritura_imovel"\n\n---\n\n  - name: "Processamento escritura_imovel"\n    id: "cad_obr-escritura-imovel"\n    input_dir: "data/cad_obr/escritura_imovel"\n    output_dir: "outputs/cad_obr/01_collector/escritura_imovel"\n    output_prefix: "collector_out_escritura_imovel_"\n    skill_key: "escritura_imovel"\n    schema_file: "schemas/escritura_imovel.schema.json"
```

**code:** `agents/collector-cad_obr/main.py`

```text
    client = genai.Client(api_key=api_key)\n    generate_config = types.GenerateContentConfig(\n        temperature=0.0,\n        max_output_tokens=65536,\n        response_mime_type="application/json",\n        safety_settings=[\n            types.SafetySetting(\n\n---\n\n\n\ndef assemble_prompt(\n    base_prompt: str, skill_content: str, schema_content: str, doc_content: str\n) -> str:\n    parts = [\n        base_prompt,
```

* **collector-proc**
**config:** `agents/collector-proc/config.yaml`

```text
  model: "gemini-2.0-flash"\n  temperature: 0.1\n  top_p: 0.95\n  max_output_tokens: 8192\n\npaths:\n  prompt_base: "agents/collector-proc/prompts/collector-proc.md"\n\n---\n\n\npaths:\n  prompt_base: "agents/collector-proc/prompts/collector-proc.md"\n  skills_dir: "agents/collector-proc/skills"\n  schemas_dir: "schemas"\n  io_schema: "agents/collector-proc/io.schema.json"\n\n\n---\n\npaths:\n  prompt_base: "agents/collector-proc/prompts/collector-proc.md"\n  skills_dir: "agents/collector-proc/skills"\n  schemas_dir: "schemas"\n  io_schema: "agents/collector-proc/io.schema.json"\n\n  output_base_dir: "outputs/processo/01_collector"
```

**code:** `agents/collector-proc/main.py`

```text
    client = genai.Client(api_key=api_key)\n    generate_config = types.GenerateContentConfig(\n        temperature=0.0,\n        max_output_tokens=65536,\n        response_mime_type="application/json",\n        safety_settings=[\n            types.SafetySetting(\n\n---\n\n\n\ndef assemble_prompt(\n    base_prompt: str, skill_content: str, schema_content: str, doc_content: str\n) -> str:\n    parts = [\n        base_prompt,
```

* **compliance-cli**
**config:** `agents/compliance-cli/config.yaml`

```text
  provider: gemini\n  model: gemini-2.5-flash\n  temperature: 0.0\n  max_output_tokens: 8192\n\nrag:\n  enabled: true\n\n---\n\n\npaths:\n  prompt_file: prompts/compliance.md\n  input_peticao: outputs/peticao_esqueleto.md\n  input_relatorio_firac: outputs/relatorio_firac.md\n  input_jurisprudencia: outputs/jurisprudencia.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n\n---\n\npaths:\n  prompt_file: prompts/compliance.md\n  input_peticao: outputs/peticao_esqueleto.md\n  input_relatorio_firac: outputs/relatorio_firac.md\n  input_jurisprudencia: outputs/jurisprudencia.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  output_relatorio_compliance: outputs/relatorio_compliance.md
```

**code:** `agents/compliance-cli/main.py`

```text
\n        # 1. Construir comando (Gemini)\n        # A Skill (auditoria-peticao) é responsável por ler seus\n        # arquivos de input/prompt e salvar o output.\n        command = ["gemini", "skill", skill_name]\n\n        print(f"Executando: {' '.join(command)}")\n\n---\n\n\n        # 2. Chamar sub-processo\n        process = subprocess.run(\n            command, text=True, encoding="utf-8", capture_output=True\n        )\n\n        # 3. Imprimir resultados
```

* **firac-cli**
**config:** `agents/firac-cli/config.yaml`

```text
  provider: gemini\n  model: gemini-2.5-flash\n  temperature: 0.0\n  max_output_tokens: 8192  # FIRAC pode precisar de respostas maiores\n\nrag:\n  enabled: true\n\n---\n\n\npaths:\n  prompt_file: prompts/firac.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  input_collector_json: outputs/collector_out.json\n  input_contexto_societario: inputs/contexto/contexto_societario.json\n  input_hipotese_juridica: inputs/contexto/hipotese_juridica.md\n\n---\n\npaths:\n  prompt_file: prompts/firac.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  input_collector_json: outputs/collector_out.json\n  input_contexto_societario: inputs/contexto/contexto_societario.json\n  input_hipotese_juridica: inputs/contexto/hipotese_juridica.md\n  template_relatorio: templates/relatorio_base.md
```

**code:** `agents/firac-cli/main.py`

```text
\n        # 1. Construir comando (Gemini)\n        # A Skill (firac-relatorio) é responsável por ler seus próprios\n        # arquivos de input/prompt/template e salvar o output.\n        command = ["gemini", "skill", skill_name]\n\n        print(f"Executando: {' '.join(command)}")\n\n---\n\n\n        # 2. Chamar sub-processo\n        process = subprocess.run(\n            command, text=True, encoding="utf-8", capture_output=True\n        )\n\n        # 3. Imprimir resultados
```

* **petition-cli**
**config:** `agents/petition-cli/config.yaml`

```text
  provider: gemini\n  model: gemini-2.5-flash\n  temperature: 0.0\n  max_output_tokens: 8192\n\nrag:\n  enabled: true\n\n---\n\n\npaths:\n  prompt_file: prompts/petition.md\n  input_relatorio_firac: outputs/relatorio_firac.md\n  input_jurisprudencia: outputs/jurisprudencia.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  template_peticao: templates/peticao_esqueleto.md\n\n---\n\npaths:\n  prompt_file: prompts/petition.md\n  input_relatorio_firac: outputs/relatorio_firac.md\n  input_jurisprudencia: outputs/jurisprudencia.md\n  input_cadeia_obrigacoes: outputs/cadeia_obrigacoes.json\n  template_peticao: templates/peticao_esqueleto.md\n  template_regras: templates/Regras_para_petição_juridica.md
```

**code:** `agents/petition-cli/main.py`

```text
\n        # 1. Construir comando (Gemini)\n        # A Skill (esqueleto-peticao) é responsável por ler seus\n        # arquivos de input/prompt/template e salvar o output.\n        command = ["gemini", "skill", skill_name]\n\n        print(f"Executando: {' '.join(command)}")\n\n---\n\n\n        # 2. Chamar sub-processo\n        process = subprocess.run(\n            command, text=True, encoding="utf-8", capture_output=True\n        )\n\n        # 3. Imprimir resultados
```

* **reconciler-cli**
**config:** `agents/reconciler-cli/config.yaml`

```text
  model: gemini-2.5-flash\n  temperature: 0.0\n  top_p: 0.95\n  max_output_tokens: 8192\n\npaths:\n  # Prompt base do reconciler\n\n---\n\n    # Skill padrão (fallback) quando o tipo de processo NÃO bater com o alvo\n    skill_key_default: "core"\n\n    # Skill usada quando input.contexto_caso.tipo_processo == process_type_target\n    skill_key_target: "cadeia_obrigacoes_nulidade_hipoteca"\n\n    # Schema de saída do reconciler (seu io.schema.json)\n\n---\n\n    # Skill usada quando input.contexto_caso.tipo_processo == process_type_target\n    skill_key_target: "cadeia_obrigacoes_nulidade_hipoteca"\n\n    # Schema de saída do reconciler (seu io.schema.json)\n    schema_file: "schemas/cadeia_obrigacoes.schema.json"\n\n    # Entradas principais
```

**code:** `agents/reconciler-cli/main.py`

```text
    print(f"--- Reconciler Agent V2 ---")\n    print(f"Target: {args.property}")\n\n    # setup inputs\n    inputs = {\n        "case_id": "auto_run",\n        "target_property": args.property,\n\n---\n\n    print(f"Target: {args.property}")\n\n    # setup inputs\n    inputs = {\n        "case_id": "auto_run",\n        "target_property": args.property,\n        "hypothesis": args.hypothesis,
```

* **mcp-server-cad_obr**
_Sem trechos I/O evidentes encontrados._


---

## 4) Schemas (inventário)

- **Total arquivos com 'schema' no nome:** 36
- **Com 'consolidated' no nome:** 6

### Amostra (até 50)
- `schemas/cadeia_obrigacoes.schema.json`
- `schemas/mandato_processo.schema.json`
- `schemas/contestacao_processo.schema.json`
- `schemas/decisao_processo.consolidated.schema.json`
- `schemas/procuracao.schema.json`
- `schemas/cabecalho_processo.consolidated.schema.json`
- `schemas/contestacao_processo.consolidated.schema.json`
- `schemas/processo.schema.json`
- `schemas/escritura_hipotecaria.schema.json`
- `schemas/decisao_processo.schema.json`
- `schemas/peticao_processo.consolidated.schema.json`
- `schemas/cabecalho_processo.schema.json`
- `schemas/escritura_imovel.schema.json`
- `schemas/v1_procuracao.schema.json`
- `schemas/mandato_processo.consolidated.schema.json`
- `schemas/procuracao.consolidated.schema.json`
- `schemas/peticao_processo.schema.json`
- `schemas/defs/common.schema.json`
- `agents/petition-cli/io.schema.json`
- `agents/firac-cli/io.schema.json`
- `agents/reconciler-cli/io.schema.json`
- `agents/compliance-cli/io.schema.json`
- `agents/case-law-cli/io.schema.json`
- `agents/collector-cad_obr/io.schema.json`
- `agents/collector-proc/io.schema.json`
- `pipelines/cad_obr/schemas/common.schema.json`
- `pipelines/cad_obr/schemas/imoveis.schema.json`
- `pipelines/cad_obr/schemas/partes.schema.json`
- `pipelines/cad_obr/schemas/pendencias.schema.json`
- `pipelines/cad_obr/schemas/onus_obrigacoes.schema.json`
- `pipelines/cad_obr/schemas/novacoes_detectadas.schema.json`
- `pipelines/cad_obr/schemas/property_events.schema.json`
- `pipelines/cad_obr/schemas/contratos_operacoes.schema.json`
- `pipelines/cad_obr/schemas/documentos.schema.json`
- `pipelines/cad_obr/schemas/links.schema.json`
- `docs_iplt/collector-cli_backup/adapters/escritura_hipotecaria.schema.json`

### Por agente (quantidade em schemas/)
- **case-law-cli:** 0
- **collector-cad_obr:** 0
- **collector-proc:** 0
- **compliance-cli:** 0
- **firac-cli:** 0
- **petition-cli:** 0
- **reconciler-cli:** 0
- **mcp-server-cad_obr:** 0

---

## 5) Prompts e regras críticas (checagem)

* **case-law-cli**
- **Prompt:** `agents/case-law-cli/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **FALTA**

* **collector-cad_obr**
- **Prompt:** `agents/collector-cad_obr/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **FALTA**
- **Prompt:** `agents/collector-cad_obr/skills/SKILL.contrato_social.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - data_assinatura
required_anchors: true
validation_rules:
  - "Literalidade: não inferir dados societários ou imobiliários."
  - "Fonte/âncora obrigatória para cada imóvel e para cada valor (Cr$/R$)."
---
```

- **Prompt:** `agents/collector-cad_obr/skills/SKILL.core.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
name: core
agent: collector-cad_obr
description: Regras gerais de extração e rastreabilidade para documentos jurídicos
  em Markdown (âncoras de página, literalidade e validações).
version: 0.1.0
target_schema: io.schema.json
document_types:
```

- **Prompt:** `agents/collector-cad_obr/skills/SKILL.escritura_hipotecaria.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - fonte_documento_geral
required_anchors: true
validation_rules:
  - "Literalidade: não inferir partes, valores, prazos ou poderes."
  - "Fonte obrigatória (arquivo_md + ancora) para partes e cláusulas-chave."
---
```

- **Prompt:** `agents/collector-cad_obr/skills/SKILL.escritura_imovel.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
- fonte_documento_geral
required_anchors: true
validation_rules:
- 'literalidade: true'
- 'ancoragem: obrigatoria_em_registros_e_onus'
- 'nao_converter_moeda: true'
---
```


* **collector-proc**
- **Prompt:** `agents/collector-proc/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **OK**
  - Formato de evidência/prova: **FALTA**

```text
    - document_type
    - skill_key
    - target_schema
    - source_id
    - source_sha256
    - source_filename
    - language
```

- **Prompt:** `agents/collector-proc/skills/SKILL.cabecalho_processo.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - representations
  - anchors
validation_rules:
  - literalidade
  - ancoragem_forte
  - nao_inferir_papeis
  - nao_inventar_numero_processo
```

- **Prompt:** `agents/collector-proc/skills/SKILL.contestacao_processo.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - provas_e_requerimentos
  - pedidos_finais
validation_rules:
  - literalidade
  - ancoragem_por_bloco
  - nao_inferir_preliminares_ou_merito
  - preservar_estrutura_listas
```

- **Prompt:** `agents/collector-proc/skills/SKILL.core.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - document_type
  - anchors
validation_rules:
  - literalidade
  - ancoragem_obrigatoria
  - json_estrito_schema
  - nao_inferir
```

- **Prompt:** `agents/collector-proc/skills/SKILL.decisao_processo.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - outcome
  - determinacoes
validation_rules:
  - literalidade
  - ancoragem_forte_no_dispositivo
  - nao_inferir_resultado
  - nao_resumir_indevidamente
```

- **Prompt:** `agents/collector-proc/skills/SKILL.mandato_processo.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - assinantes
  - anchors
validation_rules:
  - literalidade
  - ancoragem_em_poderes_e_escopo
  - nao_inferir_relacao_mandataria
  - preservar_texto_de_clausulas
```

- **Prompt:** `agents/collector-proc/skills/SKILL.peticao_processo.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - provas_e_requerimentos
  - pedidos
validation_rules:
  - literalidade
  - ancoragem_por_pedido
  - nao_resumir_indevidamente
  - nao_inferir_fundamentos
```

- **Prompt:** `agents/collector-proc/skills/SKILL.processo.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - documentos_referenciados
  - anchors
validation_rules:
  - literalidade
  - ancoragem_em_identificacao_e_partes
  - nao_misturar_document_types
  - nao_inferir_papeis
```

- **Prompt:** `agents/collector-proc/skills/SKILL.procuracao.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - assinantes
  - anchors
validation_rules:
  - literalidade
  - ancoragem_em_poderes
  - nao_inferir_poderes
  - nao_inventar_partes
```


* **compliance-cli**
- **Prompt:** `agents/compliance-cli/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

* **firac-cli**
- **Prompt:** `agents/firac-cli/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**
- **Prompt:** `agents/firac-cli/skills/SKILL.acao_nulidade_garantia_hipotecaria.md`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**
- **Prompt:** `agents/firac-cli/skills/SKILL.core.md`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - Análise (aplicação das regras aos fatos)
  - Conclusões (tese provável, riscos, lacunas)
- Manter rastreabilidade:
  - Cada fato deve apontar para a fonte (arquivo, página, folha).
  - Cada conclusão deve apontar para os fatos e regras que a suportam.

## Entradas típicas
```


* **petition-cli**
- **Prompt:** `agents/petition-cli/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

* **reconciler-cli**
- **Prompt:** `agents/reconciler-cli/config.yaml`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **FALTA**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **FALTA**
- **Prompt:** `agents/reconciler-cli/skills/SKILL.cadeia_obrigacoes_nulidade_hipoteca.md`
  - Literalidade / sem inferência: **FALTA**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
  - `matricula`;
  - `id_obrigacao`, se existir;
  - `fontes_registro` – ex.: `["905:R.16", "905:Av.44-7546"]`;
  - `folhas_registro`, se houver (ex.: `["fls. 9-10"]`).

### Fatos declarados pelo usuário
```

- **Prompt:** `agents/reconciler-cli/skills/SKILL.core.md`
  - Literalidade / sem inferência: **OK**
  - Âncoras (fls/Folha/Pág.): **OK**
  - source_id/sha256: **FALTA**
  - Formato de evidência/prova: **OK**

```text
     - `descricao` breve;
   - `fatos_registros_imobiliarios[*]` – fatos objetivos, cada um com:
     - `id_fato`, `descricao`;
     - opcionalmente: `id_obrigacao`, `matricula`, `fontes_registro`, `folhas_registro`;
   - `fatos_declarados_usuario[*]` – fatos alegados no contexto do usuário;
   - `lacunas_documentais[*]` – lacunas de prova, com impacto e documentos sugeridos;
   - `checklist_documentos` – checklist específico daquela relação;
```


* **mcp-server-cad_obr**
_Nenhum prompt encontrado._


---

## 6) MCP server e tools (heurístico)

### Diretórios MCP encontrados
- `mcp-server-cad_obr`
  - entrypoint: `mcp-server-cad_obr/server.py`
    ```text
import sys

from deterministic import DATASET_PATH, get_property, list_novacoes, list_onus, timeline
from mcp.server.fastmcp import FastMCP

## Validate data path exists
if not DATASET_PATH.exists():

---

        f"WARNING: Dataset path not found at {DATASET_PATH.absolute()}", file=sys.stderr
    )

## Inicializa o servidor MCP
mcp = FastMCP("cad_obr")

    ```

### Referências a MCP (amostra)
- `pyproject.toml`
  ```text
]
## No seu pyproject.toml
[tool.ruff]
exclude = [
    ".venv",
  ```
- `test_deterministic_tools.py`
  ```text

# Add current directory to path so we can import modules
sys.path.append(str(Path("mcp-server-cad_obr").absolute()))

from deterministic import get_property, list_onus, timeline
  ```
- `test_rag_tools.py`
  ```text

## Add current directory to path
sys.path.append(str(Path("mcp-server-cad_obr").absolute()))

from rag_tools import search_laws, semantic_search
  ```
- `Plano_Arquitetura_alvo_projeto_juridico-cli.md`
  ```text
                         +------------------------------+
                           |      |            |
                           |      |            +--> MCP Tool: semantic_search (Qdrant)
                           |      +--> MCP Tool: sql/query_dataset (jsonl/DB)
                           +--> MCP Tool: build_evidence_pack
  ```
- `prompts/reconciler.md`
  ```text

### Fora de escopo
Não gerar solicitações ao banco (sem “document request” em qualquer formato/tool).

---
  ```
- `scripts/precedent_finder.py`
  ```text
                f"Prompt recebido via STDIN com sucesso ({len(prompt_content)} caracteres lidos)."
            )
            # Na implementação real, o prompt (e o 'google_web_search' tool)
            # seria usado para guiar a busca.
  - `tools/levantar_estado.py`
  ```text
- Inventário de schemas
- `mcp-server-cad_obr/pyproject.toml`
  ```text
[project]
name = "mcp-server-cad_obr"
version = "0.1.0"
description = "MCP Server for Juridico CLI - Data & RAG"
  ```
- `mcp-server-cad_obr/server.py`
  
from mcp.server.fastmcp import FastMCP

## Validate data path exists
  ```
- `docs/antigravity/levantamento_completo.md`
  ```text
| Entrypoint | **OK** | `agents/reconciler-cli/main.py` (Carrega Grafo) |
| Auxiliares | **OK** | `graph.py` (Estrutura LangGraph), `nodes.py` (Lógica dos nós) |
| Dependência | **CORRIGIDO** | Mocks silenciosos removidos em `nodes.py`. Agora falha explicitamente se MCP não carregar. |

### D) mcp-server-cad_obr
  ```

---

## 7) Execução mínima e validação (sugestões + detecção)

### Sugestão de validação mínima (sem executar automaticamente)
- Validar JSON (formato): `python -m json.tool <arquivo.json>`
- Verificar sintaxe Python: `python -m compileall .`

### Detectado no repo (heurística: nomes contendo validate/schema/check/lint):
- `backup/snapshot_etapa_0/scripts/setup_schemas.py`
- `docs_iplt/arquivos_processo/escritura_imovel.schema.json.md`
- `docs_iplt/collector-cli_backup/io.schema.json.md`
- `scripts/setup_schemas.py`
- `validate_collector_outputs.py`

---

## 8) Outputs e rastreabilidade (amostras)

### Amostras (JSON) + checagem de rastreabilidade

- **Arquivo:** `outputs/cad_obr/01_collector/escritura_hipotecaria/collector_out_escritura_hipotecaria_contrato_bancario_hipoteca_176700634.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **NÃO**
  {
  "tipo_documento": "CEDULA DE CRÉDITO COMERCIAL",
  "data_assinatura": "20 de dezembro de 2002",
  "credor": {
    "nome": "Banco do Brasil S.A.",
    "cnpj": "00.000.000/2666-20",
    "endereco": "Brasilia, Capital Federal, por sua Agencia CERQUEIRA CESAR",
    "representante": null,
    "fonte": {
      "arquivo_md": "documento.md",
      "ancora": "<!-- PÁGINA 1 -->"
    }
  },
  "divida_confessada": {
    "valor": "R$ 150.000,00",
    "data_posicao": "20 de dezembro de 2002",
    "operacao_original": {
      "tipo": "CEDULA DE CREDITO COMERCIAL",
      "numero": "176700634",
      "data_celebracao": "20/12/2002",
      "limite": "R$ 150.000,00",
      "vencimento": "20/12/2002",
      "garantia_original": null,
      "fonte": {
        "arquivo_md": "documento.md",
        "ancora": "<!-- PÁGINA 1 -->"
      }
    
- **Arquivo:** `outputs/cad_obr/01_collector/escritura_hipotecaria/collector_out_escritura_hipotecaria_contrato_bancario_hipoteca_176700530.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **SIM**
  - pistas: `\bfls\b`
  
  "tipo_documento": "CEDULA DE CREDITO COMERCIAL",
  "data_assinatura": "30/08/2001",
  "credor": {
    "nome": "Banco do Brasil S.A.",
    "cnpj": "00.000.000/2666-20",
    "endereco": "Brasilia, Capital Federal, por sua Agencia CERQUEIRA CESAR",
    "representante": null,
    "fonte": {
      "arquivo_md": "document.md",
      "fls": null,
      "rotulo_documento": null,
      "ancora": "[[PÁGINA 1]]"
    }
  },
  "divida_confessada": {
    "valor": "R$ 180.000,00 (cento e oitenta mil reais)",
    "data_posicao": "30 de agosto de 2002",
    "operacao_original": {
      "tipo": "CEDULA DE CREDITO COMERCIAL",
      "numero": "176.700.530",
      "data_celebracao": "30/08/2001",
      "limite": "R$ 180.000,00",
      "vencimento": "30/08/2002",
      "garantia_original": null,
      "fonte": {
        "arquivo_md": "document.md",
        "fls": null,
        "rotulo_documento": null,
        "ancora": "[[PÁGINA 1]]"
  ```

- **Arquivo:** `outputs/cadobr/02_normalize/escritura_hipotecaria/collector_out_escritura_hipotecaria_contrato_bancario_hipoteca_176700634.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **NÃO**
  ```text
{
  "tipo_documento": "CEDULA DE CRÉDITO COMERCIAL",
  "data_assinatura": "2002-12-20",
  "credor": {
    "nome": "Banco do Brasil S.A.",
    "cnpj": "00000000266620",
    "endereco": "Brasilia, Capital Federal, por sua Agencia CERQUEIRA CESAR",
    "representante": null,
    "fonte": {
      "arquivo_md": "documento.md",
      "ancora": "<!-- PÁGINA 1 -->"
    },
    "id_parte": "cnpj:00000000266620"
  },
  "divida_confessada": {
    "valor": "R$ 150.000,00",
    "data_posicao": "2002-12-20",
    "operacao_original": {
      "tipo": "CEDULA DE CREDITO COMERCIAL",
      "numero": "176700634",
      "data_celebracao": "2002-12-20",
      "limite": "R$ 150.000,00",
      "vencimento": "2002-12-20",
      "garantia_original": null,
      "fonte": {
        "arquivo_md": "documento.md",
        "ancora": "<!-- PÁGINA 1 -->"
      }
    },
    "forma_pagamento": {
  ```

- **Arquivo:** `outputs/cad_obr/02_normalize/escritura_hipotecaria/collector_out_escritura_hipotecaria_contrato_bancario_hipoteca_176700530.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **SIM**
  - pistas: `\bfls\b`
  ```text
{
  "tipo_documento": "CEDULA DE CREDITO COMERCIAL",
  "data_assinatura": "2001-08-30",
  "credor": {
    "nome": "Banco do Brasil S.A.",
    "cnpj": "00000000266620",
    "endereco": "Brasilia, Capital Federal, por sua Agencia CERQUEIRA CESAR",
    "representante": null,
    "fonte": {
      "arquivo_md": "document.md",
      "fls": null,
      "rotulo_documento": null,
      "ancora": "[[PÁGINA 1]]"
    },
    "id_parte": "cnpj:00000000266620"
  },
  "divida_confessada": {
    "valor": "R$ 180.000,00 (cento e oitenta mil reais)",
    "data_posicao": "2002-08-30",
    "operacao_original": {
      "tipo": "CEDULA DE CREDITO COMERCIAL",
      "numero": "176700530",
      "data_celebracao": "2001-08-30",
      "limite": "R$ 180.000,00",
      "vencimento": "2002-08-30",
      "garantia_original": null,
      "fonte": {
        "arquivo_md": "document.md",
        "fls": null,
        "rotulo_documento": null,
  ```

- **Arquivo:** `outputs/cad_obr/03_monetary/escritura_hipotecaria/monetary_escritura_hipotecaria_contrato_bancario_hipoteca_176700634.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **NÃO**
  ```text
{
  "tipo_documento": "CEDULA DE CRÉDITO COMERCIAL",
  "data_assinatura": "2002-12-20",
  "credor": {
    "nome": "Banco do Brasil S.A.",
    "cnpj": "00000000266620",
    "endereco": "Brasilia, Capital Federal, por sua Agencia CERQUEIRA CESAR",
    "representante": null,
    "fonte": {
      "arquivo_md": "documento.md",
      "ancora": "<!-- PÁGINA 1 -->"
    },
    "id_parte": "cnpj:00000000266620"
  },
  "divida_confessada": {
    "valor": "R$ 150.000,00",
    "data_posicao": "2002-12-20",
    "operacao_original": {
      "tipo": "CEDULA DE CREDITO COMERCIAL",
      "numero": "176700634",
      "data_celebracao": "2002-12-20",
      "limite": "R$ 150.000,00",
      "vencimento": "2002-12-20",
      "garantia_original": null,
      "fonte": {
        "arquivo_md": "documento.md",
        "ancora": "<!-- PÁGINA 1 -->"
      }
    },
    "forma_pagamento": {
  ```

- **Arquivo:** `outputs/cad_obr/03_monetary/escritura_hipotecaria/monetary_escritura_hipotecaria_contrato_bancario_hipoteca_176700530.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **SIM**
  - pistas: `\bfls\b`
  ```text
{
  "tipo_documento": "CEDULA DE CREDITO COMERCIAL",
  "data_assinatura": "2001-08-30",
  "credor": {
    "nome": "Banco do Brasil S.A.",
    "cnpj": "00000000266620",
    "endereco": "Brasilia, Capital Federal, por sua Agencia CERQUEIRA CESAR",
    "representante": null,
    "fonte": {
      "arquivo_md": "document.md",
      "fls": null,
      "rotulo_documento": null,
      "ancora": "[[PÁGINA 1]]"
    },
    "id_parte": "cnpj:00000000266620"
  },
  "divida_confessada": {
    "valor": "R$ 180.000,00 (cento e oitenta mil reais)",
    "data_posicao": "2002-08-30",
    "operacao_original": {
      "tipo": "CEDULA DE CREDITO COMERCIAL",
      "numero": "176700530",
      "data_celebracao": "2001-08-30",
      "limite": "R$ 180.000,00",
      "vencimento": "2002-08-30",
      "garantia_original": null,
      "fonte": {
        "arquivo_md": "document.md",
        "fls": null,
        "rotulo_documento": null,
  ```

- **Arquivo:** `outputs/cadeia_obrigacoes.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **NÃO**
  ```text
{
  "versao": "1.0",
  "gerado_em": "2025-12-11T16:12:34",
  "obrigacoes": [],
  "metadados": {
    "total_obrigacoes": 0,
    "fontes": [
      "/home/kiko/devops/juridico-cli/outputs/cad_obr/02_monetary/monetary_cad_obr_escritura_matricula_7.013.json",
      "/home/kiko/devops/juridico-cli/outputs/cad_obr/02_monetary/monetary_cad_obr_escritura_matricula_7.546.json",
      "/home/kiko/devops/juridico-cli/outputs/cad_obr/02_monetary/monetary_cad_obr_escritura_matricula_905.json",
      "/home/kiko/devops/juridico-cli/outputs/cad_obr/02_monetary/monetary_cad_obr_escritura_matricula_946.json"
    ]
  }
}
  ```

- **Arquivo:** `outputs/juntada/collector_out_juntada_procuracao_Juraci_para_Francisco.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **NÃO**
  ```text
{
  "data_outorga": "28/06/2002",
  "outorgantes": [
    "JURACI PIRES PAVAN",
    "MARIA CECILIA HOLZHAUSEN PAVAN"
  ],
  "outorgados": [
    "FRANCISCO CARLOS PAVAN"
  ],
  "transfere_poderes_pj": false,
  "transfere_poderes_pf": true,
  "descricao_poderes": "Poderes específicos para assinar Confissão de Dívidas junto ao Banco do Brasil S/A em nome das outorgantes como devedoras solidárias, e para praticar todos os atos necessários para o bom e cabal desempenho do mandato, incluindo agir, defender e tratar de assuntos, negócios, direitos e interesses das outorgantes, assumir responsabilidades, prestar informações, declarações e esclarecimentos, apresentar provas, atender solicitações, cumprir exigências, dirimir e suscitar dúvidas, entregar, receber e assinar quaisquer documentos necessários.",
  "poderes_especificos": [
    "assinar em nome delas OUTORGANTES, Confissão de Dívidas junto ao BANCO DO BRASIL S/A., na condição de devedoras solidárias",
    "agir, defender e tratar de todos os assuntos, negócios, direitos e interesses delas OUTORGANTES",
    "assumir quaisquer espécies de responsabilidades",
    "prestar informações, declarações e esclarecimentos",
    "apresentar provas",
    "atender solicitações",
    "cumprir exigências",
    "dirimir e suscitar dúvidas",
    "entregar, receber e assinar quaisquer documentos necessários",
    "Praticar enfim todos os demais atos que mister se tornem ao bom e cabal desempenho do presente mandato"
  ]
}
  ```

- **Arquivo:** `outputs/processo/collector_out_processo_consolidado.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **SIM**
  - pistas: `\bfls\b, \bfolha\b`
  ```text
{
  "tipo_documento": "Processo Judicial",
  "numero_processo": "1152/03",
  "partes": [
    {
      "nome": "BANCO DO BRASIL S.A.",
      "tipo": "Exequente",
      "polo": "Ativo"
    },
    {
      "nome": "JURACI PIRES PAVAN",
      "tipo": "Devedor Solidário",
      "polo": "Passivo"
    },
    {
      "nome": "FRANCISCO CARLOS PAVAN",
      "tipo": "Devedor Solidário",
      "polo": "Passivo"
    },
    {
      "nome": "MARIA CECÍLIA HOLZHAUSEN PAVAN",
      "tipo": "Devedor Solidário",
      "polo": "Passivo"
    },
    {
      "nome": "GILBERTO PAVAN",
      "tipo": "Devedor Solidário",
      "polo": "Passivo"
    },
    {
  ```

- **Arquivo:** `outputs/juntada/collector_out_juntada_contrato_social_pavao_supermercados_ltda_2001.json`
  - source_id/sha256: **NÃO**
  - âncoras (fls/Folha/Pág.): **NÃO**
  ```text
{
  "razao_social": "PAVÃO SUPERMERCADOS LTDA",
  "cnpj": "49.542.400/0001-18",
  "nire": "35200199292",
  "tipo_societario": "LTDA",
  "junta_comercial": "JUCESP",
  "numero_registro": "13.425/02-0",
  "data_registro": "17/01/2002",
  "data_ultima_alteracao": "13/07/2001",
  "sede_endereco": "Rua Olímpio Pavan, nº 52, na cidade e comarca de Cerqueira César, Estado de São Paulo, CEP nº 18.760.000",
  "sede_matriz_filial": "matriz e filiais",
  "objeto_social": null,
  "capital_social_total": "R$ 720.000,00",
  "capital_moeda": "BRL",
  "integralizacao_descricao": "Capital social composto por quotas anteriormente integralizadas, quotas integralizadas em moeda corrente neste ato, e quotas a integralizar.",
  "quotas": [
    "Gilberto Pavan – 240.000 quotas – 33,33...% – valor R$ 240.000,00",
    "Francisco Carlos Pavan – 240.000 quotas – 33,33...% – valor R$ 240.000,00",
    "Monica Aparecida Pavan – 240.000 quotas – 33,33...% – valor R$ 240.000,00"
  ],
  "socios": [
    {
      "nome": "Gilberto Pavan",
      "documento": "891.907.348-15",
      "tipo_documento": "CPF",
      "papel": "Sócio",
      "cotas": "240.000",
      "valor_cotas": "R$ 240.000,00",
      "participacao_percentual": "33,33...%",
      "ancora_qualificacao": "[[Página 2]]",
  ```


---

## 9) Dependências e prontidão para LangChain

- **pyproject.toml:** `pyproject.toml`

### Dependências (foco LangChain/LLM/RAG)
- google-genai>=0.3.3
- langgraph>=1.0.5
- langchain-core>=1.2.6

---

## 10) Sumário (CONFIRMADO / NÃO ENCONTRADO / INCONCLUSIVO)

### CONFIRMADO
- Pasta `agents/` existe (estrutura por agentes).
- Referências a `02_monetary`/`03_monetary` encontradas (verificar consistência de paths).
- Referências a Claude/Anthropic encontradas (provável legado/acoplamento).

### NÃO ENCONTRADO

### INCONCLUSIVO
- case-law-cli: itens faltando (schemas/).
- collector-cad_obr: itens faltando (schemas/).
- collector-proc: itens faltando (schemas/).
- compliance-cli: itens faltando (schemas/).
- firac-cli: itens faltando (schemas/).
- petition-cli: itens faltando (schemas/).
- reconciler-cli: itens faltando (schemas/).
- mcp-server-cad_obr: itens faltando (config, io.schema, schemas/, prompts).
