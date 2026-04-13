---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-e-edit']
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
**Last Edit:** 2026-04-07 — Edição estrutural: brownfield consolidado, baseline vs arquitetura-alvo separados, front-end registrado como camada futura, Mem0/TurboQuant/RLM preservados como obrigatórios, jornadas do usuário adicionadas.  
**Last Edit 2:** 2026-04-07 — FRs numerados (FR-001 a FR-034), métricas de baseline atual adicionadas, seção Out of Scope adicionada.

---

## Executive Summary

O **juridico-cli** é um sistema de processamento documental jurídico, organizado em arquitetura **skill-centric**, que automatiza a extração estruturada de documentos jurídicos (petições, contratos, escrituras, decisões, procurações, mandatos) usando LLMs com schemas validados.

**Este é um projeto brownfield.** O baseline atual já possui runtime canônico (`platform/skill-runtime/`), 13 skills registradas e operacionais, pipeline de 6 etapas (`convert → clean → analyze → collect → validate → load`) via CLI Typer, e infraestrutura Docker implantada. O repositório contém 15 skills no total; 2 skills adicionais estão presentes no código mas ainda não registradas no runtime.

O pipeline genérico de base (**pdf-to-md → md-clean-markdown → md-frontmatter-yaml**) é agnóstico de domínio e reutilizável. A camada jurídica especializada atualmente validada no fluxo principal é composta por 10 skills `extr-*` e 2 skills `jus-*`. Perfis de LLM diferenciados por complexidade (`fast_extraction`, `high_reasoning`, `large_context`, `local_preprocessing`) são aplicados conforme a natureza de cada skill.

O runtime canônico resolve skills via registry, carrega bundles (`SKILL.md` + `extraction-base.md` + schema JSON) e despacha com o profile LLM adequado.

**Este PRD trata da evolução incremental de um projeto brownfield existente.** Ele mantém separação explícita entre:
- **(a) Baseline atual implantado** — o que já opera hoje;
- **(b) Arquitetura-alvo** — o estado final planejado, com componentes ainda não implantados;
- **(c) Gaps reais** — divergências concretas entre (a) e (b) que precisam ser fechadas.

### Visão de Evolução

O documento mestre define três componentes previstos na arquitetura-alvo e ainda não implantados no baseline atual: **Mem0** (memória persistente e episódica), **TurboQuant** (eficiência contextual via compressão de vetores) e **RLM** (inferência recursiva para contexto extenso). Estes são **componentes obrigatórios da arquitetura-alvo** — sua implantação é incremental e posterior ao baseline funcional do MVP, mas não podem ser removidos, rebaixados a opcionais ou omitidos em revisões futuras deste PRD, da arquitetura, dos épicos ou das stories.

O PRD cobre a implantação incremental desses componentes, a ativação da extração LLM real (hoje usando `DummyLLMClient` no extractor), o registro das 2 skills pendentes, e a validação automatizada das skills.

### O que Torna Este Produto Especial

1. **Skill-centric de verdade** — cada capacidade é uma unidade registrável, despachável e validável, com profile LLM próprio. Não é um monólito de prompts.
2. **Pipeline genérico + especialização jurídica** — a base documental é reutilizável para qualquer tipo de documento; a camada jurídica é construída acima, sem contaminar o core.
3. **Runtime canônico com registry** — skill nova só roda se estiver registrada. Isso cria governança explícita de capacidade.
4. **Rastreabilidade jurídica** — as saídas que exigem rastreabilidade jurídica preservam vínculo com a fonte/âncora conforme a skill e o schema aplicável.
5. **Memória e eficiência como componentes estruturais** — Mem0, TurboQuant e RLM não são acessórios; são parte do desenho arquitetural obrigatório da arquitetura-alvo.

### Classificação do Projeto

| Dimensão | Valor |
|---|---|
| Tipo | CLI / Pipeline de processamento documental |
| Domínio | Jurídico / LegalTech |
| Complexidade | Alta |
| Contexto | Brownfield — runtime, 13 skills registradas/operacionais, pipeline de 6 etapas e infraestrutura Docker já implantados |

### Estado do Projeto: Brownfield

| Camada | Estado |
|---|---|
| **Baseline atual (implantado)** | Runtime skill-runtime, 13/15 skills registradas e operacionais, CLI Typer com 5 comandos, pipeline de 6 etapas, Docker, Qdrant (coleção `decisoes`) |
| **Gaps do baseline** | 2 skills não registradas; `DummyLLMClient` no extractor ao invés de LLM real; validação automatizada limitada a 5 skills; sem checkpoint/resume |
| **Arquitetura-alvo** | 15/15 skills registradas; extração LLM real (Gemini API); Mem0 + TurboQuant + RLM operacionais; front-end como camada humana de acesso; validação abrangente de todas as skills; 34 requisitos funcionais numerados (FR-001 a FR-034) |

---

## User Journeys

### Jornada 1 — Operador Jurídico no Baseline Atual (CLI-First)

> **Contexto:** Advogado ou paralel precisa processar um lote de documentos jurídicos (petições, contratos, decisões) para extração estruturada. O sistema opera via CLI.

| Etapa | Ação do Usuário | Comportamento do Sistema | Output Esperado |
|---|---|---|---|
| **1. Preparação** | Organiza PDFs em diretório de entrada (`var/input/`) | — | Documentos prontos para processamento |
| **2. Execução** | Executa `juridico-cli data-processing run --input var/input/ --output var/output/` | Pipeline executa: convert → clean → analyze → collect → validate → load | Log de progresso por etapa |
| **3. Conversão** | — | PDFs convertidos para Markdown via ferramenta de conversão | Arquivos `.md` em diretório intermediário |
| **4. Limpeza** | — | Markdown limpo de artefatos de conversão, formatação normalizada | Markdown estruturado e consistente |
| **5. Extração** | — | Skill dispatcher resolve skills aplicáveis, carrega bundles, despacha com profile LLM (atualmente DummyLLMClient; alvo: Gemini API) | JSON por documento, aderente ao schema da skill |
| **6. Validação** | — | Output validado contra schema JSON aplicável | JSON válido ou relatório de erro de schema |
| **7. Carga** | — | Resultados consolidados em `var/output/` | Estrutura de saída com JSON validado, logs e metadados |
| **8. Conferência** | Operador revisa outputs JSON | — | Documentos estruturados prontos para uso jurídico posterior |

**Pontos de dor no baseline atual:**
- Extração usa `DummyLLMClient` (não extrai de verdade — retorna mock)
- 2 skills não estão registradas no runtime
- Sem validação automatizada para todas as skills (apenas 5 cobertas)
- Sem checkpoint/resume — se o pipeline falhar, reprocessa tudo

### Jornada 2 — Operador Jurídico com Arquitetura-Alvo (CLI + Front-End)

> **Contexto:** Evolução do produto com front-end como camada humana de acesso, sem substituir a CLI. O operador pode interagir via interface web para auditoria, revisão e acompanhamento.

| Etapa | Ação do Usuário | Comportamento do Sistema | Output Esperado |
|---|---|---|---|
| **1. Preparação** | Upload de documentos via front-end OU diretório CLI | Front-end envia para camada de serviço; CLI opera como baseline | Documentos ingressados |
| **2. Execução** | Dispara processamento via CLI **ou** front-end | Camada de serviço compartilha orquestração entre CLI e front-end | Pipeline em execução |
| **3-7. Pipeline** | — | Idêntico à Jornada 1, com extração LLM real (Gemini API) | JSON validado com dados reais extraídos |
| **8. Auditoria via front-end** | Operador visualiza resultados, rastreabilidade e evidências no front-end | Front-end consulta camada de serviço; exibe JSON, schema aplicado, vínculo com fonte | Painel de auditoria com documento original, extração e evidências lado a lado |
| **9. Revisão humana** | Operador marca campos como confirmados, questionados ou corrigidos | Toda edição registrada como evento de revisão (autor, timestamp, justificativa) | Trilha de auditoria completa |
| **10. Consumo downstream** | Output revisado alimenta evidência, FIRAC, pesquisa jurídica, peças | Sistema consome apenas outputs validados e/ou revisados | Cadeia jurídica completa |

**Notas sobre esta jornada:**
- O front-end **não substitui a CLI** — ambas consomem a mesma camada de serviço.
- A CLI permanece a interface operacional e técnica canônica do baseline.
- O front-end é **camada futura de acesso humano** — sua existência não invalida nem degrada a CLI.
- Recursos de correção manual completa no front-end ainda não foram definidos em escopo; esta jornada trata o front-end como interface de **auditoria e acompanhamento**, não como editor documental completo.

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

#### Technical Success — Baseline / MVP

- **15 skills do repositório corretamente classificadas** — 13 do baseline já registradas e operacionais; 2 pendentes registradas ao final do MVP, totalizando 15/15 despacháveis via runtime.
- **Extração LLM real ativa** — `DummyLLMClient` substituído por `LLMClient` com Gemini API no fluxo principal aplicável.
- **Pipeline end-to-end consistente** — conversão, limpeza, análise, coleta, validação e carga executam de ponta a ponta com consistência para documentos reais.
- **Saídas conforme schema e contrato** — resultados respeitam schema JSON, contrato de dados e requisitos de rastreabilidade quando aplicáveis.
- **Validação automatizada suficiente** — existe cobertura de testes automatizados para reduzir regressão nas skills e no pipeline principal.
- **Testes do pipeline passando** — `pytest` executa sem falhas nos módulos de cleaner, orchestrator e validation.

#### Technical Success — Evolução Arquitetural (pós-MVP)

- **Mem0 operacional** — adapter funcional com persistência e recuperação de experiências de extração.
- **TurboQuant operacional** — compressão de vetores ativa com qualidade verificável.
- **RLM operacional** — processamento de contexto extenso com decomposição em etapas intermediárias de raciocínio.
- **Separação de camadas preservada** — core genérico, camada jurídica especializada, front-end como camada futura e componentes de memória/eficiência mantêm fronteiras claras.
- **Mem0, TurboQuant e RLM compõem critérios de sucesso da evolução arquitetural planejada, implantados incrementalmente sem quebrar o baseline existente.**

### Preservação Arquitetural — Componentes Obrigatórios da Arquitetura-Alvo

> **Esta seção é normativa e permanente.** Aplica-se a todas as revisões futuras deste PRD, da arquitetura, dos épicos e das stories.

**Mem0, TurboQuant e RLM são componentes obrigatórios da arquitetura-alvo do juridico-cli.**

- **Sua implantação é incremental e posterior ao baseline funcional do MVP.** Eles não são pré-requisito para que o MVP seja considerado entregue.
- **Eles não podem ser removidos, rebaixados a opcionais ou omitidos** em futuras revisões do PRD, da arquitetura, dos épicos ou das stories.
- **Devem permanecer registrados como parte do estado-alvo do projeto** até sua implantação efetiva.
- **Qualquer revisão deste PRD que os omita, rebaixe ou remova está automaticamente incorreta** e deve ser corrigida para restaurá-los como componentes obrigatórios da arquitetura-alvo.

| Componente | Função | Status no Baseline | Status na Arquitetura-Alvo |
|---|---|---|---|
| **Mem0** | Memória persistente e episódica — o sistema acumula experiência verificável por contexto de extração | Não implantado | Obrigatório — adapter funcional com add/search |
| **TurboQuant** | Eficiência contextual via compressão de vetores — reduz custo e latência de contexto extenso | Não implantado | Obrigatório — compressão com distorção dentro de threshold |
| **RLM** | Inferência recursiva para contexto extenso — decomposição em etapas intermediárias de raciocínio | Não implantado | Obrigatório — processamento com log de etapas |

---

## Measurable Outcomes

### Baseline / MVP

| Outcome | Métrica | Como verificar |
|---|---|---|
| Skills despacháveis | 13/13 do baseline já operacionais + 2 pendentes registradas = 15/15 ao final do MVP | Teste de dispatch para cada bundle_id |
| Extração LLM real | `DataExtractorApp` chama Gemini API (não dummy) | Log de chamada à API + output JSON válido |
| Pipeline end-to-end | Pipeline `data-processing run` executa sem erro para um PDF de teste | Execução de ponta a ponta com log de sucesso |
| Aderência ao schema | 100% dos outputs do conjunto suportado no baseline/MVP passam em `jsonschema` validation | Validação automatizada pós-extração |
| Testes passando | `pytest` executa sem falhas nos módulos do pipeline | Execução de testes registrada |

### Evolução Arquitetural (pós-MVP)

| Outcome | Métrica | Como verificar |
|---|---|---|
| Mem0 operacional | Experiências persistidas e recuperáveis via `get_contextual_memory` | Teste de add + search com dados reais |
| TurboQuant operacional | Vetores comprimidos com distorção dentro do threshold configurado | Métrica de qualidade pós-quantização |
| RLM operacional | Processamento de contexto extenso com decomposição em etapas | Log de etapas intermediárias de raciocínio |

### Métricas de Baseline Atual (Pré-MVP)

> **Propósito:** Registrar o estado observável do baseline atual para permitir comparação quantitativa pré/pós-MVP. Estes números refletem o que o sistema **hoje** é capaz de fazer, não o estado-alvo.

| Métrica | Valor no Baseline Atual | Meta Pós-MVP | Como medir |
|---|---|---|---|
| Skills registradas no runtime | 13/15 | 15/15 | Contagem no `skill_registry.yaml` |
| Extração LLM real | ❌ `DummyLLMClient` (mock) | ✅ Gemini API | Log de chamada à API |
| Validação automatizada coberta | 5 skills (parcial) | 15/15 skills | Contagem de scripts de validação |
| Pipeline end-to-end | Operacional (sem validação formal) | Operacional com validação | Execução de teste com PDF real |
| Checkpoint/resume | ❌ Não implementado | ✅ Implementado | Teste de interrupção e retomada |
| Mem0 | ❌ Não implantado | ❌ Pós-MVP (Evolução Arquitetural) | — |
| TurboQuant | ❌ Não implantado | ❌ Pós-MVP (Evololução Arquitetural) | — |
| RLM | ❌ Não implantado | ❌ Pós-MVP (Evolução Arquitetural) | — |

> **Nota:** Mem0, TurboQuant e RLM **não são metas do MVP**. São componentes obrigatórios da arquitetura-alvo cuja implantação ocorre na fase de Evolução Arquitetural (pós-MVP).

---

## Product Scope

### MVP — Mínimo Viável

O que é essencial para provar que o conceito funciona no **baseline atual brownfield**:

- **15 skills do repositório enquadradas e registradas** — 13 já operacionais no baseline + 2 pendentes registradas ao final do MVP, eliminando as pendências atuais.
- **Extração LLM real ativada** — `DataExtractorApp` usa `LLMClient` com Gemini API ao invés de `DummyLLMClient`.
- **Pipeline end-to-end validado** — `data-processing run` executa de ponta a ponta com PDF real, gerando JSON válido conforme schema.
- **Validação automatizada mínima** — cada skill de extração tem script de validação de output contra seu schema JSON (ampliando das 5 skills atuais para todas as 15).
- **Testes do pipeline passando** — `pytest` executa sem falhas nos módulos de cleaner, orchestrator e validation.
- **Runbook atualizado** — documentos operacionais refletem o estado real pós-MVP (pipeline genérico já criado, estado real consolidado como referência).
- **Gaps do baseline resolvidos** — G1 (skills sem registro) e G5 (DummyLLMClient) corrigidos.

> **O MVP NÃO inclui Mem0, TurboQuant ou RLM.** Esses são componentes da arquitetura-alvo cuja implantação é incremental e posterior ao MVP.

### Growth — Pós-MVP (Competitivo)

O que torna o projeto competitivo e operacionalmente maduro:

- **Mem0 implantado** — adapter funcional com persistência e recuperação de experiências de extração.
- **Validação abrangente de skills** — 100% das 15 skills com scripts de validação automatizada com cobertura real de qualidade.
- **Testes de integração end-to-end** — pipeline completo testado com documentos jurídicos reais de múltiplos tipos.
- **Cadeia de obrigações completa** — um caso real processado de PDF a evidência estruturada com reconciliação.
- **`legal-research` operacional** — módulo de pesquisa jurídica com migração dos agentes legados `case-law-cli` e `law-cli`.
- **TurboQuant implantado** — compressão de vetores ativa com qualidade verificável.
- **RLM implantado** — processamento de contexto extenso com decomposição em etapas intermediárias.
- **Front-end como camada humana de acesso** — interface web para auditoria, acompanhamento e revisão de extrações, consumindo a mesma camada de serviço da CLI.

### Vision — Futuro

O que é o sonho de longo prazo:

- **Infraestrutura de processamento documental jurídico auditável** — o juridico-cli é a base confiável para qualquer fluxo de trabalho jurídico que dependa de extração de documentos.
- **Expansão incremental por skills** — novas capacidades jurídicas (novos tipos de documento, novas análises, novos fluxos) entram como skills sem reorganizar a base.
- **Memória jurídica persistente** — o sistema aprende com cada extração, acumulando experiência verificável e recuperável por contexto (Mem0 em operação plena).
- **Multi-domínio** — o pipeline genérico de base prova-se reutilizável para tipos de documento não jurídicos (técnico, médico, regulatório).
- **Autonomia com controle** — o operador jurídico confia no output do sistema, mas mantém auditabilidade total via anchoring e rastreabilidade de cada campo extraído.
- **Front-end maduro** — interface web completa com correção manual auditável, gestão de casos, painéis operacionais e integração com sistemas processuais.

### Out of Scope

O que este PRD **não** cobre:

- **Integrações com sistemas processuais (PJe, e-SAJ, Eproc, APIs de tribunais)** — sem caso de uso concreto validado. Estas integrações são condicionadas a demanda real e não são obrigação do baseline.
- **Correção manual completa no front-end** — o front-end é tratado como camada de auditoria e acompanhamento nesta fase. Funcionalidades de editor documental completo com correção manual integral ainda não foram definidas em escopo.
- **Substituição da CLI pelo front-end** — a CLI Typer é a interface operacional e técnica canônica do baseline. O front-end complementa, nunca substitui.
- **Mem0, TurboQuant e RLM como entregas do MVP** — são componentes obrigatórios da arquitetura-alvo, mas sua implantação é incremental e posterior ao baseline funcional do MVP. Tratá-los como se já estivessem no baseline atual é incorreto.
- **Fallback de provedor LLM como entrega do MVP** — a abstração de cliente com fallback local (llama.cpp) é requisito arquitetural, não entrega do MVP.
- **Migração de agentes legados (`case-law-cli`, `law-cli`)** — entra em Growth, não no MVP.
- **Métricas, alertas e painéis operacionais de observabilidade** — evoluem incrementalmente a partir dos logs atuais (`var/logs/`). Não são entrega do MVP.

> **Regra:** Qualquer item acima que apareça em uma revisão futura como "feito" ou "entregue" sem justificativa explícita de mudança de escopo deve ser sinalizado como inconsistência com este PRD.

---

## Domain-Specific Requirements

### Conformidade e Regulatório

- **FR-001 — Cadeia de custódia documental e probatória** — o sistema preserva o documento original sem alteração, registra hash do arquivo de origem, timestamp de processamento, versão do output e trilha de transformação entre entrada e saída.
- **FR-002 — Controle de acesso por caso/documento** — segregação de acesso por processo, cliente, lote documental ou matéria sensível, não apenas proteção global do sistema.
- **FR-003 — Minimização e finalidade (LGPD)** — o sistema processa e expõe apenas os dados necessários ao fluxo jurídico específico, evitando replicação desnecessária de dados pessoais e sensíveis em múltiplas camadas.
- **FR-004 — Sigilo profissional** — attorney-client privilege e documentos sob sigilo judicial são tratados como dados sensíveis com proteção adicional.
- **FR-005 — Auditoria de revisão humana** — toda validação, correção, rejeição ou reaproveitamento de output é registrado como evento auditável com autor, timestamp e justificativa.
- **FR-006 — Política de retenção e descarte** — outputs estruturados, logs, embeddings, memória e artefatos temporários possuem política explícita de retenção, expurgo e reprocessamento.
- **FR-007 — Preferência por processamento controlável** — o projeto preserva a possibilidade de operação local ou com controle forte sobre provedores externos, dado o sigilo e a sensibilidade jurídica.

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

#### Camada de Serviço (compartilhada entre CLI e front-end futuro)

- **Camada de serviço/orquestração** — CLI e front-end consomem a mesma camada de serviço, sem acoplamento direto entre si.
- **Interface futura do front-end** — comunicação com o core por API ou camada de serviço bem definida. O front-end é camada futura de acesso humano, **não substitui a CLI**.

#### Futuras / Condicionadas a Caso Real

- PJe, e-SAJ, Eproc e outros sistemas processuais.
- APIs de tribunais (STJ, STF, TJs).
- Conectores externos de pesquisa jurídica.
- Painéis administrativos do front-end.

> **Nota:** Integrações com sistemas processuais não são obrigação do baseline sem caso de uso concreto validado. O núcleo do projeto é a infraestrutura de processamento documental jurídico rastreável.

### Padrões do Domínio

- **FR-008 — Documento original é fonte de verdade e permanece imutável.**
- **FR-009 — Output jurídico só é utilizável se houver contrato de dados claro** (schema JSON válido).
- **FR-010 — Revisão humana deve ter status e trilha auditável.**
- **FR-011 — Separar explicitamente "extraído do documento" de "inferido/derivado pelo sistema".**
- **FR-012 — Anchoring/rastreabilidade sempre que aplicável** — cada campo extraído preserva vínculo com a fonte.

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

- **FR-013 — CLI permanece canônica** — a interface CLI Typer é a porta de entrada operacional e técnica do baseline. Não é descartada nem convertida em interface legada.
- **FR-014 — Front-end como camada humana de acesso** — o front-end é uma **camada futura** de interface de acesso humano sobre o núcleo canônico (runtime + pipeline + contratos de dados). **Não substitui a CLI.**
- **FR-015 — Camada de serviço compartilhada** — CLI e front-end consomem a mesma camada de serviço/orquestração, sem acoplamento direto entre si.
- **FR-016 — Núcleo canônico** — runtime skill-centric, pipeline de processamento e contratos de dados formam o núcleo independente de interface.

#### Formato e Contrato de Dados

- **FR-017 — Schema é lei** — cada skill deve produzir output aderente ao schema aplicável. Output inválido não é consumido downstream.
- **FR-018 — Transformação intermediária formalizada** — quando houver transição entre etapas com necessidades distintas, a transformação deve ser explícita, versionada e validável.
- **FR-019 — Contrato explícito entre etapas** — não se assume que output bruto de uma skill serve automaticamente como contrato universal para todas as etapas seguintes.

#### Performance e Escala

- **FR-020 — Baseline: dezenas a centenas de documentos por execução** — o sistema suporta lotes relevantes de documentos jurídicos como operação padrão.
- **FR-021 — Documentos extensos e heterogêneos** — peças e conjuntos com centenas de páginas são cenário esperado.
- **FR-022 — Caminho para assincronia** — o pipeline opera de forma síncrono por etapa no baseline, mas a arquitetura preserva caminho para processamento em lote, filas, paralelização controlada e futura assincronia.
- **FR-023 — Rastreabilidade inegociável** — desempenho não compromete rastreabilidade, validação e auditabilidade.

#### Gestão de Estado e Erros

- **FR-024 — Estado observável por etapa** — cada etapa deixa estado auditável com insumos, logs e artefatos parciais.
- **FR-025 — Falha registrada com contexto** — erro registra onde ocorreu, com insumos da etapa, logs relevantes e artefatos disponíveis.
- **FR-026 — Checkpoint/resume sobre rollback** — o projeto caminha para suportar retomada controlada de pipeline interrompido, sem obrigar reprocessamento total. Rollback clássico não é o conceito correto para pipeline documental; o prioritário é checkpoint, isolamento da falha e reexecução segura da etapa afetada.

#### Provedor LLM e Fallback

- **FR-027 — Gemini como baseline principal** — Gemini API é o provedor de LLM do baseline operacional.
- **FR-028 — Abstração de cliente preservada** — a interface `LLMClient` é a abstração que isola o provedor concreto.
- **FR-029 — Fallback como requisito arquitetural** — fallback local (llama.cpp) ou alternativo existe como capacidade arquitetural real. A viabilidade do projeto não depende de estabilidade comercial absoluta de um único modelo.
- **FR-030 — Risco operacional formal** — custo, disponibilidade, latência e mudança de política de provedor são tratados como risco operacional do produto.

#### Observabilidade

- **FR-031 — Logs são o mínimo** — registro de execução por etapa, skill, documento e lote via `var/logs/`.
- **FR-032 — Tipos de falha identificáveis** — o sistema permite identificar falhas de dispatch, validação, schema, OCR, chamada LLM e carga.
- **FR-033 — Evolução para métricas e alertas** — métricas, alertas e painéis entram por evolução incremental, especialmente para operação em lote e front-end.
- **FR-034 — Dupla finalidade** — observabilidade serve tanto para operação técnica quanto para auditoria jurídica.

### Implementation Considerations

| Dimensão | Baseline Atual | Evolução Prevista |
|---|---|---|
| Interface | CLI Typer (5 comandos) — canônica | CLI canônica + front-end como camada humana de acesso |
| Pipeline | Síncrono por etapa | Caminho para assincronia, filas, paralelização |
| Estado | Sem checkpoint/resume | Retomada controlada de pipeline interrompido |
| LLM | Gemini API (DummyLLMClient no extractor) | Gemini real + abstração com fallback local |
| Observabilidade | Logs em `var/logs/` | Métricas, alertas, painéis operacionais |
| Contrato de dados | Schemas JSON por skill | Schemas versionados + transformações intermediárias formalizadas |
| Escala | Dezenas a centenas de docs | Lotes maiores com paralelização controlada |
| Skills | 13/15 registradas e operacionais | 15/15 registradas e despacháveis |
| Memória / Eficiência | Mem0, TurboQuant, RLM não implantados | Mem0 + TurboQuant + RLM operacionais (obrigatórios na arquitetura-alvo) |
| Camada de acesso | CLI única | CLI + front-end (camada futura, não substituta) |
