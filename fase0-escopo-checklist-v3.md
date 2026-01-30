# Plan: Fase 0 - Alinhamento e Checklist Operacional (v3)

## Visão Geral
Esta é a versão operacional (v3) do plano da **Fase 0**, refinada para ser estritamente **Read-Only** e não intrusiva. O objetivo é validar o workspace do `juridico-cli` garantindo que os pré-requisitos fundamentais para a execução de pipelines (Fase 1) estejam atendidos, alinhado aos princípios **PROCESS-FIRST** e **Run First, Refine Later**.

Este documento substitui o anterior `fase0-escopo-checklist-v2.md`.

## Tipo de Projeto
**CLI / DATA PIPELINE** (Python + DuckDB)

## Critérios de Sucesso
- [ ] **Bloco A (Layout):** Todos os diretórios e arquivos canônicos existem. Resultado: OK/FAIL.
- [ ] **Bloco B (Permissões):** Diretórios de saída são graváveis. Resultado: OK/FAIL.
- [ ] **Bloco C (Pipelines):** Runtime Python e dependências mínimas identificáveis. Resultado: OK/FAIL.
- [ ] **Data da Validação:** ______

## Estrutura de Validação
A validação deve ser feita manualmente executando os comandos read-only listados.

### A. Layout do Repo
Verifica a estrutura estática conforme definido em `docs/antigravity/juridico-cli/INDEX.md#Workspace layout (do not confuse)`.

| Item | Comando (read-only) | Resultado Esperado | Ação se Falhar |
| ------ | --------------------- | -------------------- | ---------------- |
| **Antigravity Tooling** | `test -d .agent && echo "OK" \|\| echo "MISSING"` | `OK` | Registrar FAIL e corrigir setup manualmente. |
| **Agent Code** | `test -d agents && echo "OK" \|\| echo "MISSING"` | `OK` | Registrar FAIL e avaliar restauração. |
| **Pipelines** | `test -d pipelines && echo "OK" \|\| echo "MISSING"` | `OK` | Registrar FAIL e avaliar restauração. |
| **Outputs Dir** | `test -d outputs && echo "OK" \|\| echo "MISSING"` | `OK` | Registrar FAIL. Criar manualmente apenas sob confirmação. |
| **Artifacts Dir** | `test -d artifacts && echo "OK" \|\| echo "MISSING"` | `OK` | Registrar FAIL. Avaliar estrutura de dados. |
| **Canonical Context** | `test -f docs/antigravity/juridico-cli/INDEX.md && echo "OK" \|\| echo "MISSING"` | `OK` | **CRÍTICO:** Parar. Contexto obrigatório. |

### B. Gravabilidade e Permissões
Verifica se há condições de escrever nos diretórios de destino das rotas críticas (`firac`, `cad_obr`).

| Item | Comando (read-only) | Resultado Esperado | Ação se Falhar |
| ------ | --------------------- | -------------------- | ---------------- |
| **Output Root Writable** | `[ -w outputs ] && echo "WRITABLE" \|\| echo "LOCKED"` | `WRITABLE` | Registrar FAIL. Corrigir permissões (`chmod`) manualmente. |
| **Artifacts Root Writable** | `[ -w artifacts ] && echo "WRITABLE" \|\| echo "LOCKED"` | `WRITABLE` | Registrar FAIL. Corrigir permissões manualmente. |
| **DuckDB Lock Check** | `if [ -f artifacts/db/cad_obr_dataset_v1.duckdb ]; then lsof artifacts/db/cad_obr_dataset_v1.duckdb 2>/dev/null \|\| echo "FREE"; else echo "NO_DB"; fi` | `FREE` ou `NO_DB` | Registrar FAIL. Encerrar processo concorrente manualmente. |

### C. Condições Mínimas para Rodar Pipelines
Verifica o ambiente de execução sem instalar nada.

| Item | Comando (read-only) | Resultado Esperado | Ação se Falhar |
| ------ | --------------------- | -------------------- | ---------------- |
| **Python Version** | `uv run python -V 2>/dev/null \|\| python3 -V` | `Python 3.10+` | Registrar FAIL. Verificar instalação do `uv` ou `python`. |
| **UV Instalado** | `uv --version 2>/dev/null && echo "OK" \|\| echo "MISSING"` | `OK` | Considerar instalar `uv` (não obrigatório, mas recomendado). |
| **Git Status** | `git status -s` | (Limpo ou esperado) | Registrar estado. Commit/Stash manual recomendado antes de rodar. |

## Riscos e Mitigação
- **Risco:** Diretórios de saída com permissão de root (docker antigo).
    - **Mitigação:** Verificar Bloco B antes de rodar qualquer agente.
- **Risco:** Arquivo de contexto desatualizado.
    - **Mitigação:** Verificar data em `docs/antigravity/juridico-cli/INDEX.md` (metadata `updated_at`).

## Referências
- [INDEX.md](docs/antigravity/juridico-cli/INDEX.md) - Contexto Canônico e layout de pastas.
- [03_Arquitetura_Sistema_EndToEnd_juridico-cli.md](docs/antigravity/juridico-cli/03_Arquitetura_Sistema_EndToEnd_juridico-cli.md) - Detalhe da estrutura de pastas (ver "Pilares de arquitetura").
- [05_Runbook_Operacoes_Fallbacks_e_Incidentes.md](docs/antigravity/juridico-cli/05_Runbook_Operacoes_Fallbacks_e_Incidentes.md) - Procedimentos operacionais.

## ✅ Fase X: Verificação Final
- [x] Bloco A (Layout):
- [x] Bloco B (Permissões):
- [x] Bloco C (Pipelines):
- [x] Data: 30/01/2026
