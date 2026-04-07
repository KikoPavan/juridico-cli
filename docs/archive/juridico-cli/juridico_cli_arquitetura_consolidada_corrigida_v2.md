# **juridico-cli** **Arquitetura Consolidada Corrigida**

Documento canônico de estrutura, execução, roteamento e convenções de manutenção

Versão corrigida • abril de 2026

| Status | Canônico para leitura estrutural do projeto |
| :---- | :---- |
| Modelo arquitetural | Modular por domínio funcional e centrado em skills |
| Runtime | platform/skill-runtime/ com skill\_dispatcher.py |
| LLMs oficiais | Gemini via API \+ llama.cpp local em Docker |

## **1\. Finalidade deste documento**

Este documento substitui a leitura fragmentada dos arquivos anteriores e fixa a descrição final do projeto em uma única base. A intenção é permitir que a estrutura do repositório seja conferida rapidamente, sem ambiguidade sobre módulos, skills, runtime, LLMs e infraestrutura.

Sempre que houver divergência entre documentos antigos e este documento, a regra é simples: este documento prevalece como referência estrutural e semântica até que uma nova revisão canônica seja emitida.

## **2\. Decisões canônicas**

* O projeto é um monorepo híbrido organizado em módulos funcionais em apps/ e uma camada transversal em platform/.  
* A unidade canônica de capacidade do sistema é a skill. Não há mais arquitetura oficial baseada em agentes separados de prompts e skills.  
* O diretório correto do runtime é platform/skill-runtime/.  
* O arquivo principal de despacho é skill\_dispatcher.py; o nome orchestrator.py deve ser tratado como denominação antiga.  
* A camada platform/skills/ concentra as habilidades canônicas do projeto.  
* apps/data-processing é o módulo de extração e tratamento documental.  
* apps/legal-research é o módulo de pesquisa jurídica e recuperação de insumos.  
* apps/legal-core é o módulo jurídico que executa o papel funcional do advogado.  
* A pilha oficial de LLM é: Gemini via API e llama.cpp local dentro do Docker.  
* Qdrant permanece como componente de infraestrutura local, preferencialmente também sob infra/.

## **3\. Estrutura final do repositório**

juridico-cli/  
├── apps/  
│   ├── data-processing/  
│   │   ├── README.md  
│   │   ├── src/data\_processing/  
│   │   │   ├── cli.py  
│   │   │   ├── main.py  
│   │   │   ├── orchestrator/  
│   │   │   ├── converters/  
│   │   │   ├── cleaners/  
│   │   │   ├── rule\_analysis/  
│   │   │   ├── validation/  
│   │   │   ├── loaders/  
│   │   │   └── contracts/  
│   │   └── tests/  
│   ├── legal-research/  
│   │   ├── README.md  
│   │   ├── src/legal\_research/  
│   │   │   ├── cli.py  
│   │   │   ├── retrieval/  
│   │   │   ├── jurisprudence/  
│   │   │   ├── legislation/  
│   │   │   └── doctrine/  
│   │   └── tests/  
│   ├── legal-core/  
│   │   ├── README.md  
│   │   ├── src/legal\_core/  
│   │   │   ├── cli.py  
│   │   │   ├── firac/  
│   │   │   ├── compliance/  
│   │   │   ├── petition/  
│   │   │   ├── evidence/  
│   │   │   ├── opinions/  
│   │   │   └── strategy/  
│   │   └── tests/  
│   └── orchestrator-cli/  
│       ├── README.md  
│       ├── src/orchestrator\_cli/  
│       │   ├── cli.py  
│       │   ├── dispatch.py  
│       │   └── registry.py  
│       └── tests/  
├── platform/  
│   ├── skill-runtime/  
│   │   ├── skill\_dispatcher.py  
│   │   ├── bundle\_loader.py  
│   │   ├── skill\_registry.yaml  
│   │   ├── llm\_registry.yaml  
│   │   └── prompts/  
│   ├── skills/  
│   │   ├── \_shared/  
│   │   ├── extr-contrato-social/  
│   │   ├── extr-escritura-hipotecaria/  
│   │   ├── extr-escritura-imovel/  
│   │   ├── extr-cabecalho-processo/  
│   │   ├── extr-mandato-processo/  
│   │   ├── extr-processo/  
│   │   ├── extr-contestacao-processo/  
│   │   ├── extr-decisao-processo/  
│   │   ├── extr-peticao-processo/  
│   │   ├── extr-procuracao/  
│   │   ├── firac/  
│   │   ├── case-law/  
│   │   ├── compliance/  
│   │   ├── petition/  
│   │   └── skill-creator/  
│   ├── memory-and-experiences/  
│   └── continuous-learning/  
├── packages/  
│   ├── shared-llm/  
│   ├── shared-schemas/  
│   ├── shared-utils/  
│   └── shared-legal/  
├── var/  
│   ├── input/  
│   ├── staging/  
│   ├── output/  
│   ├── logs/  
│   ├── artifacts/  
│   ├── cache/  
│   └── backups/  
├── docs/  
│   ├── architecture/  
│   ├── implementation/  
│   ├── antigravity/  
│   ├── runbooks/  
│   ├── flows/  
│   └── app-maps/  
├── infra/  
│   ├── docker/  
│   ├── qdrant/  
│   ├── mcp/  
│   └── env/  
├── scripts/  
├── tests/  
├── pyproject.toml  
├── uv.lock  
└── README.md

## **4\. Papel de cada módulo**

| Módulo | Função | Observação canônica |
| :---- | :---- | :---- |
| apps/data-processing | Entrada, conversão, limpeza, normalização, extração, validação e carga documental. | Executa skills documentais do domínio de processamento. |
| apps/legal-research | Pesquisa jurisprudencial, legislativa, doutrinária e retrieval jurídico. | Fornece insumos jurídicos para o sistema. |
| apps/legal-core | Raciocínio jurídico, estratégia, FIRAC, compliance, síntese e petições. | Desempenha o papel funcional do advogado. |
| apps/orchestrator-cli | Entrada operacional e despacho entre módulos. | Coordena fluxos sem concentrar lógica jurídica ou documental. |

## **5\. Papel do runtime**

O diretório correto do runtime é platform/skill-runtime/. Ele não representa uma camada de agentes. Sua função é carregar skills, resolver registros, selecionar configuração de LLM e despachar execução.

| Arquivo | Função |
| :---- | :---- |
| skill\_dispatcher.py | Recebe a tarefa e despacha para a skill correta com a configuração de LLM adequada. |
| bundle\_loader.py | Carrega a skill, seus recursos, contratos e regras transversais compartilhadas. |
| skill\_registry.yaml | Registro canônico de habilidades e seus caminhos. |
| llm\_registry.yaml | Registro canônico de execução de modelos, providers e aliases. |

## **6\. Modelo de execução**

**1\.** A tarefa entra pelo módulo funcional adequado.

**2\.** O runtime resolve qual skill deve ser usada.

**3\.** O runtime resolve qual configuração de LLM deve ser usada.

**4\.** A skill é carregada pelo bundle\_loader.

**5\.** A skill é executada.

**6\.** O output é validado contra contrato e schema.

**7\.** O resultado segue para o próximo módulo ou para persistência.

tarefa → módulo funcional → skill → configuração de LLM → validação → saída

## **7\. Stack oficial de LLM e infraestrutura**

| Camada | Tecnologia oficial | Observação |
| :---- | :---- | :---- |
| LLM via API | Gemini | Backend remoto usado via API. |
| LLM local | llama.cpp | Backend local executado dentro do Docker. |
| Vector store | Qdrant | Componente de infraestrutura local. |
| Infra de execução | Docker | Hospeda os serviços locais do projeto, incluindo o LLM local. |

Referências anteriores a Haiku, Sonnet, Ollama, placeholders “?” ou “???” devem ser tratadas como antigas ou incorretas para a arquitetura atual.

## **8\. Convenções obrigatórias de nomenclatura**

| Conceito | Correto | Evitar |
| :---- | :---- | :---- |
| Runtime | platform/skill-runtime/ | platform/agent-core/ |
| Despacho | skill\_dispatcher.py | orchestrator.py (como nome canônico) |
| Capacidade | skill | agente embutido |
| Registro | skill\_registry.yaml | mapa de agentes |
| Execução | execução de skill | execução de agente |

## **9\. Regras de separação estrutural**

* apps/ define fluxo funcional por domínio de negócio.  
* platform/skills/ define as habilidades canônicas do sistema.  
* platform/skill-runtime/ executa, carrega e roteia skills.  
* packages/ guarda apenas componentes realmente compartilhados.  
* platform/skills/\*/assets/ guarda os schemas autoritativos dos bundles.  
* packages/shared-schemas/ guarda apenas contratos realmente compartilhados.  
* var/ concentra runtime, I/O operacional, logs e artefatos.  
* infra/docker/ deve ser a referência de execução para os serviços locais.  
* agents/ e pipelines/ antigos, quando existirem no repositório, devem ser tratados como legado congelado e não como autoridade do caminho novo.

## **10\. Como interpretar cada documento anterior**

| Documento | O que está correto | O que está errado | Ação |
| :---- | :---- | :---- | :---- |
| juridico\_cli\_arquitetura\_final.md | Monorepo híbrido, separação em apps/platform/packages/var/infra. | Mistura skills-library, collectors como centro estrutural e nomenclatura antiga. | Atualizar para skill-runtime, platform/skills/ e modelo 100% skill-centric. |
| juridico\_cli\_projeto\_descritivo\_v1.1.md | É o documento mais próximo da direção atual de skills, registries e loader. | Ainda usa agent-core, orchestrator e linguagem de agente embutido; LLMs antigos ou incorretos. | Corrigir runtime, despacho, LLMs e remover agent-centric. |
| juridico\_cli\_projeto\_descritivo\_v1.2.md | Útil como visão futura de memória e resiliência. | Não deve ser usado como base estrutural corrente; precisa alinhar termos ao runtime novo. | Manter como expansão futura, mas alinhado à nomenclatura canônica. |

## **11\. Instruções obrigatórias para manutenção**

* Não introduzir novamente arquitetura baseada em agentes separados de prompts e skills.  
* Qualquer nova capacidade do sistema deve nascer como skill em platform/skills/.  
* Qualquer texto novo de documentação deve usar skill-runtime e skill\_dispatcher como nomenclatura canônica.  
* Se um arquivo ou script ainda apontar para agent-core ou orchestrator como nome atual, ele deve ser corrigido.  
* Mudanças em runtime, docs, registries e paths devem ser feitas juntas para evitar drift documental.  
* Não usar aliases de LLM antigos; o registry oficial deve refletir Gemini via API e llama.cpp local em Docker.  
* Antes de validar uma mudança estrutural, conferir se a árvore do repositório ainda respeita a separação entre apps, platform, packages, var e infra.  
* Sempre registrar no espelho do estado atual qualquer renomeação estrutural de pasta, arquivo canônico ou registry.

## **12\. Checklist rápido de conferência**

**☐** Existe platform/skill-runtime/ e não platform/agent-core/ como nome canônico.

**☐** Existe skill\_dispatcher.py como arquivo principal de despacho.

**☐** O runtime carrega skills e não agentes separados.

**☐** apps/data-processing, apps/legal-research e apps/legal-core estão preservados como módulos funcionais.

**☐** platform/skills/ é a camada canônica de habilidades.

**☐** Os LLMs oficiais estão documentados como Gemini via API e llama.cpp local em Docker.

**☐** infra/docker/ está previsto como parte da infraestrutura do projeto.

**☐** Os documentos operacionais e arquiteturais usam a mesma nomenclatura.

## **13\. Decisão final**

A arquitetura correta do juridico-cli é modular por domínio funcional e centrada em skills. O projeto deve ser lido a partir de apps/ para funções de negócio, de platform/skills/ para capacidades canônicas e de platform/skill-runtime/ para execução e roteamento. Qualquer denominação que reintroduza a leitura agent-centric deve ser tratada como desatualizada.
