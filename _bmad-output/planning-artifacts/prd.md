---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type']
inputDocuments:
  - docs/architecture/juridico_cli_documento_mestre.md
  - docs/architecture/juridico_cli_estado_real_consolidado.md
  - project-context.md
  - docs/architecture/juridico_cli_gaps_e_proximo_passo.md
workflowType: 'prd'
classification:
  projectType: CLI / Pipeline de processamento documental
  domain: Jurídico / LegalTech
  complexity: Alta
  projectContext: brownfield
---

# Product Requirements Document - juridico-cli

**Author:** Kiko (via BMad PM Agent)
**Date:** 2026-04-06

---

## Executive Summary

O **juridico-cli** é um sistema de processamento documental jurídico, organizado em arquitetura **skill-centric**, que automatiza a extração estruturada de documentos jurídicos (petições, contratos, escrituras, decisões, procurações, mandatos) usando LLMs com schemas validados.

O pipeline genérico de base (**pdf-to-md → md-clean-markdown → md-frontmatter-yaml**) é agnóstico de domínio e reutilizável. A camada jurídica especializada atualmente validada no fluxo principal é composta por 10 skills `extr-*` e 2 skills `jus-*`, enquanto o repositório contém 15 skills no total, das quais 13 estão registradas/operacionais no baseline atual. Perfis de LLM diferenciados por complexidade (`fast_extraction`, `high_reasoning`, `large_context`, `local_preprocessing`) são aplicados conforme a natureza de cada skill.

O runtime canônico (`platform/skill-runtime/`) resolve skills via registry, carrega bundles (`SKILL.md` + `extraction-base.md` + schema JSON) e despacha com o profile LLM adequado. O módulo operacional (`apps/data-processing/`) expõe um CLI Typer com pipeline de 6 etapas: convert → clean → analyze → collect → validate → load.

**Este PRD trata da evolução incremental de um projeto brownfield existente, preservando o baseline implantado e diferenciando claramente estado atual, arquitetura-alvo e gaps reais.**

### Visão de Evolução

O documento mestre define três componentes previstos na arquitetura-alvo e ainda não implantados no baseline atual: **Mem0** (memória persistente e episódica), **TurboQuant** (eficiência contextual via compressão de vetores) e **RLM** (inferência recursiva para contexto extenso). O PRD cobre a implantação incremental desses componentes, a ativação da extração LLM real (hoje usando `DummyLLMClient`), o registro das 2 skills pendentes, e a validação automatizada das skills.

### O que Torna Este Produto Especial

1. **Skill-centric de verdade** — cada capacidade é uma unidade registrável, despachável e validável, com profile LLM próprio. Não é um monólito de prompts.
2. **Pipeline genérico + especialização jurídica** — a base documental é reutilizável para qualquer tipo de documento; a camada jurídica é construída acima, sem contaminar o core.
3. **Runtime canônico com registry** — skill nova só roda se estiver registrada. Isso cria governança explícita de capacidade.
4. **Rastreabilidade jurídica** — as saídas que exigem rastreabilidade jurídica preservam vínculo com a fonte/âncora conforme a skill e o schema aplicável.
5. **Memória e eficiência como componentes estruturais** — Mem0 e TurboQuant não são acessórios; são parte do desenho arquitetural obrigatório.

### Classificação do Projeto

| Dimensão | Valor |
|---|---|
| Tipo | CLI / Pipeline de processamento documental |
| Domínio | Jurídico / LegalTech |
| Complexidade | Alta |
| Contexto | Brownfield — runtime, 13 skills registradas/operacionais, pipeline de 6 etapas e infraestrutura Docker já implantados |

---

## Success Criteria

### User Success

O usuário considera o problema resolvido quando consegue transformar documentos jurídicos complexos em saídas estruturadas, válidas e rastreáveis, prontas para uso operacional real, sem depender de releitura manual integral.

- **Extração estruturada válida** — processar documentos jurídicos heterogêneos e obter JSON aderente ao schema aplicável, com todos os campos obrigatórios preenchidos e validados.
- **Rastreabilidade jurídica** — preservar vínculo com a fonte/âncora conforme a skill e o schema aplicável, permitindo auditoria e conferência humana.
- **Reutilização operacional** — permitir que o resultado seja consumido diretamente por etapas posteriores: evidência, reconciliação, FIRAC, pesquisa jurídica e geração de peças.
- **Redução de retrabalho** — diminuir significativamente o tempo humano gasto em leitura, localização de trechos e organização de material documental.
- **Confiança na base de trabalho** — o sucesso do usuário não é apenas "extrair um arquivo", mas conseguir converter acervo documental jurídico em base confiável para trabalho jurídico real.

### Business Success

O projeto terá valido a pena quando deixar de ser apenas uma arquitetura promissora e passar a sustentar casos jurídicos reais com consistência operacional.

- **Caso jurídico real suportado** — o juridico-cli consegue processar um caso jurídico real com processamento documental confiável e reaproveitável.
- **Cadeia sustentável** — a cadeia entre documento bruto, extração estruturada e uso jurídico posterior torna-se tecnicamente sustentável de ponta a ponta.
- **Operação sem ajustes manuais dispersos** — o fluxo principal opera sem depender de correções e adaptações manuais a cada execução.
- **Arquitetura comprovada para expansão** — o modelo skill-centric se prova viável para expansão incremental, com novas capacidades entrando sem desorganizar a base existente.
- **Infraestrutura auditável e controlável** — o sistema se consolida como infraestrutura de processamento documental jurídico auditável, modular e controlável, não como experimento de prompts.

### Technical Success

O sistema opera como planejado quando o baseline técnico está funcional, coerente com a arquitetura vigente e apto para evolução incremental.

- **15 skills enquadradas** — todas as skills do repositório corretamente classificadas; skills do baseline atual registradas e despacháveis via runtime.
- **Extração LLM real ativa** — `DummyLLMClient` substituído por `LLMClient` com Gemini API no fluxo principal aplicável.
- **Pipeline end-to-end consistente** — conversão, limpeza, análise, coleta, validação e carga executam de ponta a ponta com consistência.
- **Saídas conforme schema e contrato** — resultados respeitam schema JSON, contrato de dados e requisitos de rastreabilidade quando aplicáveis.
- **Validação automatizada suficiente** — existe cobertura de testes automatizados para reduzir regressão nas skills e no pipeline principal.
- **Mem0, TurboQuant e RLM compõem critérios de sucesso da evolução arquitetural planejada, implantados incrementalmente sem quebrar o baseline existente.**
- **Separação de camadas preservada** — core genérico, camada jurídica especializada e componentes futuros mantêm fronteiras claras.

### Preservação Arquitetural

Mem0, TurboQuant e RLM permanecem componentes obrigatórios da arquitetura-alvo do juridico-cli. Sua implantação é incremental e posterior ao baseline funcional do MVP, mas esses componentes não podem ser removidos, rebaixados a opcionais ou omitidos em futuras revisões do PRD, da arquitetura, dos épicos ou das stories. Eles devem permanecer registrados como parte do estado-alvo do projeto até sua implantação efetiva.

### Measurable Outcomes

#### Baseline / MVP

| Outcome | Métrica | Como verificar |
|---|---|---|
| Skills despacháveis | 15/15 skills registradas e resolvidas pelo `skill_dispatcher.py` | Teste de dispatch para cada bundle_id |
| Extração LLM real | `DataExtractorApp` chama Gemini API (não dummy) | Log de chamada à API + output JSON válido |
| Pipeline end-to-end | Pipeline `data-processing run` executa sem erro para um PDF de teste | Execução de ponta a ponta com log de sucesso |
| Aderência ao schema | 100% dos outputs do conjunto suportado no baseline/MVP passam em `jsonschema` validation | Validação automatizada pós-extração |
| Testes passando | `pytest` executa sem falhas nos módulos do pipeline | Execução de testes registrada |

#### Evolução Arquitetural (pós-MVP)

| Outcome | Métrica | Como verificar |
|---|---|---|
| Mem0 operacional | Experiências persistidas e recuperáveis via `get_contextual_memory` | Teste de add + search com dados reais |
| TurboQuant operacional | Vetores comprimidos com distorção dentro do threshold configurado | Métrica de qualidade pós-quantização |
| RLM operacional | Processamento de contexto extenso com decomposição em etapas | Log de etapas intermediárias de raciocínio |

---

## Product Scope

### MVP — Mínimo Viável

O que é essencial para provar que o conceito funciona:

- **15 skills do repositório enquadradas e registradas ao final do MVP, eliminando as pendências atuais do baseline.**
- **Extração LLM real ativada** — `DataExtractorApp` usa `LLMClient` com Gemini API ao invés de `DummyLLMClient`.
- **Pipeline end-to-end validado** — `data-processing run` executa de ponta a ponta com PDF real, gerando JSON válido conforme schema.
- **Validação automatizada mínima** — cada skill de extração tem script de validação de output contra seu schema JSON.
- **Testes do pipeline passando** — `pytest` executa sem falhas nos módulos de cleaner, orchestrator e validation.
- **Runbook atualizado** — documentos operacionais refletem o estado real (pipeline genérico já criado, estado real consolidado como referência).
- **Registros de divergência resolvidos** — gaps G1 (skills sem registro) e G5 (DummyLLMClient) corrigidos.

### Growth — Pós-MVP (Competitivo)

O que torna o projeto competitivo e operacionalmente maduro:

- **Mem0 implantado** — adapter funcional com persistência e recuperação de experiências de extração.
- **Validação abrangente de skills** — 100% das 15 skills com scripts de validação automatizada, não apenas as 5 atuais.
- **Testes de integração end-to-end** — pipeline completo testado com documentos jurídicos reais de múltiplos tipos.
- **Cadeia de obrigações completa** — um caso real processado de PDF a evidência estruturada com reconciliação.
- **`legal-research` operacional** — módulo de pesquisa jurídica com migração dos agentes legados `case-law-cli` e `law-cli`.
- **TurboQuant implantado** — compressão de vetores ativa com qualidade verificável.
- **RLM implantado** — processamento de contexto extenso com decomposição em etapas intermediárias.

### Vision — Futuro

O que é o sonho de longo prazo:

- **Infraestrutura de processamento documental jurídico auditável** — o juridico-cli é a base confiável para qualquer fluxo de trabalho jurídico que dependa de extração de documentos.
- **Expansão incremental por skills** — novas capacidades jurídicas (novos tipos de documento, novas análises, novos fluxos) entram como skills sem reorganizar a base.
- **Memória jurídica persistente** — o sistema aprende com cada extração, acumulando experiência verificável e recuperável por contexto.
- **Multi-domínio** — o pipeline genérico de base prova-se reutilizável para tipos de documento não jurídicos (técnico, médico, regulatório).
- **Autonomia com controle** — o operador jurídico confia no output do sistema, mas mantém auditabilidade total via anchoring e rastreabilidade de cada campo extraído.

---

## Domain-Specific Requirements

### Conformidade e Regulatório

- **Cadeia de custódia documental e probatória** — o sistema preserva o documento original sem alteração, registra hash do arquivo de origem, timestamp de processamento, versão do output e trilha de transformação entre entrada e saída.
- **Controle de acesso por caso/documento** — segregação de acesso por processo, cliente, lote documental ou matéria sensível, não apenas proteção global do sistema.
- **Minimização e finalidade (LGPD)** — o sistema processa e expõe apenas os dados necessários ao fluxo jurídico específico, evitando replicação desnecessária de dados pessoais e sensíveis em múltiplas camadas.
- **Sigilo profissional** — attorney-client privilege e documentos sob sigilo judicial são tratados como dados sensíveis com proteção adicional.
- **Auditoria de revisão humana** — toda validação, correção, rejeição ou reaproveitamento de output é registrado como evento auditável com autor, timestamp e justificativa.
- **Política de retenção e descarte** — outputs estruturados, logs, embeddings, memória e artefatos temporários possuem política explícita de retenção, expurgo e reprocessamento.
- **Preferência por processamento controlável** — o projeto preserva a possibilidade de operação local ou com controle forte sobre provedores externos, dado o sigilo e a sensibilidade jurídica.

### Riscos Específicos do Domínio

| Risco | Descrição | Mitigação |
|---|---|---|
| **Alucinação do LLM** | Inventar cláusulas, datas, valores que não existem no documento original | Anchoring obrigatório; validação por schema; bloqueio de consumo downstream para outputs sem evidência |
| **Erro semanticamente plausível** | Output passa no schema, parece correto, mas juridicamente distorce o sentido do documento | Revisão humana obrigatória para uso operacional; separação entre "extraído" e "inferido" |
| **Erro de OCR/conversão** | Problema nasce na conversão PDF→MD, afetando datas, nomes, valores e cláusulas | Validação da conversão; detecção de páginas escaneadas; alerta de qualidade de OCR |
| **Falsa sensação de confiabilidade** | JSON válido e bem formatado induz consumo indevido downstream sem conferência | Bloqueio de consumo para outputs inválidos ou sem evidência suficiente; status explícito de confiabilidade |
| **Contaminação da prova** | Edições humanas posteriores no output sem trilha de revisão enfraquecem auditabilidade | Toda edição manual registrada como evento de revisão com autor, timestamp e justificativa |
| **Dependência de provedor único** | Viabilidade operacional acoplada a um único provedor externo (Gemini API) | Abstração de provedor LLM com possibilidade de fallback controlado (llama.cpp local) |

### Integrações

#### Baseline

- **Filesystem local / diretórios controlados** — entrada e saída via estrutura `var/` com caminhos definidos.
- **Contratos JSON estáveis** — schemas JSON como interface entre etapas do pipeline.
- **Qdrant** — para fluxos que exigirem indexação semântica (coleção `decisoes` no baseline).
- **Interface futura do front-end** — comunicação com o core por API ou camada de serviço bem definida.

#### Futuras / Condicionadas a Caso Real

- PJe, e-SAJ, Eproc e outros sistemas processuais.
- APIs de tribunais (STJ, STF, TJs).
- Conectores externos de pesquisa jurídica.
- Painéis administrativos do front-end.

> **Nota:** Integrações com sistemas processuais não são obrigação do baseline sem caso de uso concreto validado. O núcleo do projeto é a infraestrutura de processamento documental jurídico rastreável.

### Padrões do Domínio

- **Documento original é fonte de verdade e permanece imutável.**
- **Output jurídico só é utilizável se houver contrato de dados claro** (schema JSON válido).
- **Revisão humana deve ter status e trilha auditável.**
- **Separar explicitamente "extraído do documento" de "inferido/derivado pelo sistema".**
- **Anchoring/rastreabilidade sempre que aplicável** — cada campo extraído preserva vínculo com a fonte.

### Anti-padrões do Domínio

- **Tratar output validado por schema como automaticamente correto do ponto de vista jurídico.**
- **Permitir edição manual de resultado sem registrar revisão.**
- **Misturar dado extraído, hipótese interpretativa e enriquecimento externo no mesmo campo.**
- **Ocultar incerteza, ausência de evidência ou ambiguidade documental.**
- **Consumir output "bonito" sem evidência suficiente.**

### Princípio Arquitetural Central

> O **juridico-cli** não deve ser apenas um extrator, mas uma **infraestrutura jurídica auditável**.

Isso significa preservar como princípio de produto:

- **Rastreabilidade** — toda saída rastreável à sua fonte documental.
- **Separação de fases** — documento, extração, validação, revisão e uso são fases distintas com status e trilha próprios.
- **Possibilidade de auditoria posterior** — qualquer output pode ser reauditado com acesso ao original, ao schema aplicado e à trilha de transformação.
- **Evolução incremental sem perda de controle** — novas capacidades (skills, módulos, integrações) entram sem perder controle sobre prova, contexto e responsabilidade.

---

## CLI / Pipeline Specific Requirements

### Project-Type Overview

O **juridico-cli** é um sistema CLI/pipeline de processamento documental jurídico com arquitetura skill-centric. A CLI Typer é a interface operacional e técnica canônica do baseline. O pipeline executa 6 etapas (convert → clean → analyze → collect → validate → load) sobre lotes de documentos heterogêneos, produzindo outputs JSON validados por schemas.

### Technical Architecture Considerations

#### Interface de Comando e Camadas de Acesso

- **CLI permanece canônica** — a interface CLI Typer é a porta de entrada operacional e técnica do baseline. Não é descartada nem convertida em interface legada.
- **Front-end como camada humana** — o front-end atua como interface de acesso humano sobre o núcleo canônico (runtime + pipeline + contratos de dados).
- **Camada de serviço compartilhada** — CLI e front-end consomem a mesma camada de serviço/orquestração, sem acoplamento direto entre si.
- **Núcleo canônico** — runtime skill-centric, pipeline de processamento e contratos de dados formam o núcleo independente de interface.

#### Formato e Contrato de Dados

- **Schema é lei** — cada skill deve produzir output aderente ao schema aplicável. Output inválido não é consumido downstream.
- **Transformação intermediária formalizada** — quando houver transição entre etapas com necessidades distintas, a transformação deve ser explícita, versionada e validável.
- **Contrato explícito entre etapas** — não se assume que output bruto de uma skill serve automaticamente como contrato universal para todas as etapas seguintes.

#### Performance e Escala

- **Baseline: dezenas a centenas de documentos por execução** — o sistema suporta lotes relevantes de documentos jurídicos como operação padrão.
- **Documentos extensos e heterogêneos** — peças e conjuntos com centenas de páginas são cenário esperado.
- **Caminho para assincronia** — o pipeline opera de forma síncrona por etapa no baseline, mas a arquitetura preserva caminho para processamento em lote, filas, paralelização controlada e futura assincronia.
- **Rastreabilidade inegociável** — desempenho não compromete rastreabilidade, validação e auditabilidade.

#### Gestão de Estado e Erros

- **Estado observável por etapa** — cada etapa deixa estado auditável com insumos, logs e artefatos parciais.
- **Falha registrada com contexto** — erro registra onde ocorreu, com insumos da etapa, logs relevantes e artefatos disponíveis.
- **Checkpoint/resume sobre rollback** — o projeto caminha para suportar retomada controlada de pipeline interrompido, sem obrigar reprocessamento total. Rollback clássico não é o conceito correto para pipeline documental; o prioritário é checkpoint, isolamento da falha e reexecução segura da etapa afetada.

#### Provedor LLM e Fallback

- **Gemini como baseline principal** — Gemini API é o provedor de LLM do baseline operacional.
- **Abstração de cliente preservada** — a interface `LLMClient` é a abstração que isola o provedor concreto.
- **Fallback como requisito arquitetural** — fallback local (llama.cpp) ou alternativo existe como capacidade arquitetural real. A viabilidade do projeto não depende de estabilidade comercial absoluta de um único modelo.
- **Risco operacional formal** — custo, disponibilidade, latência e mudança de política de provedor são tratados como risco operacional do produto.

#### Observabilidade

- **Logs são o mínimo** — registro de execução por etapa, skill, documento e lote via `var/logs/`.
- **Tipos de falha identificáveis** — o sistema permite identificar falhas de dispatch, validação, schema, OCR, chamada LLM e carga.
- **Evolução para métricas e alertas** — métricas, alertas e painéis entram por evolução incremental, especialmente para operação em lote e front-end.
- **Dupla finalidade** — observabilidade serve tanto para operação técnica quanto para auditoria jurídica.

### Implementation Considerations

| Dimensão | Baseline Atual | Evolução Prevista |
|---|---|---|
| Interface | CLI Typer (5 comandos) | CLI canônica + front-end como camada humana |
| Pipeline | Síncrono por etapa | Caminho para assincronia, filas, paralelização |
| Estado | Sem checkpoint/resume | Retomada controlada de pipeline interrompido |
| LLM | Gemini API (DummyLLMClient no extractor) | Gemini real + abstração com fallback local |
| Observabilidade | Logs em `var/logs/` | Métricas, alertas, painéis operacionais |
| Contrato de dados | Schemas JSON por skill | Schemas versionados + transformações intermediárias formalizadas |
| Escala | Dezenas a centenas de docs | Lotes maiores com paralelização controlada |
