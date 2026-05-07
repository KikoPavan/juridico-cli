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
- stack operacional atual:
  - Gemini via API;
  - LM Studio como runtime local provisório para LLMs;
  - endpoint local compatível com OpenAI;
  - Qdrant local;
  - Docker Desktop para serviços locais e infraestrutura de apoio;
  - llama.cpp local/Docker como alternativa técnica futura, ainda não estabilizada.

## 2.1. Decisão operacional temporária sobre LLM local

No estado operacional atual, o LM Studio substitui provisoriamente a execução local de LLM via Docker/llama.cpp.

Essa decisão não altera a arquitetura skill-centric do projeto.

Regras operacionais:

- tratar LM Studio como runtime local, não como modelo;
- usar endpoint compatível com OpenAI apenas como protocolo de API;
- não usar `OPENAI_BASE_URL` como variável canônica do projeto;
- preferir variáveis neutras `LOCAL_LLM_*`;
- manter llama.cpp local/Docker como alternativa técnica futura;
- não tratar llama.cpp Docker como validado enquanto não houver estabilidade operacional no ambiente real.

---

## 3. Módulo operacional atual

O módulo operacional vigente é:

`apps/data-processing/`

Os módulos funcionais previstos na arquitetura-alvo são:

- `apps/document-processing/`
- `apps/process-processing/`
- `apps/legal-knowledge/`

Esses módulos ainda não devem ser tratados como implantados neste runbook.

---

## 4. Próxima frente ativa

Criar as três skills genéricas do pipeline documental:

1. `pdf-to-md`
2. `md-clean-markdown`
3. `md-frontmatter-yaml`

A skill `pdf-to-md` deve seguir a decisão arquitetural vigente: usar PaddleOCR como mecanismo OCR canônico para PDFs ilegíveis, escaneados ou com baixa extração textual.

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
- [ ] Os módulos `document-processing`, `process-processing` e `legal-knowledge` não estão sendo tratados como implantados.
- [ ] O LM Studio está sendo tratado como runtime local provisório para LLM.
- [ ] llama.cpp Docker não está sendo tratado como validado.
- [x] A skill `pdf-to-md` preserva PaddleOCR como OCR canônico.
- [ ] Skill nova só roda após registro no runtime.
