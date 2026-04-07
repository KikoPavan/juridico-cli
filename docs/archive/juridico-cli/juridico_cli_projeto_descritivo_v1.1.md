> [!WARNING]
> **DOCUMENTO HISTÓRICO — NÃO É A FONTE PRINCIPAL DA ARQUITETURA**
> Este documento descreve uma etapa de transição e não reflete a arquitetura atual do projeto.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

**juridico-cli**

Projeto Descritivo e Estrutural

Arquitetura co-located · Orquestrador Multi-LLM · Agentes Jurídicos Especializados

Versão 1.1 · Março 2026

_Revisado: skills/ · \_shared/ · extr-\* bundles · skill-creator · skills externas_

# **1\. Visão executiva**

O juridico-cli é um monorepo híbrido de processamento jurídico baseado em agentes IA
especializados. O projeto processa documentos processuais brasileiros de ponta a
ponta: da ingestião de PDFs brutos até a entrega de análises estruturadas,
jurisprudência sintetizada, jurimetria de risco e raços de peças processuais.

A decisão arquitetural central é o modelo co-located: cada skill jurídica carrega
seu próprio agente especializado no mesmo bundle, eliminando a necessidade de
bridging externo entre agente e skill. Um orquestrador com dois eixos de decisão
qual LLM e qual bundle — garante custo ótimo e especialização máxima por tipo de tarefa.

| Atributo          | Valor                                                            |
| :---------------- | :--------------------------------------------------------------- |
| Nome              | juridico-cli                                                     |
| Tipo              | Monorepo híbrido — apps funcionais \+ plataforma transversal     |
| Domínio           | Direito imobiliário, processual civil, contencioso TJSP          |
| Modelo de execução | Co-located (skill bundle carregado pelo skill-runtime)           |
| Despacho          | skill_dispatcher.py: resolução de LLM × bundle por task          |
| LLMs suportados   | Gemini via API · llama.cpp local em Docker                       |
| Hardware alvo     | i7-6700HQ · GTX 950M 4GB · SSD 1TB · WSL/Ubuntu 24               |
| Stack principal   | Python 3.12 · uv · Qdrant · Marker · FastAPI · MCP               |

Alterações da versão 1.1 Renomeação skills-library → skills · Inclusão de
\_shared/extraction-base.md · 10 bundles extr-\* de extração documental ·
Inclusão do skill-creator · Mecanismo de skills externas (.skill / SKILL.sh) ·
Regras de anatomia de bundle revisadas

# **2\. Decisão arquitetural**

## **2.1 Modelo co-located de skills**

No modelo co-located, cada skill bundle é uma unidade autossuficiente: contém a
instrução de uso (SKILL.md), o agente especializado (agents/), os schemas de output
em assets/, os prompts e os validators. O agente interno já conhece exatamente o
formato de output esperado, as restrições e o fluxo de raciocínio da skill — sem
depender de bridge externo.

 Comparação com o modelo flat (Antigravity) No modelo flat, agents/ e skills/ são
 diretórios irmãos independentes. O orquestrador combina N agentes × M skills em
 runtime via bridging explícito no system_prompt. Máxima flexibilidade, porém
 \~20-30% mais tokens por chamada e risco de dessincronização entre agente e skill
 ao evoluir o projeto.

### **Anatomia obrigatória de um bundle**

Todo bundle co-located segue esta estrutura interna. O nome do arquivo em agents/ deve
coincidir com o nome do bundle.

| Arquivo / Diretório        | Propósito                                               |
| :------------------------- | :------------------------------------------------------ |
| SKILL.md                   | Instrução canônica de extração, triggering e configuração de runtime |
| assets/\<schema\>.json     | Schema JSON de output — jamais na raiz do bundle                     |
| prompts/                   | System prompt base e exemplos few-shot                  |
| references/                | Dicionário de campos e documentação técnica             |
| scripts/                   | Validadores e utilitários de teste                      |
| validators/                | Validação domínio-específica (citações, CPF, etc.)      |

### **Campo base no frontmatter da skill**

Quando o bundle pertence a uma família que compartilha regras transversais (ex: todos
os bundles extr-\*), o agente declara o arquivo compartilhado no frontmatter:

\---  
name: extr-escritura-imovel-agent  
skill: extr-escritura-imovel  
base: ../\_shared/extraction-base.md  
llm_default: gemini_api  
\---

O bundle_loader.py injeta o conteúdo de base antes do body do agente, evitando
duplicação entre os 10 bundles extr-\*.

## **2.2 Despacho de skills (skill_dispatcher)**

O skill_dispatcher.py toma três decisões independentes antes de executar qualquer bundle:

| Eixo   | Decisão                             | Lógica                                                                      |
| :----- | :---------------------------------- | :-------------------------------------------------------------------------- |
| Eixo 1 | LLM Registry — qual modelo usar     | ? para raciocínio · ? para extração · Local para pré-processamento          |
| Eixo 2 | Task Classifier — tipo da tarefa    | Regras determinísticas primeiro · LLM só para casos ambíguos                |
| Eixo 3 | Skill Registry — qual bundle ativar | Mapeamento task_type → bundle → agent embutido                              |

# **3\. Módulos funcionais**

O projeto organiza suas funções em quatro módulos sequenciais mais uma camada de
extração documental especializada (M0), cada um com responsabilidade única e
bundle correspondente.

## **M0 · Extração documental especializada (novo)**

Camada de extração estruturada de documentos jurídicos específicos: escrituras,
contratos sociais, peças processuais e procurações. Cada tipo de documento tem
seu próprio bundle co-located com schema JSON de output dedicado. Opera
exclusivamente com Haiku.

| Componente  | Descrição                                                                                                          |
| :---------- | :----------------------------------------------------------------------------------------------------------------- |
| Localização | platform/skills/extr-\*/                                                                                           |
| LLM         | ? para todos os bundles extr-\* (extração determinística)                                                          |
| Regras base | platform/skills/\_shared/extraction-base.md (literalidade, null seguro, moeda literal, JSON puro, schema como lei) |
| Criado com  | skill-creator (platform/skills/skill-creator/)                                                                     |
| Output      | JSON estruturado validado contra schema — alimenta o M1 e o Qdrant                                                 |

### **Bundles extr-\* previstos**

| Bundle                     | Documento alvo                                                     |
| :------------------------- | :----------------------------------------------------------------- |
| extr-contrato-social       | Contrato social e alterações (quadro societário, poderes, capital) |
| extr-escritura-hipotecaria | Escritura pública de hipoteca / cédula de crédito                  |
| extr-escritura-imovel      | Escritura pública de imóvel (compra, venda, doação) \+ ônus        |
| extr-cabecalho-processo    | Cabeçalho processual (partes, número, classe, distribuidor)        |
| extr-mandato-processo      | Mandato processual / substabelecimento                             |
| extr-processo              | Autos completos — extração geral                                   |
| extr-contestacao-processo  | Contestação (preliminares, teses de mérito, reconvenção)           |
| extr-decisao-processo      | Decisão / sentença (ratio decidendi, dispositivo, sucu mbência)    |
| extr-peticao-processo      | Petição inicial (causa de pedir, pedidos, valor da causa)          |
| extr-procuracao            | Procuração (poderes, outorgante, outorgado, validade)              |

## **M1 · Extração e tratamento documental**

| Componente   | Descrição                                                                                                 |
| :----------- | :-------------------------------------------------------------------------------------------------------- |
| App          | apps/data-processing/                                                                                     |
| Bundle ativo | platform/skills/data-processing/                                                                           |
| LLM          | ? (extração) · ? (pré-processamento, chunking)                                                            |
| Pipeline     | PDF bruto → Marker OCR → Markdown → Limpeza jurídica → Análise de regras → Collector → Validação → Qdrant |
| Sub-agentes  | collector-cad-obr · collector-proc                                                                        |
| Output       | normalized_doc.schema.json \+ chunks no Qdrant                                                            |

## **M2 · Busca jurisprudencial**

| Componente   | Descrição                                                                            |
| :----------- | :----------------------------------------------------------------------------------- |
| App          | apps/legal-research/                                                                 |
| Bundle ativo | platform/skills/case-law/                                                             |
| LLM          | ? (síntese e raciocínio) · ? (classificação de relevância)                           |
| RAG          | Agentic RAG com loop ReAct: recupera → avalia → refina query → repete até satisfação |

## **M3 · Jurimetria e análise de risco**

| Lacuna identificada — a ser implementado Este módulo não existe na estrutura atual.
É a principal adição funcional proposta. Combina os acórdãos recuperados pelo M2
com análise estatística para gerar score de probabilidade de êxito por tese.

## **M4 · IA Core jurídico**

| Componente     | Descrição                                                                                        |
| :------------- | :----------------------------------------------------------------------------------------------- |
| App            | apps/legal-core/                                                                                 |
| Bundles ativos | firac/ · petition/ · compliance/ · jus-diagnose/ · jus-breve/ · jus-autoridade/ · jus-sistêmico/ |
| LLM            | ?                                                               |

# **4\. Árvore de arquivos final**

Marcas: (N) novo · (M) modificado · sem marca \= já existe. Renomeação skills-library → skills aplicada em todo o projeto.

## **4.1 Plataforma transversal**

platform/  
├── skill-runtime/  
│ ├── skill_dispatcher.py (M) despacho de skills: LLM \+ bundle  
│ ├── bundle_loader.py (N) load_bundle() \+ injeta base  
│ ├── llm_registry.yaml (N)  
│ └── skill_registry.yaml (N)  
│  
├── skills/ (M)
│ ├── \_shared/ proc-core.md
│ │ └── extraction-base.md (N) null seguro · moeda literal · JSON puro · schema como lei  
│ │  
│ ├── skill-creator/ (N) trazido de \~/devops/SKILLS  
│ │ ├── SKILL.md  
│ │ ├── agents/ grader · comparator · analyzer  
│ │ ├── assets/  
│ │ ├── eval-viewer/  
│ │ ├── references/dicionario_campos.md
│ │ └── scripts/ run_loop · package_skill · run_eval  
│ │  
│ ├── extr-contrato-social/  
│ │ ├── SKILL.md (instrução canônica)  
│ │ ├── assets/contrato_social.schema.json  
│ │ ├── references/  
│ │ └── scripts/  
│ ├── extr-escritura-hipotecaria/  
│ │ ├── SKILL.md (instrução canônica)  
│ │ ├── assets/escritura_hipotecaria.schema.json  
│ │ └── ...  
│ ├── extr-escritura-imovel/  
│ │ ├── SKILL.md (instrução canônica)  
│ │ ├── assets/escritura_imovel.schema.json  
│ │ └── ...  
│ ├── extr-cabecalho-processo/ (N) · extr-mandato-processo/ (N)  
│ ├── extr-processo/ (N) · extr-contestacao-processo/ (N)  
│ ├── extr-decisao-processo/ (N) · extr-peticao-processo/ (N)  
│ ├── extr-procuracao/ (N)  
│ │  
│ ├── firac/ (M) migrado para co-located  
│ │ ├── SKILL.md (instrução canônica)  
│ │ ├── assets/ · schemas/ · validators/  
│ ├── petition/ (M) · case-law/ (M) · compliance/ (M)  
│ ├── jurimetria/ (N) novo módulo M3  
│ ├── jus-diagnose/ já co-located, sem alterações  
│ ├── jus-breve/ já co-located, sem alterações  
│ ├── jus-autoridade/ já co-located, sem alterações  
│ └── jus-sistêmico/ já co-located, sem alterações  
│  
├── memory-and-experiences/  
│ ├── mem0_adapter.py (N)  
│ └── experience_rewriter.py (M)  
└── continuous-learning/ preservar estrutura existente

## **4.2 Skills externas — mecanismo de aquisição**

Skills criadas fora do projeto ou obtidas de repositórios externos são empacotadas como arquivos .skill e instaladas via script. O mecanismo é gerenciado pelo skill-creator.

| Etapa         | Ação                                                                                       |
| :------------ | :----------------------------------------------------------------------------------------- | --------------------------------- |
| 1\. Empacotar | python \-m scripts.package_skill platform/skills/extr-\*/ → gera extr-\*.skill             |
| 2\. Instalar  | SKILL.sh ou python scripts/install_skill.py \<arquivo\>.skill → extrai em platform/skills/ |
| 3\. Registrar | Adicionar entrada em platform/skill-runtime/skill_registry.yaml                            |
| 4\. Rastrear  | skill.origin.yaml dentro do bundle: source (local                                          | externo) · version · created_with |

\# skill.origin.yaml (dentro de cada bundle instalado externamente)  
source: externo  
version: 1.0.0  
created_with: skill-creator  
installed_at: 2026-03-28

## **4.3 Apps (thin wrappers)**

apps/  
├── data-processing/cli.py (M) usa bundle_loader  
├── legal-research/  
│ ├── cli.py (M) usa bundle_loader  
│ └── jurimetry/ (N) submódulo M3  
└── legal-core/cli.py (M) usa bundle_loader

# **5\. Configuração do orquestrador**

## **5.1 llm_registry.yaml**

execution_classes:  
 gemini_api:  
 provider: gemini  
 mode: api  
 deployment: external_api  
 use_for: \[high_reasoning, fast_extraction, large_context\]  
 llama_cpp_local:  
 provider: llama_cpp  
 mode: local  
 deployment: docker  
 use_for: \[pre_processing, chunking, metadata, routing\]

## **5.2 skill_registry.yaml (com entradas extr-\*)**

skills:  
 extr-contrato-social:  
 path: platform/skills/extr-contrato-social  
 profile: high_reasoning  
 extr-escritura-hipotecaria:  
 path: platform/skills/extr-escritura-hipotecaria  
 profile: high_reasoning  
 extr-escritura-imovel:  
 path: platform/skills/extr-escritura-imovel  
 profile: large_context  
 \# ... demais extr-\* seguem o mesmo padrão  
 firac:  
 path: platform/skills/firac  
 profile: high_reasoning  
 jus-diagnose:  
 path: platform/skills/jus-diagnose  
 profile: high_reasoning  

# **6\. Regras transversais — \_shared/extraction-base.md**

Arquivo compartilhado por todos os bundles extr-\*. O bundle_loader.py injeta seu
conteúdo antes do body de cada SKILL.md. Elimina duplicação das quatro
regras gerais entre os 10 bundles.

| Regra           | Descrição                                                                                            |
| :-------------- | :--------------------------------------------------------------------------------------------------- |
| Literalidade    | Extrair apenas o que está explicitamente no texto — nunca inferir partes, valores ou datas           |
| Null seguro     | Campo ausente → null · lista ausente → \[\] · nunca omitir campo obrigatório do schema               |
| Moeda literal   | Copiar valor literal para campos originais — nunca converter CR$→R$ ou qualquer moeda histórica      |
| JSON puro       | Responder somente com o JSON final — sem markdown, sem blocos de código, sem comentários             |
| Schema como lei | Não criar campos fora do schema · rastreabilidade: preencher sempre fonte.arquivo_md \+ fonte.ancora |

| Por que \_shared/ e não copiar em cada bundle? Com 10 bundles extr-\*, copiar as 5 regras em cada SKILL.md cria 10 cópias para manter sincronizadas. Uma única alteração em \_shared/extraction-base.md propaga para todos os bundles no próximo load. O campo base: no frontmatter da skill declara a dependência explicitamente. |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

# **7\. Mapa de skills e bundles**

| Bundle                     | Instrução canônica | LLM              | \_shared | Status    | HITL |
| :------------------------- | :----------------- | :--------------- | :------- | :-------- | ---- |
| extr-contrato-social       | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-escritura-hipotecaria | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-escritura-imovel      | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-cabecalho-processo    | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-mandato-processo      | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-processo              | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-contestacao-processo  | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-decisao-processo      | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-peticao-processo      | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| extr-procuracao            | SKILL.md           | gemini_api       | Sim      | Pronto    | Não  |
| data-processing            | SKILL.md           | gemini_api       | Não      | Migrar    | Não  |
| case-law                   | SKILL.md           | gemini_api       | Não      | Migrar    | Não  |
| firac                      | SKILL.md           | gemini_api       | Não      | Migrar    | Sim  |
| petition                   | SKILL.md           | gemini_api       | Não      | Migrar    | Sim  |
| compliance                 | SKILL.md           | gemini_api       | Não      | Migrar    | Sim  |
| jurimetria                 | SKILL.md           | gemini_api       | Não      | Criar (N) | Sim  |
| jus-diagnose               | SKILL.md           | gemini_api       | Não      | Pronto    | Sim  |
| jus-breve                  | SKILL.md           | gemini_api       | Não      | Pronto    | Sim  |
| jus-autoridade             | SKILL.md           | gemini_api       | Não      | Pronto    | Sim  |
| jus-sistêmico              | SKILL.md           | gemini_api       | Não      | Pronto    | Sim  |
| skill-creator              | SKILL.md           | gemini_api       | Não      | Pronto    | Sim  |

# **8\. Roadmap de implantação (atualizado)**

Fase 0 adicionada para os bundles extr-\* antes da migração dos bundles jurídicos. A sequência garante que a infraestrutura \_shared/ esteja pronta antes de criar os bundles que dependem dela.

## **Fase 0 · \_shared/ e bundles extr-\* (Semana 1\)**

- Criar platform/skills/\_shared/extraction-base.md com as 5 regras transversais

- Trazer skill-creator de \~/devops/SKILLS para platform/skills/skill-creator/

- Usar skill-creator para criar cada bundle extr-\* com SKILL.md \+ agent \+ assets/schema \+ references/dicionario \+ scripts/validate

- Criar skill.origin.yaml em cada bundle instalado externamente

- Registrar todos os extr-\* no skill_registry.yaml com llm: gemini_api e hitl: false

- Implementar campo base no bundle_loader.py: injeta \_shared/extraction-base.md antes do agent body

- Validar: extr-escritura-imovel processa documento com leasing histórico em CR$ — output deve manter moeda literal

## **Fase 1 · Infraestrutura do orquestrador (Semana 2\)**

- Criar llm_registry.yaml e skill_registry.yaml em platform/skill-runtime/

- Implementar bundle_loader.py: leitura de SKILL.md \+ base (se declarado)

- Implementar LLMClient unificado em packages/shared-llm/

- Implementar skill_dispatcher.py com resolução dupla LLM × bundle

## **Fase 2 · Migração co-located dos bundles jurídicos (Semana 3\)**

- Criar SKILL.md para firac, petition, case-law, compliance com instrução canônica

- Criar SKILL.md para data-processing com instrução de extração

- Refatorar apps/\*/cli.py para usar bundle_loader

- Remover arquivos de instrução duplicados fora de platform/skills/

## **Fase 3 · M3 Jurimetria (Semana 4\)**

- Criar platform/skills/jurimetria/ com SKILL.md \+ risk_report.schema.json

- Implementar apps/legal-research/jurimetry/jurimetry_runner.py

- Integrar com output do M2

## **Fase 4 · Agentic RAG e Memória (Semana 5\)**

- Implementar agentic_rag.py em legal-research/retrieval/

- Integrar Mem0 em platform/memory-and-experiences/

- Configurar três coleções Qdrant: docs, jurisprudencia, embeddings

## **Fase 5 · HITL e validação (Semana 6\)**

- Implementar HITL checkpoint explícito no orquestrador

- Interface CLI de validação com loop de retry e feedback injetado no contexto

- Logs estruturados por tarefa para auditabilidade

| Continuous Learning — Fase 6 (após estabilização) sage_rl, agentic_proposing e network_expansion devem ser especificados formalmente antes de implementar. |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------- |

# **9\. Stack técnica**

| Camada              | Tecnologia                       | Observação                     |
| :------------------ | :------------------------------- | :----------------------------- |
| LLM principal       | **gemini-2.5-pro**               | Gemini via API                 |
| LLM rápido          | **gemini-2.5-flash**             | Gemini via API                 |
| LLM local           | **llama.cpp**                    | Docker · zero custo de API     |
| Embedding local     | **Qdrant + modelo configurável** | Qdrant local · Docker          |
| Vector store        | **Qdrant**                       | Local · Docker                 |
| OCR / PDF           | **Marker v1.10.2**               | Mais rápido que MarkItDown     |
| Runtime             | **Python 3.12 · uv**             | Ambiente virtual gerenciado    |
| Criação de skills   | **skill-creator**                | platform/skills/skill-creator/ |
| Empacotamento       | **package_skill.py \+ SKILL.sh** | Skills externas via .skill     |
| Orquestração futura | **LangGraph**                    | Para agentic loop ReAct        |
| Memória             | **Mem0**                         | Episódica \+ Semântica         |
| Protocolo MCP       | **MCP servers**                  | Conexão com Claude.ai          |
| Linting             | **Ruff · Black · mypy**          | CI automático                  |

juridico-cli · Projeto Descritivo v1.1 · Março 2026
