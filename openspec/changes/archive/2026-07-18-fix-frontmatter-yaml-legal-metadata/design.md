## Context

`apply_frontmatter.py` detecta `title` via primeiro H1 do corpo (`_detect_title`)
e `author` via rótulo explícito (`_detect_author`, regex `Responsável:` /
`Autor:` / etc.). Essas heurísticas são genéricas e agnósticas de domínio,
o que é correto para documentos comuns, mas falha em peças jurídicas
convertidas de PDF: a conversão frequentemente produz um H1 espúrio a partir
de uma linha de texto corrido (ex.: descrição da ação judicial quebrada em
uma linha `# PROCEDIMENTO COMUM (...)`), e o nome da parte apresentante não
segue o padrão de rótulo (`Nome:`), aparecendo em prosa no início do corpo
(ex.: `BANCO DO BRASIL S.A., instituição financeira ..., vem ... apresentar`).

O `document_type` já é passado explicitamente via `--doc-type` (não é
inferido pela skill). O caso real usa `document_type: contestacao_processo`.

## Goals / Non-Goals

**Goals:**
- Melhorar a qualidade de `title` e `author` para peças de contestação sem
  usar LLM, mantendo as heurísticas conservadoras e determinísticas.
- Preservar 100% de compatibilidade com o comportamento atual para
  documentos que não são peças jurídicas reconhecidas (heurísticas novas só
  atuam quando as condições específicas são satisfeitas; caso contrário,
  cai no fallback existente).
- Manter body do Markdown intocado (garantia já testada).

**Non-Goals:**
- Não implementar classificação de `document_type` (continua vindo de
  `--doc-type` ou dos locators judiciais).
- Não cobrir todos os tipos de peça processual — apenas o padrão necessário
  para `contestacao_processo` no caso real, com estrutura extensível para
  tipos futuros.
- Não alterar `pdf-to-md`, `md-clean-markdown`, OCR ou integração
  Gemini/JSON.

## Decisions

### Decisão 1 — Title: prioridade de "linha de rótulo de peça" sobre H1

Quando `document_type` começar com `contestacao_processo` (comparação
literal com o valor passado via `--doc-type`), procurar nas primeiras ~40
linhas do corpo por uma linha isolada cujo conteúdo (após strip de
marcadores de página/locator e espaços) seja exatamente `CONTESTAÇÃO`
(case-sensitive, maiúsculas — é assim que a peça se autodenomina no
documento). Se encontrada, essa linha vira `title` com método
`legal_doc_type_line`, e a detecção de H1 genérica (`_detect_title`) não é
usada para este arquivo.

Se a linha explícita não existir, cai no comportamento atual (H1 genérico,
podendo resultar em `null` ou em heading espúrio — sem regressão em relação
a hoje).

**Alternativas consideradas:**
- Heurística "H1 mais curto que N caracteres": rejeitada por ser frágil e
  não verificável de forma determinística (o limite N seria arbitrário).
- Usar LLM para classificar heading correto: rejeitado por regra explícita
  do usuário (não usar LLM nesta skill).

### Decisão 2 — Author: padrão de abertura de petição brasileira

Quando não houver rótulo explícito (`_AUTHOR_LABELS`) nem `user` extraído de
locator judicial, buscar nas primeiras ~30 linhas do corpo (mesmo orçamento
já usado por `_detect_author` para rótulos explícitos — o caso real mostra
a parte identificada após um bloco de cabeçalho/endereço, na linha 20, e a
cláusula `vem ... apresentar` nas linhas seguintes) por um padrão de
abertura de petição:

```
^([A-ZÀ-Ú][A-ZÀ-Ú0-9À-Ü.\-\s]{2,80}?),\s
```

isto é, uma sequência de palavras em caixa alta (permitindo sufixos
societários como `S.A.`, `LTDA`, `EIRELI`, `ME`) no início de uma linha,
seguida de vírgula — condicionada a essa mesma linha (ou uma das duas
linhas seguintes) conter posteriormente o verbo de protocolo `vem` seguido,
em alguma das próximas linhas, de `apresentar`. Essa combinação (nome em
caixa alta + vírgula no início + `vem ... apresentar` próximo) é o padrão
estrutural clássico de qualificação de parte em petições brasileiras e não
depende do nome específico do banco.

Se o padrão não for encontrado, `author` permanece `null` (comportamento
atual, sem regressão).

**Alternativas consideradas:**
- Lista hardcoded de nomes de bancos/empresas conhecidas (`BANCO DO BRASIL
  S.A.`, etc.): rejeitada — não generaliza e viola o princípio de
  detecção conservadora por padrão estrutural, não por dado específico.
- Extrair author sempre do primeiro trecho em caixa alta do corpo, sem
  exigir o padrão `vem ... apresentar`: rejeitada por risco de falso
  positivo (ex.: capturar nome de tribunal ou vara em vez da parte).

### Decisão 3 — Escopo da mudança

Toda a lógica nova fica em `apply_frontmatter.py`, como funções auxiliares
específicas de peças jurídicas (ex.: `_detect_legal_doc_type_title`,
`_detect_petition_party_author`), chamadas condicionalmente a partir de
`main()` antes do fallback genérico. Não é necessário alterar
`judicial_locator.py` (pacote compartilhado) nem outras skills.

## Risks / Trade-offs

- [Risco] O padrão de "linha isolada com o nome do tipo de peça" pode não
  existir em todas as contestações reais (algumas podem não repetir a
  palavra `CONTESTAÇÃO` isolada no corpo) → Mitigação: fallback para H1
  genérico já existente; nenhuma regressão, apenas ausência de melhoria
  nesses casos.
- [Risco] O padrão de abertura de petição (`NOME, qualificação, vem ...
  apresentar`) pode variar (ex.: `vêm`, `veio`, ordem de cláusulas
  diferente) → Mitigação: regex tolera adjacências de linha (não exige
  tudo na mesma linha) e cobre apenas o caso validado no teste real; casos
  não cobertos caem em `null`, que é o comportamento atual — não há perda
  em relação ao estado presente.
- [Risco] Falso positivo capturando nome de comarca/vara em vez da parte,
  caso apareça em caixa alta seguido de vírgula antes do nome real da parte
  → Mitigação: exigir a proximidade textual com `vem ... apresentar`, que é
  específica da cláusula de qualificação da parte, não de endereçamento ao
  juízo.

## Migration Plan

Mudança aditiva e local à skill `md-frontmatter-yaml`. Não requer migração
de dados existentes; arquivos já processados não são reprocessados
automaticamente. Rollback trivial: reverter o commit da skill.

## Open Questions

Nenhuma pendente para o escopo definido nesta mudança.
