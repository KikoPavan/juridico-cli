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

## 5. Módulos funcionais

### 5.1. `apps/data-processing/`

Módulo funcional documental do projeto.

Função arquitetural:

- receber e processar fluxos documentais;
- coordenar conversão, limpeza, análise, extração, validação e carga;
- operar como porta funcional do pipeline documental;
- consumir o runtime canônico para resolver skills aplicáveis.

### 5.2. `apps/legal-research/`

Módulo funcional jurídico de pesquisa.

Função arquitetural:

- pesquisa jurisprudencial;
- pesquisa legislativa;
- pesquisa doutrinária;
- recuperação de insumos jurídicos.

### 5.3. `apps/legal-core/`

Módulo funcional jurídico de raciocínio e produção.

Função arquitetural:

- FIRAC;
- compliance;
- estratégia;
- síntese jurídica;
- pareceres;
- petições.

### 5.4. `apps/orchestrator-cli/`

Módulo funcional de coordenação operacional.

Função arquitetural:

- coordenar fluxos entre módulos;
- expor entrada operacional de alto nível;
- integrar fluxos sem concentrar a lógica documental nem a lógica jurídica.

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

O pipeline documental base do projeto é composto por três habilidades principais:

1. `pdf-to-md`
2. `md-clean-markdown`
3. `md-frontmatter-yaml`

### Papel do pipeline base

#### `pdf-to-md`

Converte PDF em Markdown bruto.

#### `md-clean-markdown`

Normaliza e limpa o Markdown bruto.

#### `md-frontmatter-yaml`

Adiciona frontmatter YAML genérico ao documento processado.

### Regra arquitetural

Esse pipeline é:

- genérico;
- documental;
- agnóstico de domínio;
- reutilizável para diferentes tipos de documento.

Ele não deve nascer especializado em processo judicial.

---

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

- Gemini via API
- llama.cpp local

### Infraestrutura local

- Docker Desktop
- Qdrant local

### Papel de Docker

Docker compõe a infraestrutura arquitetural obrigatória do projeto.

Função arquitetural:

- hospedar serviços locais;
- padronizar execução;
- isolar componentes;
- apoiar integração de LLM local, vector store e serviços auxiliares.

### Papel de Qdrant

Qdrant compõe a infraestrutura local de busca vetorial e recuperação.

### Regra arquitetural

Docker e serviços locais não são opcionais no desenho-alvo do projeto.

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

```

O próximo ajuste certo é fazer o **estado real implantado** refletir essa arquitetura, sem contaminar este documento.
```
