# QWEN.md — Contexto Permanente do Projeto `juridico-cli`

## Status
Contexto permanente para agentes executores auxiliares.

## Finalidade
Este arquivo fornece contexto estável e duradouro sobre o projeto `juridico-cli`.

Ele não substitui os documentos canônicos do projeto.
Ele não deve conter instruções temporárias de tarefa.
Toda tarefa pontual deve ser descrita separadamente em arquivos próprios, por exemplo em:

`docs/qwen_tasks/`

---

## 1. Fontes prioritárias do projeto

### Fonte principal de intenção
`docs/architecture/juridico_cli_documento_mestre.md`

### Fonte principal de estado real
`docs/architecture/juridico_cli_estado_real_consolidado.md`

### Documento que melhor representa o projeto vigente
`docs/architecture/juridico_cli_arquitetura_evolutiva.md`

### Contexto técnico complementar
`_bmad-output/project-context.md`

### Espelho formal do estágio atual
`_bmad-output/implementation-artifacts/implementation-state.md`

### Apoio operacional
`docs/runbooks/runbook_operacional_minimo.md`

### Apoio histórico
`docs/archive/juridico-cli/`

---

## 2. Regra de precedência documental

Se houver divergência entre documentos:

1. o estado real deve ser lido em `docs/architecture/juridico_cli_estado_real_consolidado.md`;
2. a visão integrada do projeto vigente deve ser lida em `docs/architecture/juridico_cli_arquitetura_evolutiva.md`;
3. `docs/architecture/juridico_cli_documento_mestre.md` permanece como fonte de intenção, não como fonte única do estágio atual;
4. `_bmad-output/implementation-artifacts/implementation-state.md` registra o estágio operacional corrente para continuidade entre agentes.

---

## 3. Visão geral do projeto

O `juridico-cli` é um monorepo Python 3.12+ voltado a processamento documental jurídico com uso de LLMs.

O projeto é brownfield e evolui de forma incremental sobre um baseline já aceito.

O domínio principal é jurídico, mas parte do pipeline documental base pode ser genérica e reutilizável para outros tipos de documento.

---

## 4. Decisão arquitetural vigente

A arquitetura oficial do projeto é modular por domínio funcional e centrada em skills.

### Regras canônicas
- A unidade canônica do sistema é a skill.
- Não existe mais arquitetura oficial baseada em agentes separados de prompts e skills.
- O runtime canônico é `platform/skill-runtime/`.
- O ponto oficial de despacho é `platform/skill-runtime/skill_dispatcher.py`.
- A camada canônica de habilidades é `platform/skills/`.
- `agents/` na raiz e partes antigas de `pipelines/` são legado congelado e não fonte de verdade.

---

## 5. Estrutura lógica do repositório

```text
juridico-cli/
├── apps/
├── platform/
│   ├── skill-runtime/
│   └── skills/
├── packages/
├── var/
├── infra/
├── docs/
├── scripts/
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
