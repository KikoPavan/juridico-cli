
### `docs/qwen_tasks/task_atual.md`

```md
# Tarefa Atual — Validação da Nova Esteira Jurídica Fora do Pipeline

## Status
Tarefa temporária vigente.

## Objetivo
Amadurecer e validar a nova esteira jurídica fora do pipeline executável, até que as extrações, envelopes e conversões JSON estejam consistentes e confiáveis.

## Escopo atual
Trabalhar somente nas 3 skills abaixo, fora do `apps/data-processing/`:

- `platform/skills/segmentador-juridico/`
- `platform/skills/curador-relevancia/`
- `platform/skills/yaml-normalizador-juridico/`

## O que deve ser considerado confirmado
- O baseline do projeto já foi aceito.
- As 3 skills novas já foram configuradas e ajustadas contratualmente.
- `segmentador-juridico` e `curador-relevancia` operam sobre envelope `{metadata, pecas[]}`.
- `yaml-normalizador-juridico` recebe peça curada individual, não o envelope inteiro.
- Existe pendência residual em:
  `platform/skills/yaml-normalizador-juridico/references/example_output.md`

## Tarefa operacional atual

### 1. Corrigir pendência residual
Corrigir `platform/skills/yaml-normalizador-juridico/references/example_output.md` para remover enums legados e alinhar o exemplo ao contrato/schema canônico.

### 2. Validar `segmentador-juridico`
- Usar Markdown limpo real como entrada.
- Executar a skill isoladamente.
- Validar a saída contra o schema correspondente.
- Confirmar consistência do Envelope de Processo `{metadata, pecas[]}`.

### 3. Validar `curador-relevancia`
- Usar como entrada o envelope gerado pelo segmentador.
- Executar a skill isoladamente.
- Validar a saída contra o schema correspondente.
- Confirmar consistência do Envelope Curado.

### 4. Validar `yaml-normalizador-juridico`
- Usar peças curadas individuais como entrada.
- Executar a skill isoladamente.
- Validar o `.md` gerado e o frontmatter YAML.
- Confirmar aderência ao schema correspondente.

### 5. Validar a cadeia fora do pipeline
Executar o fluxo fora do `apps/data-processing/`:

`Markdown limpo -> segmentador-juridico -> curador-relevancia -> yaml-normalizador-juridico`

Validar cada artefato intermediário.

### 6. Critério de maturidade
Só considerar a esteira madura quando:
- os 3 estágios produzirem saídas válidas;
- os envelopes estiverem estáveis;
- a conversão JSON estiver consistente;
- os resultados forem repetíveis.

## O que não fazer agora
- não alterar `apps/data-processing/`;
- não alterar `pipeline_runner.py`;
- não alterar `stage_router.py`;
- não alterar `cli.py`;
- não implementar integração da nova esteira no pipeline executável;
- não rodar `bmad-sprint-planning`;
- não criar `sprint-status.yaml`.

## Saída esperada de qualquer executor
Ao final de cada rodada de trabalho, entregar:
- o que foi testado;
- quais arquivos foram lidos ou alterados;
- quais validações passaram;
- quais inconsistências restam;
- se o contrato entre as 3 skills está maduro ou não.

## Próximo passo após esta tarefa
Somente depois de a esteira estar redonda fora do pipeline:
- produzir plano técnico final de integração;
- e só então avaliar alteração controlada no `apps/data-processing/`.
