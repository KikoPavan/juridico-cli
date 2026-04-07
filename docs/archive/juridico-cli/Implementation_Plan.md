> [!WARNING]
> **DOCUMENTO HISTÓRICO — NÃO É A FONTE PRINCIPAL DA ARQUITETURA**
> Este plano de reorganização estrutural já foi executado. O estado atual está no documento canônico.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Plano de Reorganização Estrutural: Juridico-CLI (Transição v1.1)

O objetivo primário deste plano é executar uma transição segura, modular e estritamente aderente aos guias arquiteturais atuais do projeto, sanando o débito técnico e o alto acoplamento diagnóstico, sem impactar o pipeline produtivo diário (Zero Downtime / Shadow Deployment).

> [!IMPORTANT]
> - O escopo remove intencionalmente abstrações de Mem0, TurboQuant, ou ReliabilityBench para futuras expansões.
> - O plano usa a técnica de duplo-deploy: Construiremos a infraestrutura ideal lado-a-lado. Processos antigos só serão deletados (Fase 4) após a validação de que os `apps` operam com a inteligência do `platform/skills` com paridade integral ao pipelines legado.

## Proposed Changes

### 1. Camada Transversal (Platform & Packages)
A infraestrutura será solidificada isolada da lógica de domínio para ser injetável através de todo o Monorepo:
* **platform/skills/_shared/extraction-base.md** (Regra-Mestra da abstração de extrações)
* **platform/skill-runtime/bundle_loader.py** (Carregador e Compilador de Bundles em Memória)
* **platform/skill-runtime/llm_registry.yaml** e **skill_registry.yaml**
* **packages/shared-llm/client.py** (Cliente Unificado LLM Agnóstico a provedor/modelo)
* **packages/shared-schemas/** (Repositório Central Pydantic/JSON)

### 2. Domínios Funcionais (Apps)
Deixarão de ser meros CLIs vazios. Assumem o papel maduro de **Domain Business Logic**.
* Coletores e regras de extração processual vão se estabelecer funcionalmente contidos nas verticais de `apps/data-processing/`.
* Orquestrarão os `bundle_loader.py` para injetar os *Intelligent Bundles* localizados sob `platform/skills/`.

### 3. Operação de Runtime e I/O (Var)
* Todos os diretórios de escapes transitórios do workflow legado (`data/`, `outputs/`, `logs/`, `artifacts/`, etc.) serão gradativamente movidos, centralizando tudo sob os caminhos oficiais ditados pela arquitetura:
  * `var/input/raw/`
  * `var/input/md/`
  * `var/input/json/`
  * `var/staging/`
  * `var/output/`
  * `var/logs/`
  * `var/artifacts/`
  * `var/cache/`
  * `var/backups/`

---

## O que fazer para NÃO quebrar a produção (Diretriz Global)
1. **Nenhum arquivo executável atual** (como `pipelines/cad_obr.py`) **será movido ou alterado nas Fases 0, 1 e 2**.
2. Schemas antigos realocados (Fase 1) utilizarão compatibilidade temporária controlada ou cópia transitória para garantir imports não quebrados no legado (sem gerar symlinks), com deleção planejada apenas na Fase 4.
3. Testes end-to-end ocorrem na Fase 3 isoladamente em novas saídas de terminal geradas pelos `apps/`.
4. A deleção de lixos e desuso de lógicas legadas se dará apenas como um *switch* de arquitetura (Fase 4), assegurando rollback instântaneo nas Fases 1 a 3.
5. O critério de aceite central em qualquer reestruturação é a **paridade funcional** com o pipeline legado em ambiente de homologação.

---

## Task Breakdown (Ordem de Implementação por Fases)

### Fase 0: Infraestrutura Base e Transversais
*Cria o esqueleto abstrato para as ferramentas subsequentes.*

- **Task 0.1**: Criar o contrato abstrato base em `platform/skills/_shared/extraction-base.md`.
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Requisitos de literalidade e JSON seguro → Markdown global → Confirmar semântica das diretrizes aplicadas em inspeção visual.
- **Task 0.2**: Desenvolver a lógica central no motor de despacho de skills `platform/skill-runtime/bundle_loader.py`.
  - **Dependencies**: 0.1
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Path da respectiva skill a carregar → Componente lógico com payload dinâmico injetando as regras conjuntas e schemas JSON → Execução de carregamento mock estrutural validada.
- **Task 0.3**: Refatorar `skill-creator` para localizar-se oficialmente estruturado em `platform/skills/`.
  - **Dependencies**: 0.2
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Mover scripts/geradores remanescentes de root pro diretório central de ferramentas → Garantir teste real (criar script de skill *dummy* utilizando a estrutura unificada).
- **Critério de Aceite da Fase 0**: O `bundle_loader.py` compila e consolida dinamicamente um bundle com as regras transversais de extração, resultando num empacotamento sem falhas funcionais.

### Fase 1: Desacoplamento de LLM e Registro Global
*Garante independência de provider de inteligência e esquemas genéricos.*

- **Task 1.1**: Centralizar Data Model transacionando de `schemas/` legados para livraria oficial `packages/shared-schemas/`. Implementar cópias transitórias preservando a base na raiz para o suporte vitalício simultâneo.
  - **Dependencies**: Fase 0 concluída
  - **Agent**: `database-architect` (apoio estrutural: `backend-specialist`)
  - **INPUT → OUTPUT → VERIFY**: Estruturas de bases e Sub-JSONs transferidos sem apagar o suporte temporário da raiz → Packages aptos a serem listados nativamente no python root.
- **Task 1.2**: Introduzir `LLMClient` genérico na branch `packages/shared-llm/`. Totalmente agnóstico, limpo de travas de providers específicos (e.g., OpenAI) ou limitações hardcoded.
  - **Dependencies**: 1.1
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Codificar o cliente e a interface limpa → Validar compilação limpa injetando dummy interface.
- **Task 1.3**: Declarar os registros canônicos no `platform/skill-runtime/` via `llm_registry.yaml` e `skill_registry.yaml`.
  - **Dependencies**: 1.2
  - **Agent**: `backend-specialist`
- **Critério de Aceite da Fase 1**: Resolução do cliente LLM em ambiente de sandbox local opera inteiramente alheio a vendor loc-in e a plataforma está apta a apontar a skills catalogados no yaml sem ferir instâncias legadas.

### Fase 2: Módulos de Domínio (Apps) e Skill Bundles
*Reconstrução lógica no ecossistema Co-Located adotando nomenclatura oficial (v1.1).*

- **Task 2.1**: Estabelecer estritamente e instanciar todos os bundles extraídos orientados pela arquitetura para habitarem a pasta `platform/skills/`:
  - `extr-contrato-social`
  - `extr-escritura-hipotecaria`
  - `extr-escritura-imovel`
  - `extr-cabecalho-processo`
  - `extr-mandato-processo`
  - `extr-processo`
  - `extr-contestacao-processo`
  - `extr-decisao-processo`
  - `extr-peticao-processo`
  - `extr-procuracao`
  - **Dependencies**: Fase 1 concluída
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Absorver os prompts remanescentes órfãos nestes containers Co-Located. Ligar cada skill ao sub-JSON correto vindo de Packages → Chancelar compilação isolada dos 10 domínios perante o loader.
- **Task 2.2**: Estruturar os coletores atrelando inteligência e roteamentos nas verticais de `apps/data-processing/`.
  - **Dependencies**: 2.1
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Lógica determinística e de negócio baseia os chamados em motor e carrega o Intelligent Bundle correto para o contexto exato da extração paralela.
- **Critério de Aceite da Fase 2**: Domain logic no `apps/` comunicando através da `platform` operante, com bundles formatados obedecendo fielmente o documento 1.1 e os schemas corretos na mesma arquitetura.

### Fase 3: Roteamento Rigoroso de I/O
*Eliminação do escape efêmero - Runtime restrita aos caminhos oficiais .*

- **Task 3.1**: Reconfigurar os módulos operantes isolados criados em `apps/` determinando direcionamento unificado em `var/`: `var/input/(raw|md|json)`, `var/staging/`, `var/output/`, `var/logs/`, `var/artifacts/`, `var/cache/` e `var/backups/`.
  - **Dependencies**: Fase 2 concluída
  - **Agent**: `backend-specialist`
  - **INPUT → OUTPUT → VERIFY**: Configurações de Paths → Aplicação do direcionador I/O → Esgotar uma extração demonstrando logs, text extraction e schema em seus caminhos oficiais sob `/var`.
- **Critério de Aceite da Fase 3**: Execução simulada onde todos os sub-produtos da fatura estritamente obedecem a hierarquia `/var` com restrição de acesso a qualquer área cruzada como a raiz corporativa legada (`/outputs/`).

### Fase 4: Descomissionamento ("Stop Bleeding")
*Expurgar as velhas artérias dependentes, acatando a paridade de Output garantida no Double Deploy.*

- **Task 4.1**: Saneamento cirúrgico da arquitetura legada. Exclusão permanente das pastas provisórias mantidas nas Fases 0~3: cópia transitória das schemas radiculares, resquícios em `prompts/`, lixo log em `data/` e `outputs/`, diretórios de agentes em `agents/` inativos.
  - **Dependencies**: O Pipeline modularizado (via `apps/data-processing`) alcançou **paridade funcional idêntica** ao ambiente de `pipelines/` antigas perante uma carga real validada.
  - **Agents**: `code-archaeologist` em alinhamento final com `devops-engineer`
  - **INPUT → OUTPUT → VERIFY**: Varredura manual com tree list reportando artefatos soltos → Apagamento limpo → Garantia que testes remanescentes continuam passando incólumes sem side-effects no `python .agent/scripts/checklist.py .`.
- **Critério de Aceite da Fase 4**: Inspeção manual via listagem atestando total limpeza e conformidade com o esqueleto do ecossistema de infraestrutura 1.1 e final, com isolamento funcional mantido. Morte arquitetural do fluxo obsoleto provado seguro.

---

## Verification Plan

### Paridade Funcional (Critério Supremo)
1. Rodar os scripts de pipelines transicionados invocando os novos bundles de domínio hospedados em `apps/data-processing`.
2. O resultado extraído unificado na nova estrutura `var/output/` deve ser estritamente superior ou garantir completude idêntica ao output cravado na antiga arquitetura root.
3. Não prosseguir caso haja degradação funcional, perda de mapeamento json em atributos processuais, resultantes de instabilidade ou chamadas de fallback em bundles criados.

### Validações Passivas Complementares
- Relacionamentos inspecionados via ferramentas analíticas passivas: utilitário `checklist.py` atua como suporte estático pós-facto em todas as compilações e execuções críticas da Fase 2.
