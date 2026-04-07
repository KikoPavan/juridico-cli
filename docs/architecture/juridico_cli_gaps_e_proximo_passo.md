# Gaps e Próximo Passo — `juridico-cli`

**Data:** 2026-04-05
**Referência:** `docs/architecture/juridico_cli_documento_mestre.md` + `juridico_cli_estado_real_implantado.md`

---

## 1. Gaps Reais

### Gap 1 — 2 skills operacionais sem registro no runtime
**O que:** 2 skill dirs existem em `platform/skills/` com `SKILL.md` completo, estrutura canônica (`assets/`, `references/`, `scripts/`) e conteúdo jurídico real, mas não estão no `skill_registry.yaml`:
- `jus-breve` (`platform/skills/jus-breve/`) — análise FIRAC com barreira fática
- `jus-diagnose` (`platform/skills/jus-diagnose/`) — análise IRAC / triagem jurídica

**Impacto:** Alto. As 2 skills operacionais não são despacháveis pelo `skill_dispatcher.py`, violando a regra canônica: "skill nova só roda se estiver registrada".

**Prioridade:** 🔴 Alta

---

### Gap 2 — Validação funcional das 3 skills genéricas do pipeline
**O que:** `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml` estão criadas, com `SKILL.md` completo, estrutura mínima (`assets/`, `references/`, `scripts/`) e registradas no `skill_registry.yaml` com perfil `local_preprocessing`. Não há evidência de execução ponta a ponta validada (testes automatizados ou logs de sucesso).

**Impacto:** Médio. O pipeline genérico está "pronto no papel" mas sem prova de funcionamento real.

**Prioridade:** 🟡 Média

---

### Gap 3 — `legal-research` sem contrapartida operacional
**O que:** O documento mestre (Seção 10) lista `apps/legal-research/` como previsto. As responsabilidades de orquestração e core (`legal-core`, `orchestrator-cli`) foram absorvidas de facto por `apps/data-processing/`. Mas as responsabilidades de pesquisa jurídica (`legal-research`) permanecem sem implementação — os agentes legados `agents/case-law-cli/` e `agents/law-cli/` continuam congelados sem migração.

**Impacto:** Baixo. O documento mestre classifica esses módulos como "não tratados como frente ativa imediata".

**Prioridade:** 🟢 Baixa (não é frente ativa)

---

### Gap 4 — Scripts avulsos na raiz do repositório
**O que:** `scripts/` na raiz contém 15 scripts Python (rag_service.py, precedent_finder.py, index_library_qdrant.py, genai_adapter.py, etc.) fora do modelo skill-centric.

**Impacto:** Baixo-Médio. Fora do caminho canônico. Podem criar duplicação com funcionalidades já existentes nas skills ou em `data-processing`.

**Prioridade:** 🟡 Média

---

### Gap 5 — Testes de `data-processing` sem evidência de execução recente
**O que:** `apps/data-processing/tests/` contém 3 arquivos de teste (`test_cleaners.py`, `test_rule_analysis.py`, `test_validation.py`). Não há evidência de que foram executados com sucesso recentemente.

**Impacto:** Baixo-Médio. Sem validação automatizada comprovada, a confiabilidade do módulo operacional único não é verificável.

**Prioridade:** 🟡 Média

---

## 2. Itens que NÃO são gaps técnicos atuais

### Legado congelado (`agents/`, `pipelines/`, `main.py` raiz, diretórios diversos)
O documento mestre (Seção 3) já classifica `agents/` na raiz e partes antigas de `pipelines/` como "legado congelado e não fonte de verdade". O descomissionamento ou arquivamento depende de **gate explícito**. Não é gap técnico — é estado intencional até decisão de remoção.

### `packages/shared-core`, `shared-legal`, `shared-utils` (diretórios vazios)
Esses diretórios contêm apenas `.gitkeep`. O documento mestre não os nomeia individualmente como requisitos vigentes — apenas designa `packages/` como camada de "componentes compartilhados" de forma genérica. Nenhum código do projeto os referencia. Não há impacto funcional comprovado. **Não são classificados como gap.**

### `platform/continuous-learning/` e `platform/memory-and-experiences/`
Correspondem à "expansão futura compatível" do documento mestre (Seção 9: Mem0, RLM). São previstos, não pendentes.

---

## 3. Resumo de Impacto por Prioridade

| Prioridade | Gap | Ação resumida |
|------------|-----|---------------|
| 🔴 Alta | Gap 1 — 2 skills operacionais sem registro | Registrar `jus-breve`, `jus-diagnose` |
| 🟡 Média | Gap 2 — Validação do pipeline genérico | Executar ponta a ponta com PDF de teste |
| 🟡 Média | Gap 4 — Scripts avulsos | Classificar um a um: útil, legado ou arquivar |
| 🟡 Média | Gap 5 — Testes sem evidência | Executar e registrar resultado |
| 🟢 Baixa | Gap 3 — `legal-research` sem implementação | Manter como previsto (não é frente ativa) |

---

## 4. Próximo Passo Recomendado

### Passo imediato (alinhamento ao modelo skill-centric)

1. **Registrar as 2 skills operacionais** — Adicionar ao `skill_registry.yaml`:
   - `jus-breve` → profile: `high_reasoning` (análise FIRAC complexa)
   - `jus-diagnose` → profile: `fast_extraction` (triagem IRAC rápida)
   Cada uma precisa de `schema_ref` apontando para seu `assets/*.schema.json`.

2. **Validar execução do pipeline genérico** — Executar com um PDF de teste:
   ```
   pdf-to-md → md-clean-markdown → md-frontmatter-yaml
   ```
   Verificar saídas em `var/output/`. Registrar evidência.

### Passo seguinte (evolução controlada)

3. **Executar testes de `data-processing`** — Rodar `pytest apps/data-processing/tests/` e registrar resultado.

4. **Classificar scripts da raiz** — Para cada script em `scripts/`: manter como ferramenta, mover para skill correspondente, ou arquivar.

---

## 5. Foco: Manter Alinhamento ao Modelo Skill-Centric

O projeto está **majoritariamente alinhado** ao modelo skill-centric:

- ✅ Runtime, dispatcher, registries operacionais
- ✅ 3 skills genéricas do pipeline criadas e registradas
- ✅ 10 skills de extração registradas (`extr-*`)
- ✅ `apps/data-processing` operacional com orquestrador interno
- ✅ Infraestrutura mínima Docker definida

A pendência **operacional** é registrar as 2 skills operacionais (`jus-breve`, `jus-diagnose`). Sem isso, não são despacháveis, mas também não bloqueiam as 15 skills já funcionais (13 registradas + 3 do pipeline).
