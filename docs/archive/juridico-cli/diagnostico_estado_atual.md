> [!WARNING]
> **DOCUMENTO HISTÓRICO — NÃO É A FONTE PRINCIPAL DA ARQUITETURA**
> Este documento é um diagnóstico do estado pré-migração e não reflete a arquitetura atual.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Diagnóstico do Estado Atual do Projeto `juridico-cli`

Abaixo está o diagnóstico objetivo do estado real do repositório `juridico-cli`, com base no inventário da árvore de diretórios atual e na arquitetura definida nos arquivos de documentação (`espelho_estado_atual_juridico-cli.md`, `data_processing_pipelines.md` e `juridico_cli_arquitetura_final.md`):

### 1. Inventário da Árvore Atual
A raiz atual do repositório apresenta alto nível de fragmentação entre a arquitetura nova (parcialmente criada) e a arquitetura operacional atual. Os principais diretórios encontrados na raiz são:
* **Estrutura Alvo (criada, mas subutilizada):** `apps/`, `platform/`, `packages/`, `var/`
* **Núcleo de Código Ativo:** `agents/`, `pipelines/`, `schemas/`, `scripts/`, `tests/`
* **Pastas de Dados/Artefatos Escapadas na Raiz:** `data/`, `input/`, `outputs/`, `logs/`, `artifacts/`, `backup/`, `backups/`, `base_juridica/`
* **Documentação & Apoio Variado:** `docs/`, `docs_iplt/`, `manual_User/`, `policies/`, `templates/`, `tools/`
* **Fragmentos de Agentes Soltos:** `prompts/`, `skills/`
* **Outros/Ambientes:** `mcp-server-cad_obr/`, `arq-js/`, `arq-md/`
* **Arquivos na Raiz:** `main.py`, `debug.py`, `.env`, arquivos de configuração (`pyproject.toml`, `uv.lock`) e artefatos soltos (ex.: zips e JSONs isolados).

### 2. Diretórios Ativos
Os locais que sustentam de fato o código funcional rodando os fluxos hoje:
* **`agents/`:** Onde habitam os códigos dos coletores (e.g. `collector-cad_obr`, `collector-proc`, `case-law-cli`, `firac-cli`, etc.). Cada um com seus respectivos `main.py`, `config.yaml` e diretório local isolado de `skills/`.
* **`pipelines/`:** Responsável pela orquestração de scripts num workflow bach, englobando subpastas importantes de tratamento (`cad_obr`, downstream modules como `normalize` e `monetary`) e as rotinas do índice separado de bases jurídicas (`ingest/`).
* **`schemas/`:** Repositório dos JSON schemas efetivamente consumidos nas coletas e validações documentais.
* **`scripts/`:** Onde operam bibliotecas, clientes de vetorização (como Qdrant) e validações, exercendo ainda papel vital na manutenção e rotinas avulsas do repositório.
* **`platform/`:** Mostra atividade nas rotinas transversais criadas em `skill-runtime` e contém diretórios ricos de habilidades (`skills/` com `extr-peticao-processo`, `legal-data-extractor`, etc.).
* **`var/`:** Já em utilização incipiente, agrupando elementos do novo pipeline (ex.: `var/input/md` via output das ferramentas `convert`).

### 3. Diretórios Obsoletos ou Redundantes
* **Dados e Logs na Raiz:** `data/`, `input/`, `outputs/`, `logs/`, `artifacts/`, `backup/` e `backups/` e `base_juridica/` devem ser considerados redundantes/avulsos pois o design prevê o encapsulamento do estado de I/O de runtime inteiramente no diretório alvo `var/`.
* **Repositório Fragmentado de Conhecimentos:** Pastas `prompts/` e `skills/` situadas livres na raiz, e as pastas `skills/` descentralizadas dentro dos subdiretórios de `agents/`. O padrão atual as torna redundantes em relação à biblioteca central `platform/skills-library` (atual `platform/skills`).
* **Docs Soltos:** `docs_iplt/`, `manual_User/`, `policies/`, `templates/`, `tools/` conflitam com a recomendação de serem absorvidos pelas pastas definitivas de documentação (`docs/`), `platform/` ou diretórios auxiliares formalizados.
* **Refugos/Scripts Soltos:** Arquivos como `arq-js/` e `arq-md/`.

### 4. Pontos de Entrada
Hoje o projeto não dispõe de um entrypoint unificado confiável. A execução engloba acionamentos dispersos:
* **CLI Raiz (Legada/Parcial):** Arquivo `main.py` da base que apresenta falhas ao tentar invocar classes não mais disponíveis nos caminhos velhos (`scripts.doc_collector`).
* **Runners dos Orquestradores de Pipelines Determinísticos:** Uso recorrente de chamadas via CLI para `pipelines/cad_obr.py`.
* **Entrypoints dos Agentes:** Inicialização direta dos arquivos independentes de agentes (`agents/collector-cad_obr/main.py`, `agents/collector-proc/main.py`, etc.).
* **Pipeline de Ingestão:** Inicializados através do `run.py` em `pipelines/ingest/...` de modo explícito pelo usuário.

### 5. Tudo que Hoje Conflita com a Estrutura Alvo (`apps` + `platform` + `packages` + `var`)
A arquitetura final híbrida e definida não está totalmente refletida em disco; há fortes divergências listadas abaixo:

1. **Camada Funcional (`apps/` vs. Realidade):**  
   Os subdiretórios dentro de `apps/` mal possuem arquivos-base. Toda a lógica de extração que deveria estar unificada em `apps/data-processing/src/data_processing/collectors/` está operando da herança pesada do diretório raiz `agents/`. Os processos downstream do negócio que deveriam migrar também encontram-se travados na pasta `pipelines/`.
2. **Componentes e Definições Compartilhadas (`packages/` vs. Realidade):**  
   O diretório `schemas/`, ativamente rodando na raiz do projeto, conflita com o mandamento arquitetural de residir em `packages/shared-schemas/`. O mesmo ocorre sobre ferramentas contidas com papel de uso partilhado na pasta `scripts/`.
3. **Plataforma Crossings (`platform/` vs. Realidade):**  
   Os agentes carregam de forma "hardcoded" localizações de suas próprias configurações, prompts e dependências lendo dos seus diretórios atrelados (`agents/*/skills`), inviabilizando que uma orquestração contínua reutilize estas skills isoladas em vez da biblioteca genérica unificada idealizada para `platform/skills/`.
4. **Infraestrutura e Serviços Externos (`infra/` vs. Realidade):**  
   Ao invés de estarem controlados e contidos em diretórios adequados aos serviços, módulos RAG encontram-se dentro de `scripts/`, scripts da base de QA e RAG residem em `pipelines/ingest/` e há ferramentas como `mcp-server-cad_obr/` em pleno conflito rodando pela própria raiz.
5. **Estado Efêmero da Aplicação (`var/` vs. Realidade):**  
   A lógica atual determinística continua a despejar subprodutos em `outputs/`, rastrear de `data/` e exportar relatórios de `logs/` fora de `var/`, o que fere o isolamento absoluto de metadados, debug e caches na estrutura `var/` requeridos pelo design contínuo.
