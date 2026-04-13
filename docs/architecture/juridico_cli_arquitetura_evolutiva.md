# Documento de Arquitetura Evolutiva: Jurídico CLI

## 1. Visão Arquitetural Geral

### 1.1. Natureza Brownfield e Evolução Incremental
O projeto **Jurídico CLI** é categorizado estritamente como um projeto brownfield. A evolução arquitetural não reconstrói o sistema do zero, mas parte de um estado-base operacional que hospeda artefatos funcionais. A progressão ocorre de forma incremental e aditiva, preservando a estabilidade do baseline e mapeando claramente o *Baseline Atual*, os *Gaps Reais* e a *Arquitetura-Alvo*.

### 1.2. O Modelo *Skill-Centric* como Unidade Canônica
A arquitetura baseia-se no modelo *Skill-Centric*. Uma skill atua como a unidade canônica de capacidade do sistema. As execuções e consolidações de dados ocorrem dentro do escopo de habilidades validadas, despachadas pelo runtime da plataforma.

### 1.3. Base Normativa: Requisitos FR-001 a FR-034
A modelagem arquitetural atende às especificações do Documento de Requisitos (PRD). Elementos centrais incluem:
* **Trilha de Auditoria (Chain of Custody):** Requisitos de rastreabilidade para mutações e inferências processadas no sistema.
* **Conformidade de Domínio:** Determinações sobre manipulação restrita de dados, cadeia auditável estruturada e observância a schemas jurídicos validados.

---

## 2. Baseline Atual Implantado (As-Is)

> **[ESTADO: BASELINE ATUAL]** Esta camada descreve os componentes operacionais na infraestrutura física atual do repositório.

### 2.1. Organização do Repositório Real e Runtime Vigente
O repositório apresenta uma topologia dividida entre componentes de aplicação (`apps/data-processing/`) e a plataforma fundacional (`platform/skill-runtime/`). O runtime local atual resolve requisições orquestrando I/O em diretórios, acionando o despachante de skills e validando payloads.

### 2.2. A CLI como Fronteira Operacional Canônica
A CLI Typer permanece inalterada como a interface técnica e operacional canônica do baseline, atuando como o elo de execução direta de pipelines e processos em lote no projeto.

### 2.3. Estado das Capacidades (Skills)
O sistema reflete o seguinte estado taxonômico de capacidades:
* **15 skills no repositório:** Existência estrutural de pastas de skills no repositório do projeto.
* **13 skills registradas e operacionais no baseline atual:** Formalizadas no registry de ambiente de baseline.
* **Skills efetivamente validadas:** Distinção explícita no baseline: existir no repositório ou no registry não significa execução validada em pipeline end-to-end; algumas operam sob simulações interinas dependentes de fechamento.

---

## 3. Gaps Reais e Ordem de Tratamento Imediato

> **[ESTADO: GAPS REAIS]** Lacunas identificadas no baseline que atuam como bloqueadores orgânicos.

* **Identificação de mocks:** Mitigação do artefato preenchedor `DummyLLMClient`, ativando integrações por via do GenAI Adapter e de providers efetivos.
* **Registro de skills pendentes:** Equalização do escopo de 15 skills por incorporação no registry e setup completo das lógicas pendentes.
* **Validação E2E base:** Provar o fluxo completo do runtime real (*CLI -> Input -> Skill -> Schema JSON -> Output*) em terminal sem artefatos hardcoded lógicos.

---

## 4. Arquitetura-Alvo (To-Be) e Fronteiras entre Camadas

> **[ESTADO: ARQ-ALVO]** Estado projetado e futuro limitante para garantir que adições tecnológicas respeitem hierarquias duradouras.

### 4.1. Camadas da Arquitetura Topológica
* **Camada de I/O de Dados:** Entrada e extração de payload de arquivos.
* **Camada de Runtime/Core:** Escopo de processamento onde a CLI gerencia as instâncias limitadas das skills para resolução de inferência documental.
* **Camada de Serviços / Orquestração Compartilhada:** Barramento padronizado que unifica os métodos da aplicação a serem chamados internamente.

### 4.2. Fronteira de Interface: CLI vs. Front-end
A separação de papéis na evolução adota restrições inequívocas:
* **Soberania da CLI:** É e deverá continuar exercendo como ferramenta fundamental operacional do baseline técnico.
* **Independência de Camada e Consumo Front-End:** O front-end (futuro) é apenas uma camada voltada à visualização assistida por auditoria humana.
* **Contrato de Consumo:** A CLI e o front-end deverão consumir a mesma camada de orquestração (serviços ou API conectada). O front-end não substitui a CLI operacional e futuramente acessa a orquestração de forma apartada por APIs.

---

## 5. Componentes Estruturais Obrigatórios do Bloco Atual

> **[ESTADO: OBRIGATÓRIOS DO BLOCO ATUAL / PÓS-ESTABILIZAÇÃO DO BASELINE]** Estes módulos integram a arquitetura-alvo obrigatória do projeto e devem ser implantados no bloco atual após a estabilização do baseline, antes da transição para o próximo bloco arquitetural.

### 5.1. Mem0
A camada de **memória persistente / contextual**. O componente integrará a retenção longitudinal de referências jurídicas e metadados contextuais, evitando inferências cegas entre sessões interdependentes de processos extensos.

### 5.2. TurboQuant
O componente de **eficiência e compressão contextual**. Atua no intercâmbio de carga pré-provisão, racionalizando janelas complexas com extrações de alta densidade seletiva antes da entrega aos modelos.

### 5.3. Recursive Logic Model (RLM)
O componente de **raciocínio coordenativo**. O RLM absorverá a coordenação iterativa para contextos documentais maciços, revisões estruturadas e autoaprimoramentos reflexivos de prompt e lógica no sistema de skills.

### 5.4. LLMs Locais
A camada de **execução local validada de modelos**. Sua implantação no bloco atual é obrigatória para verificar viabilidade operacional, compatibilidade com a arquitetura vigente, impacto no runtime e riscos de regressão antes do avanço para o próximo bloco.

---

## 6. Contratos de Dados e Integrações

> **[ESTADO: APLICABILIDADE GERAL (BASELINE & ALVO)]** Padrão normativo de qualidade da I/O no pipeline documental.

### 6.1. Abstração LLM Client
O baseline se fundamenta principalmente no provedor **Gemini**. Conserva-se ativamente a camada de abstração do cliente, limitando a necessidade de grandes quebras; a opção de fallbacks atua dentro desse framework nativamente projetado no baseline para não forçar dependências excessivas.

### 6.2. Contratos de Schema Extrativo
* **O schema é o contrato formal e imutável de saída da skill.** Output sem schema validável é lixo lógico no sistema arquitetado.
* O output bruto (*raw generation*) emitido por uma skill jamais é alocado como contrato universal downstream indiscriminado.
* Quaisquer transformações entre domínios paralelos, processos ou etapas deverão sempre ser explícitas e versionadas sob esquemas documentais limitados e autossuficientes.

### 6.3. Anchoring e Rastreabilidade Baseados em Contrato
A implementação efetiva dos requisitos de rastreabilidade documental (*chain of custody*) e *anchoring* opera orientada à **exigência pontual estipulada pela skill individual e pelo schema aplicável** de retorno, evitando processamento massivo universal indesejado.

---

## 7. Ordem de Implantação Incremental

O framework evolutivo restringe a inclusão e o deploy em transições incrementais e faseadas:

1. **Onda 1 | Estabilização do baseline:** Resoluções de mocking, consolidação do ciclo *Skill-Centric* básico e validação da CLI Typer na extração com schemas.
2. **Onda 2 | Fechamento arquitetural do bloco atual:** Implantação e validação de Mem0, TurboQuant, RLM e LLMs locais sobre a base estabilizada pela Onda 1, com avaliação de compatibilidade, risco e impacto.
3. **Onda 3 | Próximo bloco arquitetural:** Consolidação da camada de acesso, front-end e barramento/API compartilhada, consumindo base operacional orquestrada via interfaces de serviço sem substituir a CLI.

---

## 8. Guardrails, Riscos e Defesas das Entregas

### 8.1. Limites Claros do Baseline
A separação estrutural define formalmente os alvos que permanecem **fora do baseline operacional estrito**:
* A elaboração estrutural da camada de acesso/front-end UI.
* Integrações especulativas precoces para endpoints judiciários (PJe, e-SAJ, Eproc) sem validação prática prévia em fluxos offline do baseline.
* Qualquer expansão que bypassa a ordem incremental definida na seção 7.

**Observação importante:** Mem0, TurboQuant, RLM e LLMs locais não integram o baseline operacional estrito, mas **integram obrigatoriamente o fechamento do bloco atual**. Portanto, não devem ser tratados como backlog remoto ou futuro eventual.

### 8.2. Risco Arquitetural Restritivo & Regras Base
* **Proibição de mistura indevida:** Futuras camadas não podem quebrar dependências essenciais da rotina básica do baseline hoje existente.
* **Permanência da CLI:** Abstrações de front-end não competirão nem subtrairão os acessos, scripts e rotinas acopláveis e acionáveis da CLI original do repositório.
* **Impossibilidade de subtração de alvo:** Ferramentas descritas na seção 5 (Mem0, TurboQuant, RLM e LLMs locais) sob nenhum cenário podem ser reduzidas a funcionalidades opcionais removíveis da arquitetura-alvo.
* **Downstream segregado:** Arquiteturas e interfaces deverão observar interposição de contratos (*fail-fast architecture*), impedindo consumo downstream de outputs de skills mal gerados ou sem schema consolidado.
* **Rastreabilidade segregada:** Garantir os parâmetros judiciais restritivos impostos sobre cadeia limpa, conforme diretrizes do PRD vigente e restrições dominiais operantes.

---

## 9. Critério de Encerramento do Bloco Atual

O bloco atual do `juridico-cli` somente poderá ser considerado arquiteturalmente encerrado após:

1. estabilização do baseline vigente;
2. implantação de Mem0;
3. implantação de TurboQuant;
4. implantação de RLM;
5. execução local validada de LLMs no ambiente do projeto;
6. avaliação explícita de compatibilidade, risco, impacto e regressão desses componentes sobre a base já homologada.

### Interpretação correta do estágio
A leitura correta do estágio é:

- **baseline atual:** pode estar parcialmente homologado e operacional;
- **bloco atual:** permanece aberto até o fechamento da Onda 2;
- **próximo bloco arquitetural:** não deve ser iniciado antes da verificação explícita dos itens obrigatórios definidos neste documento.

### Regra de governança
Mem0, TurboQuant, RLM e LLMs locais:
- não pertencem ao grupo de “futuro eventual”;
- não devem ser rebaixados a backlog genérico;
- devem ser tratados como **pendências arquiteturais obrigatórias de fechamento do bloco atual**.
