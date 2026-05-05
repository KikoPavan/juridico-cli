# CLAUDE.md — juridico-cli

## Projeto

Monorepo Python para processamento documental e jurídico.

Arquitetura **skill-centric** com separação explícita entre módulos funcionais, skills canônicas, runtime de execução, documentação operacional e fluxo OpenSpec.

Documentos de referência:
- `docs/architecture/juridico_cli_documento_mestre.md` — arquitetura-alvo canônica
- `docs/runbooks/runbook_operacional_minimo.md` — estado operacional atual
- `docs/reference/project_version_matrix.md` — versões validadas de ferramentas
- `openspec/config.yaml` — contexto e regras globais do OpenSpec

---

## Language & Communication Rules

- Responda exclusivamente em português do Brasil (pt-BR), independentemente do idioma do prompt.
- Se o prompt estiver em outro idioma, interprete internamente conforme necessário, mas mantenha a resposta em pt-BR.
- Se o usuário solicitar uma tradução, forneça a tradução pedida, mantendo em pt-BR todas as instruções, explicações e contextualizações adicionais.
- Escreva todo o código em inglês, incluindo nomes de variáveis, funções, classes, schemas de banco de dados, chaves de configuração e comentários.
- Escreva mensagens de commit em inglês, seguindo o padrão Conventional Commits.

---

## Estrutura canônica

```
apps/              # módulos funcionais (fluxos implantáveis por domínio)
platform/
  skill-runtime/   # runtime canônico: dispatcher, bundle_loader, registries
  skills/          # skills canônicas (capacidades reutilizáveis)
packages/          # componentes compartilhados
infra/             # infraestrutura local (Docker, Qdrant)
var/               # dados operacionais de runtime
docs/              # documentação oficial
openspec/          # changes, specs e config do fluxo OpenSpec
```

Módulo operacional ativo: `apps/data-processing/`

---

## Regras arquiteturais

- **Skill ≠ módulo funcional.** `platform/skills/` define capacidades reutilizáveis. `apps/` define fluxos implantáveis que usam essas capacidades.
- Skill nova só é operacional após: existir em `platform/skills/<nome>/`, ter `SKILL.md` válido, estar registrada em `skill_registry.yaml`, usar profile em `llm_registry.yaml` e ser resolvível pelo dispatcher.
- O runtime canônico é `platform/skill-runtime/`. Não criar arquiteturas paralelas de loading ou despacho.
- Especialização jurídica é camada superior ao pipeline documental genérico — não misturar.
- Legado pode existir preservado, mas não governa a arquitetura.

---

## Stack operacional atual

- Gemini via API
- LM Studio como runtime local provisório para LLMs (não é modelo — é runtime)
- Endpoint local OpenAI-compatible como protocolo de API
- Qdrant local
- Docker Desktop para serviços locais

Variáveis LLM local: usar `LOCAL_LLM_*`. Não usar `OPENAI_BASE_URL` como variável canônica.
llama.cpp Docker: não tratar como validado até estabilidade operacional confirmada.

Antes de recomendar ferramenta, extensão, CLI ou runtime: consultar `docs/reference/project_version_matrix.md`. Não inventar versões.

---

## Fluxo OpenSpec

Mudanças no projeto seguem o fluxo OpenSpec:
1. **Propose** — proposta com objetivo, escopo e fora de escopo
2. **Design** — somente quando houver decisão técnica real
3. **Specs** — requisitos verificáveis
4. **Tasks** — etapas pequenas, ordenadas, com critério de conclusão
5. **Apply** — executar somente o que estiver em `tasks.md`
6. **Archive** — somente após revisão humana

Skills disponíveis: `/openspec-propose`, `/openspec-apply-change`, `/openspec-archive-change`, `/openspec-explore`

---

## Regras de execução

- Executar somente o que estiver descrito em `tasks.md`. Não expandir escopo durante apply.
- Validar arquivos alterados antes de concluir.
- Não alterar código em changes exclusivamente documentais.
- Não alterar `.agent/`, `.claude/`, `.gemini/`, `.codex/`, `.opencode/` salvo se a change pedir explicitamente.
- Manter revisão humana antes de sync ou archive.
- Não reintroduzir BMAD, agentes antigos ou documentação legada.
- Módulos `document-processing`, `process-processing` e `legal-knowledge` ainda não estão implantados — não tratar como existentes.

---

## Scripts Python inline

Usar `uv run python - <<'PY'` para scripts Python inline. Nunca `-c "..."` com código multilinha.
