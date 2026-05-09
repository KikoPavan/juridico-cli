# Regras de Limpeza — md-clean-markdown

Versão: 1.0.0

Regras genéricas, determinísticas e agnósticas de domínio que governam
o comportamento do limpador. Nenhuma regra assume tipo, domínio ou
conteúdo específico do documento.

---

## Princípio geral

> Quando houver ambiguidade, **preservar** o texto em vez de inferir estrutura.

O limpador opera apenas em sintaxe e formatação Markdown.
Nunca reescreve, interpreta ou remove conteúdo textual por critério semântico.

---

## Regra 1 — Preservação de blocos de código

Blocos delimitados por ` ``` ` ou ` ~~~ ` são **completamente isolados**
antes de qualquer processamento. Nenhuma outra regra é aplicada ao conteúdo
interno desses blocos. Ao final, os blocos são restaurados sem modificação.

```
Antes:   ```python\nprint( "hello" )   \n```
Depois:  ```python\nprint( "hello" )   \n```   ← idêntico, intocado
```

---

## Regra 2 — Trailing whitespace

Remover espaços e tabs ao final de cada linha (exceto dentro de blocos
de código, que são protegidos pela Regra 1).

```
Antes:   "Texto com espaços finais   "
Depois:  "Texto com espaços finais"
```

**Exceção:** duas ou mais linhas terminando em dois espaços (`  `) representam
quebra de linha forçada em Markdown. Neste caso, preservar exatamente dois
espaços finais.

---

## Regra 3 — Linhas em branco consecutivas

Colapsar sequências de 3 ou mais linhas em branco consecutivas para o
valor de `max_blank_lines` (padrão: 2).

```
Antes:   "Parágrafo A\n\n\n\n\nParágrafo B"
Depois:  "Parágrafo A\n\nParágrafo B"   (max_blank_lines=2 → 1 linha em branco)
```

Não remover linhas em branco isoladas — elas têm função estrutural em Markdown.

---

## Regra 4 — Normalização de headings

Garantir exatamente um espaço entre os `#` e o texto do heading.

```
Antes:   "##Título sem espaço"
Depois:  "## Título sem espaço"

Antes:   "###   Título com excesso"
Depois:  "### Título com excesso"
```

Não alterar o nível (`#`, `##`, etc.) do heading.
Não alterar o texto do heading.

---

## Regra 5 — Normalização de bullets

Substituir marcadores de lista `*` e `+` (quando usados como bullets,
não como ênfase ou multiplicação) por `-`.

```
Antes:   "* Item A"
Depois:  "- Item A"

Antes:   "+ Item B"
Depois:  "- Item B"
```

**Critério de detecção de bullet:** linha começa com `* `, `+ ` ou `- `
(marcador seguido de espaço) após opcional indentação.

Não modificar `*palavra*` (ênfase), `**palavra**` (negrito) ou `*` em
outros contextos.

---

## Regra 6 — Normalização de separadores horizontais

Unificar variantes de linha horizontal (`<hr>`) para `---`.

| Padrão detectado | Substituído por |
|------------------|-----------------|
| `***`            | `---`           |
| `___`            | `---`           |
| `===` (linha)    | `---`           |
| `- - -`          | `---`           |
| `* * *`          | `---`           |
| `_ _ _`          | `---`           |

**Critério:** linha contém apenas o padrão (com possível espaçamento),
sem outro conteúdo.

---

## Regra 7 — Preservação de marcadores de página

Dois formatos de marcador de página são reconhecidos e devem ser preservados
integralmente:

| Formato | Papel | Exemplo |
|---------|-------|---------|
| `[[Pág. N]]` | **Primário** — output real de `pdf-to-md` | `[[Pág. 1]]` |
| `<!-- page N -->` | **Legado** — compatibilidade retroativa | `<!-- page 1 -->` |

Variantes legadas suportadas: `<!-- page N: empty -->`,
`<!-- page N: extraction_failed -->`, `<!-- page N: scanned_no_ocr -->`.

Esses marcadores são a ponte entre a etapa `pdf-to-md` e esta skill.
Nenhuma regra de limpeza pode remover, modificar ou reformatar esses
marcadores.

**Proibição absoluta:** nunca converter `[[Pág. N]]` em `<!-- page N -->`
nem o inverso. Os formatos devem ser preservados exatamente como recebidos.

---

## Regra 8 — Remoção de linhas de pontuação pura

Remover linhas compostas exclusivamente por repetição de um único
caractere de pontuação não-Markdown (ex.: `====`, `....`, `####` como
decoração sem função de heading).

**Critério seguro:** linha com 4+ caracteres, todos iguais, nenhum
sendo espaço, e não sendo um separador válido Markdown (`---`, `***`, `___`).

Atenção: aplicar **apenas** quando não há ambiguidade com headings ou
separadores. Na dúvida, **preservar**.

---

## Regra 9 — Linha final do arquivo

Garantir que o arquivo termine com exatamente uma quebra de linha (`\n`).

```
Arquivo sem \n final    → adicionar \n
Arquivo com múltiplos \n → colapsar para um único \n
```

---

## Proibições absolutas

| Proibido                                        | Justificativa                                |
|-------------------------------------------------|----------------------------------------------|
| Remover ou alterar texto de headings            | Risco de perda de informação                 |
| Remover parágrafos ou seções inteiras           | Sem critério semântico explícito             |
| Inserir YAML frontmatter                        | Responsabilidade da etapa seguinte           |
| Classificar ou rotular o tipo do documento      | Fora do escopo desta skill                   |
| Reescrever frases ou parágrafos                 | Viola o princípio de preservação             |
| Aplicar regras de domínio (jurídico, médico...) | A skill é agnóstica de domínio               |
| Remover marcadores `[[Pág. N]]` ou `<!-- page N -->` | Violaria a rastreabilidade de páginas   |
| Converter `[[Pág. N]]` ↔ `<!-- page N -->`     | Viola o contrato de preservação de formato   |
| Tocar no conteúdo interno de blocos de código   | Protegido pela Regra 1                       |
