# Tarefa — Validação da Nova Esteira Jurídica Fora do Pipeline

## Status
Tarefa pontual para executor.

## Repositório base
`~/devops/juridico-cli`

## Objetivo
Validar e amadurecer a nova esteira jurídica fora do pipeline executável, sem alterar o `apps/data-processing/` e sem integrar a nova esteira ao fluxo operacional neste momento.

O trabalho deve responder com precisão:

1. se `segmentador-juridico` produz Envelope de Processo válido;
2. se `curador-relevancia` produz Envelope Curado válido;
3. se `yaml-normalizador-juridico` produz `.md` com frontmatter YAML válido por peça;
4. se a cadeia completa funciona fora do pipeline executável;
5. quais inconsistências ainda impedem considerar a esteira madura para futura integração.

---

## Fontes principais obrigatórias
Ler primeiro:

1. `~/devops/juridico-cli/QWEN.md`
2. `~/devops/juridico-cli/docs/architecture/juridico_cli_arquitetura_evolutiva.md`
3. `~/devops/juridico-cli/docs/architecture/juridico_cli_estado_real_consolidado.md`
4. `~/devops/juridico-cli/_bmad-output/implementation-artifacts/implementation-state.md`
5. `~/devops/juridico-cli/_bmad-output/project-context.md`

Se algum desses arquivos não existir, registrar isso explicitamente no relatório.

### Fonte complementar
Usar apenas como apoio, sem tratá-la como fonte única de verdade:

- `~/devops/juridico-cli/docs/architecture/juridico_cli_documento_mestre.md`

---

## Leitura obrigatória das skills
Inspecionar diretamente os seguintes caminhos:

- `~/devops/juridico-cli/platform/skills/segmentador-juridico/`
- `~/devops/juridico-cli/platform/skills/curador-relevancia/`
- `~/devops/juridico-cli/platform/skills/yaml-normalizador-juridico/`
- `~/devops/juridico-cli/platform/skill-runtime/skill_registry.yaml`
- `~/devops/juridico-cli/platform/skill-runtime/llm_registry.yaml`

### Leitura opcional de apoio
Somente se necessário para conferir compatibilidade futura, sem alterar nada:

- `~/devops/juridico-cli/apps/data-processing/`
- `~/devops/juridico-cli/docs/runbooks/runbook_operacional_minimo.md`

---

## Escopo operacional desta tarefa

### Etapa 1 — Corrigir pendência residual
Corrigir o arquivo:

`~/devops/juridico-cli/platform/skills/yaml-normalizador-juridico/references/example_output.md`

Objetivo:
- remover enums legados;
- alinhar o exemplo ao contrato/schema canônico;
- eliminar a pendência residual já conhecida.

### Etapa 2 — Validar `segmentador-juridico`
Executar a skill isoladamente com Markdown limpo real como entrada.

Validar:
- aderência ao schema de saída;
- consistência do Envelope de Processo `{metadata, pecas[]}`;
- ausência de campos incompatíveis com o contrato canônico.

### Etapa 3 — Validar `curador-relevancia`
Executar a skill isoladamente usando o envelope produzido pelo segmentador.

Validar:
- aderência ao schema de saída;
- consistência do Envelope Curado;
- coerência dos campos curatoriais por peça;
- comportamento dos modos suportados, quando aplicável.

### Etapa 4 — Validar `yaml-normalizador-juridico`
Executar a skill isoladamente usando peças curadas individuais.

Validar:
- aderência ao schema correspondente;
- geração correta de `.md` com frontmatter YAML;
- presença dos campos obrigatórios;
- consistência entre conteúdo da peça e metadados gerados.

### Etapa 5 — Validar a cadeia ponta a ponta fora do pipeline
Executar, fora do `apps/data-processing/`, o fluxo:

`Markdown limpo -> segmentador-juridico -> curador-relevancia -> yaml-normalizador-juridico`

Validar cada artefato intermediário e registrar onde houver quebra, inconsistência ou ambiguidade contratual.

---

## Restrições
- não alterar `apps/data-processing/`;
- não alterar `pipeline_runner.py`;
- não alterar `stage_router.py`;
- não alterar `cli.py`;
- não integrar a nova esteira ao pipeline executável;
- não rodar `bmad-sprint-planning`;
- não criar `sprint-status.yaml`;
- não tratar hipótese como fato confirmado;
- não declarar algo como validado sem evidência objetiva;
- usar caminhos exatos do repositório como evidência.

---

## Saídas obrigatórias

### 1. Relatório principal
Criar o arquivo:

`~/devops/juridico-cli/docs/qwen_tasks/relatorio_validacao_esteira_juridica.md`

#### Conteúdo obrigatório
- resumo executivo;
- arquivos lidos;
- arquivos alterados;
- resultado da validação do `segmentador-juridico`;
- resultado da validação do `curador-relevancia`;
- resultado da validação do `yaml-normalizador-juridico`;
- resultado da cadeia completa fora do pipeline;
- inconsistências encontradas;
- evidências com caminhos exatos.

### 2. Diagnóstico objetivo
Ao final, informar claramente:
- o que já está maduro;
- o que ainda não está maduro;
- o que impede futura integração;
- se o contrato entre as 3 skills está estável ou ainda não.

---

## Critério de qualidade
A análise deve ser:

- objetiva;
- curta;
- sem especulação;
- baseada em evidência real;
- consistente com `QWEN.md` e com os documentos canônicos;
- clara na distinção entre:
  - validado;
  - parcialmente validado;
  - inconsistente;
  - não confirmado.

---

## Forma de validação
Ao final da execução, mostrar:

1. arquivos lidos;
2. arquivos alterados;
3. quais validações passaram;
4. quais validações falharam;
5. resumo curto do que falta para considerar a esteira madura.

---

## Observação importante
Esta tarefa é pontual.

Ela não altera o papel do `QWEN.md`, que continua sendo apenas contexto permanente do executor.

Ela também não autoriza alteração no pipeline executável.
A integração com `apps/data-processing/` só poderá ser discutida depois que esta esteira estiver estável fora do pipeline.
