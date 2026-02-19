# Plan: Fase 1 - Execução FIRAC-Core

## Visão Geral
Esta fase foca na execução do pipeline **FIRAC-Core** (PROCESS-FIRST), que é o caminho crítico primário do sistema. O objetivo é transformar documentos processuais brutos (Markdown) em um relatório FIRAC consolidado, passando pelo `collector-proc`.

**Cadeia de Execução:**
`data/processo/*.md` → `collector-proc` → `outputs/processo/01_collector/*.json` → `firac-cli` → `outputs/relatorio_firac.[json|md]`

## Tipo de Projeto
**CLI / DATA PIPELINE** (Python + Agentes LLM)

## Critérios de Sucesso
- [ ] **Entradas:** Arquivos Markdown em `data/processo/` com frontmatter válido.
- [ ] **Collector:** Execução de `collector-proc` gera JSONs estruturados em `outputs/processo/01_collector/`.
- [ ] **FIRAC:** Execução de `firac-cli` consome os outputs do collector e gera `relatorio_firac.json` (válido) e `relatorio_firac.md`.
- [ ] **Logs:** Ausência de erros críticos em `outputs/processo/99_logs/`.

## Estrutura de Execução

### Tarefa 1: Preparação de Entradas (Input)
- **Ação:** Garantir que `data/processo/` contenha arquivos `.md` válidos.
- **Requisito:** Cada arquivo deve ter frontmatter mínimo conforme `agents/collector-proc/config.yaml` (document_type, source_id, etc).
- **Verificação:** `grep -l "document_type:" data/processo/*.md`

### Tarefa 2: Execução do Collector-Proc
- **Comando:** `python agents/collector-proc/main.py` (ou ponto de entrada equivalente).
- **Saída Esperada:**
    - `outputs/processo/01_collector/*.json` (individuais)
    - `outputs/processo/01_collector/*.consolidated.json` (se configurado para consolidar)
- **Critério de Aceite:** Pelo menos um arquivo JSON gerado por arquivo de entrada; JSONs parseáveis.

### Tarefa 3: Execução do FIRAC-CLI
- **Comando:** `python agents/firac-cli/main.py`
- **Entrada:** Consome automaticamente de `outputs/processo/01_collector/` (conforme convenção).
- **Saída Esperada:**
    - `outputs/relatorio_firac.json` (Estrutura Faca/Regra/Aplicação/Conclusão)
    - `outputs/relatorio_firac.md` (Relatório legível)
- **Critério de Aceite:** `relatorio_firac.json` é um JSON válido e não está vazio.

## Riscos e Mitigação
- **Risco:** Falha de parseamento no Collector (JSON inválido do LLM).
    - **Mitigação:** Verificar logs em `outputs/processo/99_logs/`. Ajustar prompt se necessário (Fase de Refinamento).
- **Risco:** FIRAC alucinar fatos sem evidência.
    - **Mitigação:** Verificar se os `source_id` nos outputs do Collector estão preservados no FIRAC.

## Referências
- `docs/antigravity/juridico-cli/INDEX.md` (Base) - Contexto Canônico e fluxo FIRAC-Core.
- `docs/antigravity/juridico-cli/03_Arquitetura_Sistema_EndToEnd_juridico-cli.md#43-primary-must-run-firac-core-process-first` (Arquitetura) - Detalhe do fluxo primário.
- `agents/collector-proc/config.yaml` (Config) - Definição de paths de saída e schema de frontmatter.

## ✅ Fase X: Verificação Final
- [ ] Inputs preparados:
- [ ] Collector executado com sucesso:
- [ ] FIRAC executado com sucesso:
- [ ] Relatório gerado e válido:
- [ ] Data: ______
