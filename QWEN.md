# QWEN.md — Contexto Permanente do Projeto `juridico-cli`

## Status
Contexto permanente para agentes executores.

## Finalidade
Este arquivo existe para fornecer ao executor um contexto estável e duradouro sobre o projeto `juridico-cli`.

Ele não substitui o documento mestre do projeto e não deve conter instruções temporárias de tarefa.

Toda tarefa pontual deve ser descrita separadamente em arquivos próprios dentro de:

`docs/qwen_tasks/`

---

## 1. Fonte principal do projeto

A referência principal e obrigatória do projeto é:

`docs/architecture/juridico_cli_documento_mestre.md`

Documento auxiliar operacional:

`docs/runbooks/runbook_operacional_minimo.md`

Se qualquer documento antigo ou histórico divergir destes, os documentos acima prevalecem.

---

## 2. Visão geral do projeto

O `juridico-cli` é um monorepo em Python 3.12+ para processamento documental e jurídico com uso de LLMs.

O projeto está organizado em torno de uma arquitetura **skill-centric**, com runtime canônico próprio, infraestrutura local mínima e separação entre módulos funcionais, bundles de skills e componentes compartilhados.

O domínio principal do projeto é jurídico, mas parte do pipeline documental base pode ser genérica e reutilizável para outros tipos de documento.

---

## 3. Decisão arquitetural vigente

A arquitetura oficial do projeto é **modular por domínio funcional e centrada em skills**.

### Regras canônicas
- A unidade canônica do sistema é a **skill**.
- Não existe mais arquitetura oficial baseada em agentes separados de prompts e skills.
- O runtime canônico é `platform/skill-runtime/`.
- O ponto oficial de despacho é `platform/skill-runtime/skill_dispatcher.py`.
- A camada canônica de habilidades é `platform/skills/`.
- `agents/` na raiz e partes antigas de `pipelines/` são legado congelado e não fonte de verdade.

---

## 4. Estrutura lógica do repositório

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

