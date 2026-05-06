# juridico-cli — Documento Mestre de Arquitetura

## Status

Canônico para arquitetura do projeto.

## Finalidade

Este documento define a **arquitetura-alvo** do `juridico-cli`.

Seu papel é descrever:

- como o projeto deve ser estruturado;
- quais camadas compõem o sistema;
- quais componentes são obrigatórios no desenho final;
- como as responsabilidades se separam.

Este documento **não** deve conter:

- inventário do que já está implantado;
- backlog;
- gaps;
- próximos passos;
- validações temporárias;
- instruções operacionais para executores.

Esses assuntos pertencem a documentos separados.

---

## 1. Visão arquitetural

O `juridico-cli` é um monorepo de processamento documental e jurídico, organizado em torno de uma arquitetura **skill-centric**, com separação explícita entre:

- módulos funcionais;
- habilidades canônicas;
- runtime de execução;
- memória e contexto;
- eficiência contextual;
- inferência recursiva;
- infraestrutura local.

A unidade canônica de capacidade do sistema é a **skill**.

O projeto é estruturado por:

- módulos funcionais em `apps/`;
- habilidades canônicas em `platform/skills/`;
- runtime canônico em `platform/skill-runtime/`;
- componentes compartilhados em `packages/`;
- infraestrutura local em `infra/`;
- dados operacionais em `var/`.

---

## 2. Princípios arquiteturais

### 2.1. Skill como unidade canônica

Toda capacidade canônica do sistema deve ser modelada como skill.

### 2.2. Separação entre módulo funcional e skill

`apps/` define o fluxo funcional por domínio.  
`platform/skills/` define capacidades reutilizáveis.  
`platform/skill-runtime/` executa e resolve essas capacidades.

### 2.3. Runtime centralizado

A execução das skills deve ocorrer pelo runtime canônico do projeto.

### 2.4. Base documental genérica

O pipeline documental base deve ser genérico e agnóstico de domínio.

### 2.5. Especialização jurídica em camada superior

A interpretação, segmentação e curadoria jurídica devem ser construídas acima da base documental genérica.

### 2.6. Memória, eficiência e inferência fazem parte do desenho-alvo

Mem0, TurboQuant e RLM compõem a arquitetura-alvo do projeto e não devem ser tratados como extensões opcionais.

### 2.7. Infraestrutura local obrigatória

Docker e serviços locais fazem parte do desenho arquitetural do projeto.

### 2.8. Legado não governa a arquitetura

Estruturas legadas podem permanecer preservadas, mas não definem o caminho canônico.

---

## 3. Estrutura lógica do repositório

```text
juridico-cli/
├── apps/
├── platform/
│   ├── skill-runtime/
│   └── skills/
├── packages/
├── var/
├── infra/
├── docs/
├── scripts/
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 4. Separação de responsabilidades

### `apps/`

Camada de módulos funcionais do projeto.

Responsável por:

- entrada operacional dos fluxos;
- composição funcional do processamento;
- integração com runtime, validação e persistência;
- exposição de CLIs e fluxos por domínio.

### `platform/skills/`

Camada canônica de habilidades.

Responsável por:

- representar capacidades reutilizáveis do sistema;
- encapsular instruções, ativos, referências e scripts;
- servir como unidade canônica de execução lógica.

### `platform/skill-runtime/`

Runtime canônico de skills.

Responsável por:

- resolver skills;
- carregar bundles;
- selecionar perfis de execução;
- despachar chamadas;
- manter registries de skill e LLM.

### `packages/`

Camada de componentes compartilhados.

Responsável por:

- utilidades compartilhadas;
- contratos reutilizáveis;
- abstrações comuns;
- código transversal.

### `var/`

Camada operacional de dados de runtime.

Responsável por:

- input;
- staging;
- output;
- logs;
- artefatos;
- cache;
- backups.

### `infra/`

Camada de infraestrutura local.

Responsável por:

- Docker;
- Qdrant;
- configuração de ambiente;
- serviços locais de apoio à execução.

---

## 5. Módulos funcionais implantáveis

O `juridico-cli` é composto por três módulos funcionais principais, projetados para
execução e implantação separada, preservando contratos compartilhados por schemas,
runtime de skills, infraestrutura local e componentes comuns.

### 5.1. `apps/document-processing/`

Módulo responsável pelo tratamento documental genérico.

Responsabilidades:

- ingestão de arquivos;
- conversão de PDF/DOCX/TXT/HTML para Markdown;
- OCR e fallback quando necessário;
- limpeza e normalização;
- criação de anchors;
- geração de metadados técnicos;
- validação estrutural;
- persistência em formato tratado.

Este módulo não executa interpretação jurídica profunda.

### 5.2. `apps/process-processing/`

Módulo responsável pelo tratamento do processo jurídico.

Responsabilidades:

- composição do processo;
- identificação e classificação de peças;
- extração jurídica estruturada;
- partes;
- fatos;
- eventos;
- provas;
- obrigações;
- prazos;
- linha do tempo;
- síntese processual;
- preparação de dados para raciocínio jurídico.

Este módulo consome documentos previamente tratados pelo `document-processing`.

### 5.3. `apps/legal-knowledge/`

Módulo responsável pela formação e manutenção da base jurídica.

Responsabilidades:

- ingestão de jurisprudência;
- ingestão de legislação;
- ingestão de doutrina;
- ingestão de fontes fornecidas pelo operador;
- reaproveitamento de bases já tratadas;
- normalização;
- indexação;
- persistência em banco vetorial, banco relacional ou formato tratado;
- recuperação de insumos jurídicos para uso pelos demais módulos.

Este módulo pode consumir fontes externas ou arquivos locais fornecidos pelo operador.

### 5.4. Contrato entre módulos

Os módulos não devem depender de implementação interna uns dos outros.

A comunicação entre módulos deve ocorrer por:

- arquivos tratados;
- JSONs versionados;
- schemas compartilhados;
- banco de dados;
- banco vetorial;
- contratos explícitos de entrada e saída.

Cada módulo deve possuir CLI própria e poder ser executado isoladamente.

### 5.5. Geração estruturada por schemas

O projeto deve adotar uma camada de geração estruturada baseada em schemas para garantir que saídas produzidas por LLMs respeitem contratos explícitos, JSONs versionados e formatos verificáveis.

O Outlines compõe a arquitetura-alvo como ferramenta de apoio à geração estruturada, restrição de saída e conformidade com schemas.

A função arquitetural do Outlines é:

- apoiar geração de JSONs compatíveis com schemas definidos;
- reduzir saídas livres ou malformadas de LLMs;
- reforçar contratos entre módulos funcionais;
- apoiar validação de outputs produzidos por skills;
- servir como camada auxiliar para extrações estruturadas.

A versão, modo de instalação, integração operacional e validação prática do Outlines pertencem à matriz de versões, ao runbook ou a uma change OpenSpec específica.

### Regra arquitetural

Schemas continuam sendo os contratos canônicos do projeto.

Outlines não substitui os schemas, o runtime de skills nem os validadores do sistema. Ele atua como ferramenta de geração estruturada orientada por schemas.

---

## 6. Runtime canônico

O runtime oficial do projeto é:

`platform/skill-runtime/`

### Componentes canônicos

#### `skill_dispatcher.py`

Ponto canônico de despacho de skills.

#### `bundle_loader.py`

Carregador interno dos bundles de skills.

#### `skill_registry.yaml`

Registro canônico das skills do sistema.

#### `llm_registry.yaml`

llm_profiles:
gemini_api:
provider: gemini
status: validated

lm_studio_local:
provider: openai_compatible
runtime: lm_studio
base_url_env: LOCAL_LLM_BASE_URL
api_key_env: LOCAL_LLM_API_KEY
model_env: LOCAL_LLM_MODEL
status: preferred_local_validation

llama_cpp_local:
provider: openai_compatible
runtime: llama_cpp
base_url_env: LLAMA_CPP_BASE_URL
api_key_env: LLAMA_CPP_API_KEY
model_env: LLAMA_CPP_MODEL
status: pending_stability_validation

LLM local via endpoint OpenAI-compatible,
com LM Studio como runtime local preferencial no estágio atual
e llama.cpp como alvo alternativo pendente de validação.
Registro canônico de perfis, classes e execução de LLMs.

### Regras do runtime

- skill nova não integra a arquitetura apenas por existir no disco;
- skill deve ser resolvível pelo runtime;
- a resolução canônica deve passar pelo registry;
- arquiteturas paralelas de loading e despacho não são o caminho oficial.

---

## 7. Skills canônicas

As skills do projeto residem em:

`platform/skills/`

Cada skill representa uma capacidade específica e reutilizável.

Uma skill pode conter:

- `SKILL.md`;
- `assets/`;
- `references/`;
- `scripts/`.

### Regra arquitetural

A skill é a unidade canônica de capacidade, mas não substitui o conceito de módulo funcional em `apps/`.

Módulo funcional e skill possuem papéis distintos e complementares.

---

## 8. Pipeline documental base

### `pdf-to-md`

Skill responsável pela conversão de PDF para Markdown bruto.

A conversão deve operar em dois modos:

1. **PDF legível / digital**
   - extração textual direta;
   - preservação de páginas;
   - geração de anchors;
   - baixo custo computacional.

2. **PDF ilegível, escaneado ou com baixa extração textual**
   - OCR obrigatório via PaddleOCR;
   - detecção de páginas que exigem OCR;
   - extração textual por imagem;
   - preservação de referência de página;
   - geração de Markdown bruto compatível com o restante do pipeline.

O PaddleOCR passa a ser o mecanismo canônico de OCR do pipeline documental, substituindo o fallback anterior para PDFs ilegíveis ou escaneados.
O objetivo da skill `pdf-to-md` não é interpretar juridicamente o documento, mas entregar Markdown bruto rastreável para as etapas posteriores.
Após revisão arquitetural, ficou definido que o PaddleOCR substituirá o fallback OCR anterior para PDFs ilegíveis, escaneados ou com baixa extração textual.
A skill `pdf-to-md` permanece como interface canônica do pipeline documental, mas sua implementação deverá incorporar o PaddleOCR como mecanismo OCR obrigatório quando a extração textual direta não for suficiente.

## 9. Camada jurídica especializada

A especialização jurídica não pertence ao pipeline documental base.

Ela deve ser construída como camada superior, posterior ao pipeline genérico, e pode incluir:

- classificação de tipo de peça;
- segmentação por documento lógico;
- identificação de conteúdo descartável;
- avaliação de relevância processual;
- frontmatter jurídico enriquecido;
- composição por processo.

### Regra arquitetural

A camada jurídica especializada deve usar a base documental genérica como fundamento, e não substituir sua função.

---

## 10. Camada de memória

A arquitetura-alvo do projeto inclui uma camada obrigatória de memória.

### Mem0

Mem0 compõe a camada de memória persistente e episódica do sistema.

Função arquitetural:

- manter memória entre execuções;
- persistir experiências, contexto e informação útil de longo prazo;
- apoiar continuidade operacional e jurídica;
- servir como memória complementar ao fluxo imediato de execução.

### Regra arquitetural

Memória persistente faz parte da arquitetura-alvo e deve ser tratada como componente estrutural do projeto.

---

## 11. Camada de eficiência contextual

A arquitetura-alvo do projeto inclui uma camada obrigatória de eficiência contextual.

### TurboQuant

TurboQuant compõe a camada de compressão e eficiência de representação contextual.

Função arquitetural:

- reduzir custo de representação de contexto e vetores;
- permitir uso mais eficiente de memória e recursos locais;
- apoiar processamento de contexto extenso com menor pressão computacional;
- servir como componente estrutural de eficiência do sistema.

### Regra arquitetural

TurboQuant faz parte do desenho final do projeto e não deve ser tratado como acessório opcional.

---

## 12. Camada de inferência recursiva

A arquitetura-alvo do projeto inclui uma camada obrigatória de inferência recursiva.

### RLM

RLM compõe a camada de inferência/execução recursiva do sistema.

Função arquitetural:

- lidar com contexto extenso;
- decompor raciocínio em etapas intermediárias;
- permitir processamento progressivo de documentos longos e estruturas complexas;
- apoiar fluxos jurídicos e documentais que excedam uma leitura linear simples.

### Regra arquitetural

RLM integra o projeto-alvo como componente estrutural de raciocínio e execução, ainda que sua implantação ocorra progressivamente.

---

## 13. Stack oficial e infraestrutura local

### Modelos e execução

A arquitetura do projeto adota execução híbrida de LLMs:

- Gemini via API;
- LLMs locais por meio de endpoint compatível com OpenAI;
- camada de abstração para alternância entre runtimes locais;
- suporte a LM Studio, llama.cpp ou runtime equivalente compatível.

A decisão arquitetural não depende de uma ferramenta única de execução local. O requisito canônico é manter uma camada de abstração compatível com provedores locais, permitindo alternar entre runtimes sem alterar a lógica das skills.

O Documento Mestre não define qual runtime local está ativo em cada momento operacional. Essa decisão pertence ao runbook operacional ou ao documento de estado real implantado.

### Infraestrutura local

A infraestrutura local do projeto pode incluir:

- Docker Desktop;
- Qdrant local;
- runtimes locais de LLM expostos por API compatível com OpenAI;
- serviços auxiliares de apoio à execução.

### Papel de Docker

Docker compõe a infraestrutura-alvo do projeto para serviços locais, isolamento de componentes e padronização operacional.

Docker não é requisito obrigatório para executar LLM local em todas as fases do projeto. Quando um runtime local externo, como LM Studio, estiver em uso, ele pode substituir provisoriamente a execução de LLM via container, sem alterar a arquitetura skill-centric.

### Papel de Qdrant

Qdrant compõe a infraestrutura local de busca vetorial e recuperação.

### Regra arquitetural

A arquitetura deve preservar compatibilidade com execução local e serviços locais, independentemente de o runtime de LLM estar em Docker, LM Studio, llama.cpp ou runtime equivalente.

Docker permanece como componente da infraestrutura-alvo, mas não define sozinho a forma de execução local de LLMs.

---

## 14. Convenções estruturais

### Convenção de responsabilidade

- `apps/` → módulos funcionais
- `platform/skills/` → habilidades canônicas
- `platform/skill-runtime/` → execução e roteamento
- `packages/` → compartilhamento
- `var/` → dados operacionais
- `infra/` → infraestrutura local

### Convenção de evolução

- novas capacidades devem nascer como skill ou ser compatíveis com a camada de skills;
- especializações de domínio devem ser tratadas acima da base documental;
- componentes estruturais obrigatórios devem ser preservados no desenho, mesmo com implantação progressiva;
- componentes legados não definem o caminho canônico.

---

## 15. Legado

São considerados fora do caminho canônico vigente:

- `agents/` na raiz;
- partes antigas de `pipelines/`;
- outras estruturas que reintroduzam leitura agent-centric como centro arquitetural.

### Regra arquitetural

Legado pode existir como material preservado, mas não governa a arquitetura atual do projeto.

---

## 16. Limites deste documento

Este documento não descreve:

- o que já está implantado;
- o que ainda falta;
- o que está pendente;
- prioridades;
- tarefas de execução;
- relatórios de gap;
- instruções para Claude, Qwen ou outros executores.

Esses assuntos pertencem a documentos separados.

---

## 17. Decisão final

A arquitetura do `juridico-cli` é modular por domínio funcional e centrada em skills.

O projeto deve ser interpretado a partir de:

- `apps/` como módulos funcionais;
- `platform/skills/` como camada canônica de capacidades;
- `platform/skill-runtime/` como runtime oficial de execução e roteamento;
- pipeline documental base genérico;
- camada jurídica especializada construída acima dessa base;
- Mem0 como camada obrigatória de memória;
- TurboQuant como camada obrigatória de eficiência contextual;
- RLM como camada obrigatória de inferência recursiva;
- Docker e serviços locais como infraestrutura obrigatória;
- legado explicitamente separado do caminho arquitetural vigente.

---

## 18. Componentes estruturais obrigatórios da arquitetura-alvo

Mem0, TurboQuant, RLM e a execução local de LLMs compõem o desenho-alvo obrigatório do `juridico-cli`.

Esses componentes não devem ser tratados como capacidades opcionais, extensões periféricas ou adições descartáveis do projeto.

### Papel de cada componente na arquitetura-alvo

- **Mem0**: camada de memória contextual e persistência de conhecimento operacional.
- **TurboQuant**: camada de eficiência e viabilidade operacional para processamento contextual e uso de modelos locais.
- **RLM**: camada de inferência recursiva, refinamento e coordenação de raciocínio.
- **LLMs locais**: capacidade estrutural de execução local, necessária para compor a arquitetura híbrida do projeto ao lado do uso de provedores via API.

### Regra arquitetural

No documento mestre, esses componentes devem ser lidos exclusivamente como partes obrigatórias da arquitetura-alvo.

Cronograma, ordem de implantação, fechamento de bloco, validação operacional, prioridades e estado real de implementação pertencem a documentos separados e não devem ser definidos aqui.
