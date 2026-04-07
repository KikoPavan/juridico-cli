# Runbook Operacional Mínimo — juridico-cli

## Status
Auxiliar operacional ativo, subordinado ao documento mestre.

## Referência principal
Este runbook não substitui a arquitetura do projeto.

A referência principal continua sendo:

`docs/architecture/juridico_cli_documento_mestre.md`

---

## 1. Finalidade
Este runbook existe para orientar a operação mínima do projeto no estado atual, sem redefinir arquitetura, escopo ou roadmap.

---

## 2. Base vigente do projeto
- arquitetura skill-centric;
- runtime canônico em `platform/skill-runtime/`;
- despacho canônico em `platform/skill-runtime/skill_dispatcher.py`;
- camada de skills em `platform/skills/`;
- stack oficial:
  - Gemini via API
  - llama.cpp local em Docker Desktop
  - Qdrant local
  - Docker Desktop

---

## 3. Módulo operacional atual
O módulo operacional vigente é:

`apps/data-processing/`

Os módulos abaixo continuam como previstos, sem tratamento como frente ativa imediata:
- `apps/legal-research/`
- `apps/legal-core/`
- `apps/orchestrator-cli/`

---

## 4. Próxima frente ativa
Criar as três skills genéricas do pipeline documental:

1. `pdf-to-md`
2. `md-clean-markdown`
3. `md-frontmatter-yaml`

### Regras obrigatórias
- criar do zero;
- não usar `agents/`;
- usar `SKILL.md` como instrução principal;
- incluir:
  - `assets/`
  - `references/`
  - `scripts/`
- manter conteúdo genérico e agnóstico de domínio.

---

## 5. Regras de integração
Uma skill nova só pode ser considerada operacional quando:

1. existir em `platform/skills/<nome>/`;
2. tiver `SKILL.md` válido;
3. estiver registrada em `platform/skill-runtime/skill_registry.yaml`;
4. usar profile válido em `platform/skill-runtime/llm_registry.yaml`;
5. puder ser resolvida pelo dispatcher.

---

## 6. Regras de manutenção
- não reintroduzir arquitetura baseada em agentes separados;
- não usar documento histórico como fonte de verdade;
- não misturar pipeline genérico com especialização jurídica sem decisão explícita;
- não tratar módulo previsto como implantado;
- manter runtime, docs e registries alinhados.

---

## 7. Estrutura documental ativa
Documentos ativos do projeto:

- `docs/architecture/juridico_cli_documento_mestre.md`
- `docs/runbooks/runbook_operacional_minimo.md`

Documentos antigos devem ficar em:

`docs/archive/juridico-cli/`

---

## 8. Checklist rápido
- [ ] O documento mestre existe e é a referência principal.
- [ ] O runtime canônico é `platform/skill-runtime/`.
- [ ] O dispatcher canônico é `skill_dispatcher.py`.
- [ ] O módulo ativo atual é `apps/data-processing/`.
- [ ] As próximas três skills ainda estão pendentes.
- [ ] Skill nova só roda após registro no runtime.
