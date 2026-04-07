# Regras de Frontmatter — md-frontmatter-yaml

Versão: 1.0.0

Regras que governam quando preencher, quando omitir, quando usar `null`
e como preservar o corpo do documento.

---

## Princípio geral

> **Conservadorismo:** na dúvida, usar `null` ou valor padrão em vez de inventar.

Esta skill adiciona metadados básicos observáveis no documento.
Nunca cria informação que não esteja explícita ou facilmente inferível
a partir do texto.

---

## Regra 1 — Verificar se já há frontmatter

Antes de qualquer processamento, verificar se o arquivo já começa com `---`.

- Se sim → **abortar com exit code 2** e informar o usuário
- Se não → prosseguir normalmente

Nunca sobrescrever frontmatter existente silenciosamente.

---

## Regra 2 — Quando preencher um campo

Preencher um campo quando **pelo menos uma** das condições for verdadeira:

1. O valor foi fornecido explicitamente via CLI (`--title`, `--author`, etc.)
2. O valor é inferível com alta confiança por heurística simples (regex)
3. O campo tem um valor padrão definido (`document_type`, `language`, `status`)
4. O campo é de rastreabilidade obrigatória (`source_file`, `source_path`,
   `created_by_skill`)

---

## Regra 3 — Quando usar `null`

Usar `null` quando:

- O campo é inferível mas **não foi encontrado** no texto
- O campo foi fornecido como string vazia via CLI
- Há ambiguidade entre dois valores possíveis sem critério claro de escolha

Campos que usam `null` por padrão: `title`, `document_date`, `author`

```yaml
title: null
document_date: null
author: null
```

---

## Regra 4 — Quando omitir um campo

Nesta versão, **nenhum campo é omitido**: todos os campos do template
sempre aparecem no frontmatter, usando `null` ou valor padrão quando
não preenchidos.

Isso garante consistência e facilita o processamento downstream.

---

## Regra 5 — Inferência do título

Estratégia de detecção (aplicada em ordem, parar no primeiro match):

1. Parâmetro `--title` via CLI → usar diretamente
2. Primeiro heading `# Texto` no corpo → extrair `Texto`
3. Nenhum match → `null`

Limpar o título extraído: remover marcadores de página, trailing spaces,
e caracteres de controle.

---

## Regra 6 — Inferência da data

Estratégia de detecção nas **primeiras 20 linhas** do corpo:

| Padrão no texto                       | Resultado no YAML    |
|---------------------------------------|----------------------|
| `15/03/2024` ou `15-03-2024`          | `"2024-03-15"`       |
| `2024-03-15`                          | `"2024-03-15"`       |
| `15 de março de 2024`                 | `"2024-03-15"`       |
| `março de 2024` / `Março 2024`        | `"2024-03"`          |
| Nenhum padrão detectado               | `null`               |

**Regra:** na ambiguidade entre dois padrões, usar o primeiro encontrado.
Sempre converter para ISO 8601. Nunca usar data parcial além de `YYYY-MM`.

---

## Regra 7 — Inferência do autor

Estratégia de detecção nas **primeiras 30 linhas** do corpo:

| Padrão detectado                      | Exemplo                              |
|---------------------------------------|--------------------------------------|
| `Responsável: <nome>`                 | `Responsável: João Silva`            |
| `Autor: <nome>`                       | `Autor: Maria Costa`                 |
| `Elaborado por: <nome>`               | `Elaborado por: Equipe de TI`        |
| `Preparado por: <nome>`               | `Preparado por: Dep. de Operações`   |
| `Redator: <nome>`                     | `Redator: Carlos Mendes`             |

Capturar tudo após o delimitador `:` até o fim da linha (trimmed).

Nenhum padrão encontrado → `null`.

---

## Regra 8 — Preservação do corpo

O corpo do documento (tudo após o frontmatter inserido) deve ser idêntico
ao arquivo de entrada, byte a byte.

**Verificação:** fazer diff entre o corpo da saída e o arquivo de entrada.
Se houver diferença, reportar como erro.

Nunca modificar headings, listas, tabelas, blocos de código ou
marcadores de página durante a inserção do frontmatter.

---

## Regra 9 — Validade do YAML

O YAML gerado deve:

- Ser parseável por `pyyaml` sem warnings
- Usar aspas duplas para strings com caracteres especiais ou que comecem
  com `#`, `:`, `{`, `[`
- Usar `null` (não `~` nem vazio) para valores ausentes
- Usar lista explícita `[]` quando tags estiver vazio
- Não conter tabs (usar 2 espaços de indentação)

---

## Regra 10 — Campos fora do escopo

Os seguintes campos **nunca** devem ser inseridos por esta skill,
independentemente de serem detectáveis no texto:

`process_number`, `court`, `comarca`, `vara`, `parties`, `classe_processual`

Esses campos são responsabilidade de skills de extração especializadas
que operam **depois** desta skill no pipeline.
