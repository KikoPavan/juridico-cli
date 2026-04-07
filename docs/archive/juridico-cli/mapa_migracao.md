> [!WARNING]
> **DOCUMENTO HISTÓRICO — NÃO É A FONTE PRINCIPAL DA ARQUITETURA**
> Este documento descreve o plano de migração já executado. O estado atual está no documento canônico.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Mapa de Migração e Arqueologia do Código: Juridico-CLI

## 1. Arqueologia: De onde estamos partindo
Conforme diagnosticado na Fase 1, o código hoje está fragmentado entre um formato procedural/estruturado não centralizado e tentativas dispersas de seguir a arquitetura alvo.

**Pontos Genéricos Atuais (Legacy):**
* As lógicas de extração e prompts estão misturados sem contrato (vazando em `prompts/`, `skills/` e `agents/*/skills/`).
* Orquestração engessada (`pipelines/` chama scripts de extração imperativamente).
* Ambientes de I/O em runtime vazando para a raiz (`data/`, `input/`, `outputs/`, `logs/`, `artifacts/`).

## 2. Mapa de Destino: Onde vamos chegar
A arquitetura `v1.1` e `v1.2` dita um repositório centralizado, operado como monorepo.
* **`apps/`**: Apenas as CLIs / Entrypoints (Frontend do backend). Orquestração isolada por domínio (`data-processing`, `ingest`). Não armazenam lógicas de LLM.
* **`platform/`**: O motor inteligente. Inclui `bundle_loader.py`, `llm_registry` e todos os **Skill Bundles** no formato Co-Located (cada skill tem seu prompt, schema e agente restrito na mesma pasta `platform/skills/nome-skill/`).
* **`packages/`**: Integrações estáticas que são consumidas (banco, vetorização, `shared-schemas`, utilitários).
* **`var/`**: Memória híbrida (Mem0 + TurboQuant), caches, dados transientes e relatórios (`run_outputs`, `logs`, `cache`).

## 3. Roteiro e Plano de Migração

### Fase 0: Transversais e Infraestrutura Core (Foco Atual)
* **Status:** Implantação Imediata. Não impactam os scripts rolando atualmente.
* **Ações:**
  1. Criar o contrato base de abstração para as extrações em `platform/skills/_shared/extraction-base.md`.
  2. Desenvolver a lógica central no `bundle_loader.py` capaz de ler um skill bundle em `platform/skills/` e injetar a base transversal dinamicamente.
  3. Migrar o motor de prompts e criação/teste de skills (`skill-creator`) e sua interface para a estrutura oficial.
* **Critério de Aceite:** O `bundle_loader.py` consegue compilar um payload (Prompt + Schema + Regras Transversais) completo em memória sem depender de arquivos soltos.

### Fase 1: Centralização de Dependências
* **Status:** Desacoplamento do LLM e registro global.
* **Ações:**
  1. Transferir os arquivos de schemas soltos na raiz para a biblioteca oficial em `packages/shared-schemas/`.
  2. Implementar a interface uniciada `LLMClient` dentro de `packages/shared-llm/`.
  3. Definir os registros canônicos no `platform/skill-runtime/` (`llm_registry.yaml` e `skill_registry.yaml`).
* **Critério de Aceite:** Ferramentas são capazes de chamar um LLM lendo chaves e registros em um único lugar no projeto.

### Fase 2: Refatoração dos Agentes para Skill Bundles Co-Located
* **Status:** O coração do projeto - reescrevendo o workflow extrativo.
* **Ações:**
  1. Eliminar o diretório solto de skills na raiz de cada pasta de `agents/`.
  2. Transformar casos como `collector-cad_obr` e `collector-proc` em diretórios de skills puros localizados em `platform/skills/extr-cadastro/`, `platform/skills/extr-processos/`.
  3. Assegurar que os schemas de Validação (JSON) relativos a estas skills coabitam no respectivo diretório do bundle.
* **Critério de Aceite:** As rotinas de extração não dependem de nada executável dentro da antiga pasta `agents/`.

### Fase 3: Roteamento via Entrypoints (`apps/`)
* **Status:** Refatoração de Entrypoint e Orquestração (`orchestrator`).
* **Ações:**
  1. Excluir o legadíssimo `main.py` corrompido na raiz da árvore.
  2. Criar as CLIs autônomas dentro de `apps/data-processing/` que funcionarão apenas invocando o motor de roteamento e injeção do `bundle_loader.py`.
  3. Redirecionar os subprodutos gerados por estas ferramentas do disco estático nativo para caminhos sob `var/`.
* **Critério de Aceite:** 100% dos fluxos diários são gerados pelo comando `python apps/data-processing/src/main.py --skill extr-cadastro`, e todo output vai para `var/data/` ou `var/logs/`.

### Fase 4: Limpeza do Passado e "Stop Bleeding"
* **Status:** Estabilidade na Gestão da Informação.
* **Ações:**
  1. Excluir com segurança as pastas `agents/`, `pipelines/estáticos antigos`, `schemas/raiz`, `prompts/raiz`, `skills/raiz` que não servem mais a nenhum bundle migrado.
  2. Deletar `data/`, `outputs/` e afins da raiz do repositório, garantindo que o `.gitignore` varra as origens do `var/`.
* **Critério de Aceite:** Raiz do repositório sem a presença de lixo de execução.

## Restrições Críticas da Arqueologia
- **Do Not Break Production:** Os processos em `pipelines/cad_obr.py` estão rodando. Nenhuma alteração neles pode ser feita antes que a CLI de `apps/` correspondente atinja paridade na homologação (Teste do bundle carregado por `bundle_loader`).
- **Nomenclatura Padrão:** O padrão para novos e existentes módulos a operar no core extrativo são `platform/skills/`.

---
*Documento forjado via inteligência @code-archaeologist fundamentando a transição `v1.1` e `v1.2`.*
