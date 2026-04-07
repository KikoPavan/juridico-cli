# Tarefa — Levantamento do Estado Real Implantado do `juridico-cli`

## Status
Tarefa pontual para executor.

## Repositório base
`~/devops/juridico-cli`

## Objetivo
Levantar o estado real implantado do projeto `juridico-cli` e comparar esse estado com a arquitetura vigente, sem alterar código nem estrutura do repositório.

O trabalho deve responder com precisão:

1. o que está realmente implantado no repositório;
2. o que está implantado, mas sem validação clara;
3. o que está apenas previsto;
4. o que é legado congelado ou fora do caminho canônico;
5. quais divergências existem entre a arquitetura vigente e o estado real do disco.

---

## Fontes principais obrigatórias
Ler primeiro:

1. `~/devops/juridico-cli/QWEN.md`
2. `~/devops/juridico-cli/docs/architecture/juridico_cli_documento_mestre.md`
3. `~/devops/juridico-cli/docs/runbooks/runbook_operacional_minimo.md`

Se algum desses arquivos não existir, registrar isso explicitamente no relatório.

### Fonte histórica de fallback
Usar apenas se necessário e sem tratá-la como verdade principal:

- `~/devops/juridico-cli/docs/archive/juridico-cli/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

## Leitura obrigatória do repositório real
Inspecionar diretamente os seguintes caminhos:

- `~/devops/juridico-cli/apps/`
- `~/devops/juridico-cli/platform/`
- `~/devops/juridico-cli/packages/`
- `~/devops/juridico-cli/infra/`
- `~/devops/juridico-cli/var/`
- `~/devops/juridico-cli/scripts/`
- `~/devops/juridico-cli/tests/`
- `~/devops/juridico-cli/pyproject.toml`
- `~/devops/juridico-cli/README.md`

### Leitura histórica opcional
Somente se necessário para esclarecer divergência:

- `~/devops/juridico-cli/docs/archive/juridico-cli/`

---

## Restrições
- não alterar código;
- não alterar estrutura do repositório;
- não mover arquivos;
- não criar nova arquitetura;
- não assumir que algo está implantado sem evidência no disco;
- não usar documento histórico como verdade principal;
- não declarar algo como validado sem evidência objetiva;
- usar caminhos exatos do repositório como evidência.

---

## Saídas obrigatórias

### 1. Relatório principal
Criar o arquivo:

`~/devops/juridico-cli/docs/architecture/juridico_cli_estado_real_implantado.md`

#### Conteúdo obrigatório
- resumo executivo;
- itens implantados e validados;
- itens implantados, mas sem validação clara;
- itens previstos, mas não implantados;
- itens legados ou fora do caminho canônico;
- divergências entre o documento mestre e o estado real;
- evidências com caminhos exatos.

---

### 2. Relatório de gaps
Criar o arquivo:

`~/devops/juridico-cli/docs/architecture/juridico_cli_gaps_e_proximo_passo.md`

#### Conteúdo obrigatório
- gaps reais;
- impacto de cada gap;
- prioridade;
- próximo passo recomendado;
- foco no que falta para manter o projeto alinhado ao modelo skill-centric.

---

## Critério de qualidade
A análise deve ser:

- objetiva;
- curta;
- sem especulação;
- baseada no estado real do repositório;
- consistente com `QWEN.md` e com o documento mestre;
- clara na distinção entre:
  - implantado;
  - implantado parcialmente;
  - previsto;
  - legado.

---

## Forma de validação
Ao final da execução, mostrar:

1. arquivos lidos;
2. arquivos produzidos;
3. resumo curto do que está implantado;
4. resumo curto do que falta.

---

## Observação importante
Esta tarefa é pontual.

Ela não altera o papel do `QWEN.md`, que continua sendo apenas contexto permanente do executor.
