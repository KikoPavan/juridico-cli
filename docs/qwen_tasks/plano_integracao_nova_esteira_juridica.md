# Plano Técnico Final de Integração — Nova Esteira Jurídica

**Projeto:** `juridico-cli`
**Data:** 2026-04-12
**Escopo:** Integração de `segmentador-juridico`, `curador-relevancia` e `yaml-normalizador-juridico` ao pipeline executável
**Restrição:** Este documento é **somente um plano técnico**. Nenhuma linha de código foi alterada. Nenhuma implementação foi realizada.

---

## BLOCO 1 — Leitura do Ponto Real de Integração

### 1.1 Onde o pipeline está hoje (código real, não hipótese)

O pipeline executável atual (`PipelineRunner` em `pipeline_runner.py`) executa **6 etapas sequenciais** sobre arquivos de entrada:

```
convert → clean → analyze → collect → validate → load
```

**Após `clean`**, o fluxo real é:

1. **`clean`** recebe Markdown (de `convert` ou direto do input), roda `LegalDocCleaner.clean_batch()`, escreve em `staging/`.
2. **`analyze`** roda `GeradorDeRegras` (detecção de frases repetidas) e **injeta frontmatter YAML** em cada `.md` do staging. Este frontmatter contém: `document_type`, `skill_key`, `target_schema`, `source_sha256`, etc. O `document_type` é inferido por heurística de nome de arquivo (`DOC_TYPE_HINTS`), com default `peticao_processo`.
3. **`collect`** lê os `.md` do staging, parseia o frontmatter para obter `skill_key`, e despacha cada arquivo **individualmente** para `DataExtractorApp.run_extraction(bundle_id=f"extr-{skill_key}", input_filename=...)`. O extractor lê de `var/staging/`, despacha via `SkillDispatcher`, e escreve JSON em `var/output/`.
4. **`validate`** e **`load`** rodam dentro do collector e atualizam o index registry.

**Fato confirmado:** O pipeline atual trata cada `.md` do staging como **um documento independente** — itera `for md_file in md_files` e despacha um por um. **Não há iteração sobre `pecas[]` de um envelope.**

### 1.2 Onde a nova esteira deve se encaixar (proposta, não implementado)

A nova esteira jurídica (`segmentador-juridico` → `curador-relevancia` → `yaml-normalizador-juridico`) opera sobre um **modelo radicalmente diferente** do pipeline atual:

| Pipeline atual (baseline) | Nova esteira jurídica (proposta) |
|---|---|
| 1 arquivo `.md` → 1 JSON de extração | 1 arquivo `.md` limpo → Envelope JSON com `pecas[]` → N arquivos `.md` normalizados → N JSONs de extração |
| Iteração: 1:1 (arquivo → extração) | Iteração: 1:N (documento → peças → extrações individuais) |
| Frontmatter injetado por `analyze` (heurístico) | Frontmatter injetado por `yaml-normalizador-juridico` (LLM-curado) |
| `collect` despacha `extr-*` diretamente | A nova esteira deve rodar **antes** do `collect`, produzindo os `.md` normalizados que o `collect` consumirá |

**Ponto de encaixe proposto:** após `clean`, substituindo `analyze` no ramo da nova esteira.

Justificativa: o `analyze` atual injeta frontmatter com `document_type` inferido por heurística de nome de arquivo. A nova esteira substitui essa inferência heurística por **segmentação real por LLM** + curadoria + normalização. Manter o `analyze` heurístico junto da nova esteira geraria redundância e conflito de metadados.

### 1.3 O que já existe no código vs o que é proposta

| Item | Estado |
|---|---|
| `segmentador-juridico` registrada no `skill_registry.yaml` | ✅ Fato confirmado |
| `curador-relevancia` registrada no `skill_registry.yaml` | ✅ Fato confirmado |
| `yaml-normalizador-juridico` registrada no `skill_registry.yaml` | ✅ Fato confirmado |
| Skills com SKILL.md, schemas, scripts e exemplos | ✅ Fato confirmado |
| Validação contratual entre skills (A→B→C) compatível no mérito | ✅ Fato confirmado |
| Saneamento de enums do normalizador (`acao_curatorial`, `impacto_sentenca_confirmado`) | ✅ **Resolvido** — verificado em `example_output.md`, `example_input.json`, `apply_yaml_normalization.py`, `validate_yaml_normalizador_juridico.py` e `io.schema.json` |
| Integração no pipeline executável (`pipeline_runner.py`) | ❌ **Não implementada** — proposta |
| Nova etapa no `PipelineRunner` | ❌ **Não implementada** — proposta |
| Iteração sobre `pecas[]` e roteamento por peça | ❌ **Não implementado** — proposta |
| `DataExtractorApp` usa `DummyLLMClient` — extração real não funciona | ⚠️ Fato confirmado — risco para E2E real, mas não bloqueia integração da esteira |

---

## BLOCO 2 — Plano Técnico Final de Integração

### 2.1 Mapa da Sequência de Execução (proposta)

```
convert → clean → [NOVA ESTEIRA] → collect → validate → load
                      │
                      ├── segmentador-juridico
                      │     entrada: *.md limpo (pós-clean, com marcadores de página)
                      │     saída:   envelope_segmentacao.json ({metadata, pecas[]})
                      │
                      ├── curador-relevancia
                      │     entrada: envelope_segmentacao.json
                      │     saída:   envelope_curadoria.json ({metadata, pecas[]} enriquecido)
                      │
                      └── yaml-normalizador-juridico (N vezes, 1 por peça elegível)
                            entrada: pecas[i] individual do envelope curado
                            saída:   {process_group_id}__{piece_id}.md com frontmatter YAML
                                      → gravado em var/staging/

                           ↓ retorno ao baseline ↓

                collect (itera sobre os .md normalizados do staging)
                → dispatch extr-{skill_key} por peça
                → JSON por peça em var/output/
                → validate → load
```

### 2.2 Artefatos por Etapa

| Etapa | Artefato de Entrada | Artefato de Saída | Formato |
|---|---|---|---|
| **clean** (existente) | PDFs convertidos ou `.md` brutos | `.md` limpos em `staging/` | Markdown com marcadores de página |
| **segmentador-juridico** (nova) | `.md` limpo (pós-clean) de `staging/` | `envelope_segmentacao.json` | JSON — Envelope de Processo (`{metadata, pecas[]}`) validado por `output-schema.json` v1.1.0 |
| **curador-relevancia** (nova) | `envelope_segmentacao.json` | `envelope_curadoria.json` | JSON — Envelope Curado (mesma estrutura com campos curatoriais por peça) validado por `schema_saida.json` v1.1.0 |
| **yaml-normalizador-juridico** (nova) | `pecas[i]` individual de `envelope_curadoria.json` | `{process_group_id}__{piece_id}.md` | Markdown com frontmatter YAML, gravado em `staging/` (substitui o `.md` original) |
| **collect** (existente, inalterado) | `.md` normalizados em `staging/` | JSONs de extração por peça | JSON — output das `extr-*` skills |

### 2.3 Como ocorre a iteração sobre `pecas[]`

**Proposta — três fases de iteração:**

1. **segmentador-juridico:** recebe **1 `.md` limpo** → produz **1 envelope** com `pecas[]` (array de N peças). Não há iteração aqui — a skill processa o documento inteiro de uma vez.

2. **curador-relevancia:** recebe **1 envelope** → produz **1 envelope curado** (mesma estrutura, peças enriquecidas). Também processa o envelope inteiro de uma vez.

3. **yaml-normalizador-juridico:** recebe **1 peça individual** (`pecas[i]`) → produz **1 `.md` com frontmatter**. **Esta etapa itera N vezes** — uma por peça elegível (`acao_curatorial != "remover"`). Cada iteração gera um arquivo `.md` independente em `staging/`.

4. **collect (existente):** já itera sobre `*.md` em `staging/` (linha `for md_file in md_files`). **Não precisa ser alterado** — consumirá os `.md` normalizados como se fossem documentos individuais, exatamente como já faz hoje.

### 2.4 Ponto de retorno ao baseline

Após o `yaml-normalizador-juridico` escrever todos os `.md` normalizados em `staging/`, o fluxo **retorna ao `collect`** exatamente onde estava antes. O `collect` já:

- Lê `*.md` de `staging/`
- Parseia frontmatter para obter `skill_key`
- Despacha para `DataExtractorApp.run_extraction(bundle_id=f"extr-{skill_key}", ...)`

A diferença é que, em vez de `.md` com frontmatter injetado pelo `analyze` (heurístico), agora os `.md` vêm do `yaml-normalizador-juridico` (LLM-curado). O contrato de frontmatter é **diferente** — precisa ser compatibilizado.

### 2.5 Arquivos/Áreas Impactados (proposta)

| Arquivo/Área | Tipo de impacto | Justificativa |
|---|---|---|
| `apps/data-processing/src/data_processing/orchestrator/pipeline_runner.py` | **Modificação** | Adicionar etapa(s) da nova esteira entre `clean` e `collect`; lógica de bypass do `analyze` |
| `apps/data-processing/src/data_processing/orchestrator/stage_router.py` | **Modificação** | Adicionar funções adapter: `run_segmentador_stage()`, `run_curador_stage()`, `run_normalizador_stage()` (loop sobre `pecas[]`) |
| `apps/data-processing/src/data_processing/cli.py` | **Possível adição** | Adicionar flag `--use-nova-esteira` ou similar no comando `run` para ativar/desativar a nova esteira |
| `apps/data-processing/src/data_processing/extractor.py` | **Sem alteração direta** | O extractor já despacha por `bundle_id`. Se os `.md` do staging tiverem `skill_key` correto no frontmatter, funciona sem changes |
| `platform/skills/yaml-normalizador-juridico/assets/routing_map.yaml` | **Sem alteração** | Já mapeia `document_type` → `skill_key` canonicamente |
| `platform/skill-runtime/skill_registry.yaml` | **Sem alteração** | As 3 skills já estão registradas |
| `platform/skills/yaml-normalizador-juridico/` (scripts, schemas, exemplos) | **Sem alteração** | Enums saneados — nomenclatura canônica (`acao_curatorial`, `impacto_sentenca_confirmado`) já alinhada em todos os arquivos |

### 2.6 Riscos

| # | Risco | Severidade | Mitigação |
|---|---|---|---|
| 1 | Compatibilidade final do frontmatter gerado pelo `yaml-normalizador-juridico` com o `collect` atual ainda não foi verificada formalmente no pipeline executável | 🔴 | Confirmar, em leitura de código e depois em integração controlada, que os campos mínimos esperados pelo `collect` (`document_type`, `skill_key` e correlatos) estão presentes e consumíveis sem adaptação destrutiva |
| 2 | O `analyze` atual pode sobrescrever ou conflitar com metadados da nova esteira se continuar ativo no mesmo ramo | 🔴 | No modo da nova esteira, definir bypass explícito do `analyze` heurístico ou adaptar o fluxo para impedir dupla injeção de frontmatter |
| 3 | A iteração sobre `pecas[]` ainda não existe no pipeline atual | 🟡 | Criar adapter/orquestração específica no `stage_router.py` ou equivalente, responsável por: ler o envelope curado, iterar peças elegíveis e chamar o normalizador por peça |
| 4 | A nova esteira aumenta o custo e a latência por adicionar segmentação, curadoria e normalização antes das `extr-*` | 🟡 | Tornar a esteira opt-in, medir volume de peças por documento e prever logs claros por etapa |
| 5 | Há risco de regressão do baseline se a nova esteira substituir o fluxo atual por padrão | 🔴 | A ativação deve ser explícita e o baseline `convert → clean → analyze → collect → validate → load` deve continuar íntegro como fallback |
| 6 | A escrita de artefatos intermediários da nova esteira pode colidir com o staging atual | 🟡 | Definir staging isolado ou convenção clara de nomes/paths para a nova esteira |

### 2.7 Pré-condições para Integração

| # | Pré-condição | Status atual |
|---|---|---|
| **PC1** | ~~Sanear divergência de enums no `yaml-normalizador-juridico`~~ | ✅ **Resolvido** — nomenclatura canônica (`acao_curatorial`, `impacto_sentenca_confirmado`) verificada em todos os artefatos da skill |
| **PC2** | Provar que `yaml-normalizador-juridico` gera frontmatter compatível com `run_collect_stage` (campos `document_type` + `skill_key` no topo do YAML) | ⚠️ **Parcial** — os campos existem no frontmatter de saída (`build_frontmatter_context` os produz), mas a compatibilidade de consumo pelo `collect` ainda não foi testada end-to-end |
| **PC3** | Definir se `analyze` será bypassed ou removido quando a nova esteira estiver ativa | ❌ **Não decidido** |
| **PC4** | Criar adapter `run_nova_esteira_stage()` no `stage_router.py` que orquestra as 3 skills + loop sobre `pecas[]` | ❌ **Não implementado** |
| **PC5** | Definir mecanismo de invocação das skills: via `SkillDispatcher` (canônico) ou via scripts diretos (`scripts/curar.py`, `scripts/apply_yaml_normalization.py`) | ❌ **Não decidido** |
| **PC6** | Garantir que o `SkillDispatcher` suporte `profile: large_context` e `profile: high_reasoning` com LLM real (não dummy) | ⚠️ **Parcial** — `DummyLLMClient` no extractor bloqueia E2E real, mas não a integração da esteira em si |
| **PC7** | Baseline atual preservado e funcionando como fallback | ✅ Baseline vigente |

### 2.8 Critérios para Não Quebrar o Baseline

1. **Opt-in obrigatório:** A nova esteira só ativa via flag CLI explícita (ex: `run --use-juridico-esteira`). Sem flag, o pipeline executa o baseline exato: `convert → clean → analyze → collect → validate → load`.

2. **Sem alteração nos contratos downstream:** O `collect` deve receber `.md` em `staging/` com o mesmo formato de frontmatter que já espera (`document_type` + `skill_key`). Se o normalizador gerar formato diferente, é o normalizador que se adapta — não o collect.

3. **Staging isolado:** Se viável, a nova esteira pode escrever em subdiretório próprio (`staging/juridico/`) para evitar colisão com o staging do baseline.

4. **Fail-fast com fallback:** Se qualquer etapa da nova esteira falhar (validação de schema, LLM indisponível), o pipeline deve abortar com mensagem clara — não silenciar nem prosseguir com dados incompletos.

5. **Nenhum arquivo do baseline modificado sem necessidade:** `pipeline_runner.py` e `stage_router.py` devem receber **adições**, não modificações destrutivas. O baseline permanece legível e funcional.

6. **Log de auditoria:** Cada execução da nova esteira deve gerar log identificável (ex: `extraction_nova_esteira_{run_id}.log`) separado dos logs do baseline.

---

**Fim do plano técnico final.** Nenhuma linha de código foi alterada. Nenhuma implementação foi realizada.
