## Tasks

### T1: Alterar diretório de entrada no `DataExtractorApp`

**Arquivo:** `apps/data-processing/src/data_processing/extractor.py`

**Mudanças:**
- Linha 31: substituir `"staging": ...` por `"input_clean": os.path.join(self.var_dir, "output", "processed")`
- Linha 58: substituir `self.dirs["staging"]` por `self.dirs["input_clean"]`

**Critério de conclusão:** extract procura arquivo em `var/output/processed/`
em vez de `var/staging/`.

### T2: Usar provider do `llm_profile` no `create_client`

**Arquivo:** `apps/data-processing/src/data_processing/extractor.py`

**Mudanças:**
- Após linha 94, extrair provider do `llm_profile`
- Linha 98: passar `provider_override` para `create_client`

**Código:**
```python
llm_profile = dispatch_result.get("llm_profile", {})
execution_class = llm_profile.get("execution_class", {})
provider = execution_class.get("provider")
client = LLMClientFactory.create_client(provider_override=provider)
```

**Critério de conclusão:** Com `GEMINI_API_KEY` definida, extract usa Gemini
sem tentar `http://host.docker.internal:1234`.

### T3: Adicionar diretório canônico de saída `var/output/extracted/`

**Arquivo:** `apps/data-processing/src/data_processing/extractor.py`

**Mudanças:**
- No `__init__`, adicionar:
  `"extracted": os.path.join(self.var_dir, "output", "extracted")`
- Linhas 108-109: salvar em `self.dirs["extracted"]` em vez de `self.dirs["output"]`

**Critério de conclusão:** JSON salvo em `var/output/extracted/result_*.json`.

### T4: Corrigir help do `extract --input`

**Arquivo:** `apps/data-processing/src/data_processing/cli.py`

**Mudança:**
- Linha 19: help de `"Nome do arquivo em var/input/md/ para processar"` para
  `"Nome do arquivo limpo em var/output/processed/ para extrair"`

**Critério de conclusão:** `--help` mostra o caminho correto.

### T5: Corrigir default do `clean --output`

**Arquivo:** `apps/data-processing/src/data_processing/cli.py`

**Mudança:**
- Linha 82: `Path("var/staging")` → `Path("var/output/processed")`

**Critério de conclusão:** `clean` sem `--output` salva em `var/output/processed/`.

### T6: Validar com pytest e OpenSpec

```bash
uv run pytest -q
openspec validate --all --strict
```

**Critério de conclusão:** Todos os testes e validações passam.

### T7: Validar extract real com Gemini

```bash
# Verificar GEMINI_API_KEY
echo "GEMINI_API_KEY=${GEMINI_API_KEY:+definida}"

# Executar extract
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli extract \
  --bundle "extr-peticao-processo" \
  --input "Petição Declaração de Nulidade_clean.md"
```

**Critério de conclusão:** Extract executa sem erro, não tenta
`host.docker.internal:1234`, JSON salvo em `var/output/extracted/`.

**Observação:** Se o modelo `gemini-3-flash-preview` do `llm_registry.yaml` não
funcionar, testar com `gemini-2.5-flash` (default do `gemini_client.py`). Se a
troca for necessária, atualizar `llm_registry.yaml` e registrar na
`project_version_matrix.md`.

### T8: Verificar que não há regressão no pipeline `run`

```bash
PYTHONPATH=apps/data-processing/src uv run python -m data_processing.cli run --help
```

**Critério de conclusão:** `run` continua funcionando com mesma interface.

### Fora de escopo

- Alterar `convert`
- Alterar `stage_router.py`
- Alterar `skill_registry.yaml` ou `llm_registry.yaml` (exceto se modelo precisar trocar)
- Alterar skills canônicas
- Alterar `.env`
- Alterar testes existentes
- Fazer commit
- Arquivar change
