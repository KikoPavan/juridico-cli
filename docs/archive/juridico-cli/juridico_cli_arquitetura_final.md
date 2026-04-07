> [!WARNING]
> **DOCUMENTO HISTÓRICO — NÃO É A FONTE PRINCIPAL DA ARQUITETURA**
> Este documento foi superseded pelo documento canônico consolidado v2.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

**Arquitetura Final do Projeto juridico-cli**

Modelo híbrido: apps funcionais \+ plataforma transversal de agentes

| Projeto  | juridico-cli                                             |
| :------- | :------------------------------------------------------- |
| Objetivo | Definir a arquitetura final e a sequência de implantação |
| Data     | 22/03/2026                                               |

**Decisão arquitetural.** O projeto deve ser organizado como um monorepo híbrido. A camada de apps resolve o fluxo funcional do negócio; a camada de plataforma preserva orquestração, skills, memórias e evolução contínua.

| _Os collectors collector-cad-obr e collector-proc permanecem baseados em LLM, com skills, prompts e schemas, mas passam a pertencer ao app data-processing, pois sua responsabilidade principal é estruturar dados documentais._ |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

# **1\. Estrutura final da árvore**

**Árvore consolidada.** O desenho abaixo integra a separação em data-processing, legal-research e legal-core, sem conflitar com a camada transversal descrita no documento de ecossistema para agentes.

juridico-cli/  
├── apps/  
│ ├── data-processing/  
│ │ ├── README.md  
│ │ ├── src/data_processing/  
│ │ │ ├── cli.py  
│ │ │ ├── orchestrator/  
│ │ │ │ ├── pipeline_runner.py  
│ │ │ │ ├── stage_router.py  
│ │ │ │ └── contracts.py  
│ │ │ ├── converters/  
│ │ │ │ ├── markdown_engine/  
│ │ │ │ ├── pdf_to_md/  
│ │ │ │ ├── pdf_to_text/  
│ │ │ │ ├── doc_to_md/  
│ │ │ │ └── image_ocr/  
│ │ │ ├── cleaners/  
│ │ │ │ ├── clean_legal_docs.py  
│ │ │ │ ├── markdown_cleaner.py  
│ │ │ │ └── metadata_normalizer.py  
│ │ │ ├── rule_analysis/  
│ │ │ │ ├── analisador_de_regras.py  
│ │ │ │ └── structural_rules.py  
│ │ │ ├── collectors/  
│ │ │ │ ├── collector_cad_obr/  
│ │ │ │ │ ├── main.py  
│ │ │ │ │ ├── config.yaml  
│ │ │ │ │ ├── io.schema.json  
│ │ │ │ │ ├── prompts/  
│ │ │ │ │ ├── skills/  
│ │ │ │ │ ├── schemas/  
│ │ │ │ │ ├── services/  
│ │ │ │ │ └── validators/  
│ │ │ │ └── collector_proc/  
│ │ │ │ ├── main.py  
│ │ │ │ ├── config.yaml  
│ │ │ │ ├── io.schema.json  
│ │ │ │ ├── prompts/  
│ │ │ │ ├── skills/  
│ │ │ │ ├── schemas/  
│ │ │ │ ├── services/  
│ │ │ │ └── validators/  
│ │ │ ├── validation/  
│ │ │ │ ├── schema_validation.py  
│ │ │ │ ├── contract_validation.py  
│ │ │ │ └── output_checks.py  
│ │ │ ├── loaders/  
│ │ │ │ ├── qdrant_loader.py  
│ │ │ │ ├── json_store.py  
│ │ │ │ └── index_registry.py  
│ │ │ └── contracts/  
│ │ │ ├── ingestion_job.schema.json  
│ │ │ ├── normalized_doc.schema.json  
│ │ │ └── extraction_result.schema.json  
│ │ └── tests/  
│ ├── legal-research/  
│ │ ├── README.md  
│ │ ├── src/legal_research/  
│ │ │ ├── cli.py  
│ │ │ ├── case_law_cli/  
│ │ │ ├── law_cli/  
│ │ │ ├── retrieval/  
│ │ │ ├── jurisprudence/  
│ │ │ ├── legislation/  
│ │ │ └── doctrine/  
│ │ └── tests/  
│ ├── legal-core/  
│ │ ├── README.md  
│ │ ├── src/legal_core/  
│ │ │ ├── cli.py  
│ │ │ ├── firac_cli/  
│ │ │ ├── compliance_cli/  
│ │ │ ├── petition_cli/  
│ │ │ ├── evidence_agent/  
│ │ │ ├── opinions/  
│ │ │ ├── strategy/  
│ │ │ └── drafting/  
│ │ └── tests/  
│ └── orchestrator-cli/  
│ ├── README.md  
│ ├── src/orchestrator_cli/  
│ │ ├── cli.py  
│ │ ├── dispatch.py  
│ │ └── registry.py  
│ └── tests/  
├── platform/  
│ ├── skill-runtime/  
│ │ ├── skill_dispatcher.py  
│ │ └── prompts/system_prompt.md  
│ ├── skills-library/  
│ │ ├── shared/  
│ │ ├── collector-cad-obr/  
│ │ ├── collector-proc/  
│ │ ├── case-law/  
│ │ ├── law/  
│ │ ├── firac/  
│ │ ├── compliance/  
│ │ ├── petition/  
│ │ └── tools_sandbox/tool_registry.json  
│ ├── memory-and-experiences/  
│ │ ├── visual_tactics/  
│ │ ├── document_tactics/  
│ │ └── experience_rewriter.py  
│ └── continuous-learning/  
│ ├── agentic_proposing/  
│ ├── sage_rl/  
│ └── network_expansion/  
├── packages/  
│ ├── shared-core/  
│ ├── shared-llm/  
│ ├── shared-schemas/  
│ ├── shared-utils/  
│ └── shared-legal/  
├── var/  
│ ├── input/raw/  
│ ├── input/md/  
│ ├── input/json/  
│ ├── staging/  
│ ├── output/  
│ ├── logs/  
│ ├── artifacts/  
│ ├── cache/  
│ └── backups/  
├── docs/  
│ ├── architecture/  
│ ├── runbooks/  
│ ├── flows/  
│ └── app-maps/  
├── infra/  
│ ├── docker/  
│ ├── qdrant/  
│ ├── mcp/  
│ └── env/  
├── scripts/  
├── tests/  
├── .github/  
├── pyproject.toml  
├── uv.lock  
├── ruff.toml  
└── README.md

# **2\. Papel de cada bloco**

| Bloco                           | Responsabilidade principal                                                     | Observação arquitetural                             |
| :------------------------------ | :----------------------------------------------------------------------------- | :-------------------------------------------------- |
| apps/data-processing            | Conversão, limpeza, análise de regras, extração estruturada, validação e carga | Abriga os collectors e o pipeline unificado         |
| apps/legal-research             | Pesquisa jurisprudencial, legislação, doutrina e retrieval                     | Não produz a peça final; fornece base jurídica      |
| apps/legal-core                 | FIRAC, compliance, petition, evidence, parecer e estratégia                    | Representa o corpo jurídico do sistema              |
| apps/orchestrator-cli           | Entrada operacional do monorepo e despacho entre apps                          | Coordena execuções sem concentrar regras de domínio |
| platform/skill-runtime          | Carregamento, registro e despacho de skills                                    | Camada transversal compartilhada pelos apps         |
| platform/skills-library         | Biblioteca padronizada de skills, prompts e recursos auxiliares                | Evita duplicação entre apps                         |
| platform/memory-and-experiences | Experiências e táticas regravadas por contexto                                 | Suporta documentos difíceis e rotas especiais       |
| platform/continuous-learning    | Aprendizado contínuo e expansão futura                                         | Pode iniciar vazio, mas a pasta deve existir        |

# **3\. Integração dos projetos reaproveitados no data-processing**

**Pipeline unificado.** Os três projetos de extração devem ser aproveitados como etapas independentes do novo pipeline:

| Origem reaproveitada                 | Novo destino                          | Função no pipeline                                  |
| :----------------------------------- | :------------------------------------ | :-------------------------------------------------- |
| Motor de conversão do markdown       | converters/markdown_engine            | Entrada e padronização inicial                      |
| app_streamlit/clean_legal_docs.py    | cleaners/clean_legal_docs.py          | Limpeza jurídica e normalização textual             |
| pdf_legal_br/analisador_de_regras.py | rule_analysis/analisador_de_regras.py | Leitura de regras estruturais do documento          |
| collector-cad-obr                    | collectors/collector_cad_obr          | Extração estruturada do domínio cadastro/obrigações |
| collector-proc                       | collectors/collector_proc             | Extração estruturada do domínio processual          |

| _Sequência lógica do pipeline: entrada bruta → conversão → limpeza jurídica → análise de regras → collector especializado → validação → persistência/carga._ |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------- |

# **4\. Regras de separação obrigatórias**

**•** Dados de runtime devem sair da raiz e ficar em var/: input, output, logs, artifacts, cache e backups.

**•** Código compartilhado deve ser movido para packages/: schemas globais, utilitários, gateway de LLM e modelos comuns.

**•** Skills compartilhadas devem ficar em platform/skills/; apenas variações estritamente locais devem permanecer dentro de um app.

**•** A raiz do repositório deve conter apenas configuração global, documentação central, infraestrutura e scripts operacionais.

# **5\. Mapeamento da estrutura atual para a nova estrutura**

| Estrutura atual                                 | Nova posição                                                          |
| :---------------------------------------------- | :-------------------------------------------------------------------- |
| agents/collector-cad_obr                        | apps/data-processing/src/data_processing/collectors/collector_cad_obr |
| agents/collector-proc                           | apps/data-processing/src/data_processing/collectors/collector_proc    |
| agents/case-law-cli                             | apps/legal-research/src/legal_research/case_law_cli                   |
| agents/law-cli                                  | apps/legal-research/src/legal_research/law_cli                        |
| agents/firac-cli                                | apps/legal-core/src/legal_core/firac_cli                              |
| agents/compliance-cli                           | apps/legal-core/src/legal_core/compliance_cli                         |
| agents/petition-cli                             | apps/legal-core/src/legal_core/petition_cli                           |
| agents/evidence-agent                           | apps/legal-core/src/legal_core/evidence_agent                         |
| pipelines/                                      | apps/data-processing/src/data_processing/                             |
| schemas/                                        | packages/shared-schemas/ e schemas locais por app                     |
| prompts/ e skills/                              | platform/skills-library/ e complementos locais quando necessário      |
| input/, outputs/, logs/, artifacts/, backup(s)/ | var/                                                                  |

# **6\. Decisão final**

**Conclusão.** A estrutura final recomendada é híbrida. Os três apps resolvem o fluxo do negócio, enquanto a plataforma transversal preserva o desenho do ecossistema de agentes. Isso mantém o projeto escalável sem desmontar os componentes que hoje já dependem de LLM, skills e schemas.
