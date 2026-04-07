# Regras de Conversão — pdf-to-md

Versão: 1.0.0  
Escopo: agnóstico de domínio

Estas regras definem o comportamento obrigatório e esperado do conversor
para qualquer tipo de documento PDF textual.

---

## Regra 1 — Preservar a ordem do conteúdo

O texto extraído deve seguir a ordem natural do documento:
página a página, bloco a bloco, linha a linha.

- ✅ Manter a sequência original de seções e parágrafos
- ✅ Processar páginas em ordem crescente (1, 2, 3...)
- ❌ Não reordenar blocos por relevância ou tamanho
- ❌ Não mover conteúdo de uma página para outra

---

## Regra 2 — Preservar marcadores de página

Antes do conteúdo de cada página, inserir:

```
<!-- page N -->
```

onde `N` é o número ordinal da página começando em 1.

Variantes para situações especiais:

| Situação               | Marcador gerado                              |
|------------------------|----------------------------------------------|
| Página normal          | `<!-- page N -->`                            |
| Página em branco       | `<!-- page N: empty -->`                     |
| Falha de extração      | `<!-- page N: extraction_failed -->`         |
| Imagem sem OCR         | `<!-- page N: scanned_no_ocr -->`            |

O conversor **nunca deve omitir silenciosamente** uma página.
Toda página deve gerar ao menos um marcador no arquivo de saída.

---

## Regra 3 — Mapear títulos para headings Markdown

Quando o motor de extração identificar elementos de título
(por tamanho de fonte, negrito, posição ou heurística textual),
mapear conforme a hierarquia detectada:

| Nível detectado   | Markdown gerado  |
|-------------------|------------------|
| Título principal  | `# Título`       |
| Subtítulo         | `## Subtítulo`   |
| Seção terciária   | `### Seção`      |
| Demais            | parágrafo normal |

**Conservadorismo:** na dúvida, preservar como parágrafo.
Não inventar hierarquia onde não há evidência clara.

---

## Regra 4 — Preservar listas quando detectáveis

Se o texto contiver marcadores de lista (`•`, `-`, `*`, números seguidos de ponto),
tentar preservá-los como listas Markdown:

```markdown
- Item A
- Item B
- Item C
```

ou

```markdown
1. Primeiro item
2. Segundo item
```

Se a detecção for ambígua, preservar como texto plano.

---

## Regra 5 — Literalidade do conteúdo

O texto extraído deve ser preservado **como está no PDF**:

- ✅ Manter grafia, pontuação e formatação numérica originais
- ✅ Manter abreviações e siglas sem expansão
- ❌ Não corrigir ortografia ou gramática
- ❌ Não completar palavras cortadas por hifenização de layout
- ❌ Não inferir palavras ilegíveis por OCR ruim
- ❌ Não traduzir ou adaptar o idioma

---

## Regra 6 — Proibições absolutas

As seguintes operações são **explicitamente proibidas**:

| Proibido                                      | Justificativa                                     |
|-----------------------------------------------|---------------------------------------------------|
| Inserir YAML frontmatter                      | Responsabilidade de etapas posteriores            |
| Classificar o tipo ou domínio do documento    | Responsabilidade de skills de análise             |
| Extrair entidades (nomes, datas, valores...)  | Responsabilidade de skills de extração            |
| Resumir ou condensar o conteúdo               | Responsabilidade de skills de sumarização         |
| Remover páginas, seções ou parágrafos         | Perda de informação irreversível                  |
| Truncar o documento por tamanho               | Todo o conteúdo deve chegar ao próximo estágio    |
| Especializar regras por domínio do documento  | A skill deve ser agnóstica de domínio             |

---

## Regra 7 — Tratamento de páginas problemáticas

O conversor nunca deve abortar por causa de uma página problemática.

Para cada página com problema:
1. Emitir o marcador de falha adequado
2. Registrar no `conversion_report.md` (se `--report`)
3. Continuar processando o restante do documento

---

## Regra 8 — Encoding e caracteres especiais

- Saída sempre em **UTF-8**
- Caracteres não mapeáveis: substituir por `\uFFFD` (replacement character)
- Registrar ocorrências no `conversion_report.md`

---

## Motor de extração — ordem de preferência (modo `auto`)

```
1º  pdfminer.six  → melhor para PDFs com texto nativo e layout preservado
2º  pymupdf       → fallback mais robusto para PDFs complexos ou corrompidos
```

Usar `--engine pdfminer` ou `--engine pymupdf` para forçar um motor específico.
