---
name: md-clean-markdown
description: >
  Recebe um arquivo Markdown bruto oriundo de qualquer domínio e produz
  Markdown limpo, normalizado e pronto para processamento posterior.
  Remove ruído visual e textual, normaliza espaçamento e quebras de linha,
  preserva títulos, listas e marcadores de página [[judicial_locator: ...]]
  (primário), [[Pág. N]] e <!-- page N --> (legados). Use esta skill sempre que o usuário quiser
  limpar ou normalizar um arquivo Markdown, preparar um .md para etapas
  subsequentes (extração, YAML, análise), ou mencionar palavras como
  "limpar markdown", "normalizar markdown", "md limpo", "segunda etapa do
  pipeline", "preparar md para processamento" — mesmo que não mencione
  "md-clean-markdown" explicitamente.
profile: local_preprocessing
version: 1.0.0
---

# md-clean-markdown

Segunda etapa do pipeline documental do `juridico-cli`.

Recebe Markdown bruto (tipicamente saído de `pdf-to-md`) e produz
Markdown limpo, normalizado e estruturalmente consistente, pronto para
etapas de extração ou adição de frontmatter YAML.

Esta skill é **agnóstica de domínio**: funciona para relatórios, manuais,
artigos, formulários, documentos corporativos, técnicos ou administrativos.
Ela não interpreta nem classifica o conteúdo.

---

## O que esta skill faz

- Recebe 1 arquivo Markdown bruto por execução
- Remove espaços redundantes no final das linhas
- Expande ligaduras tipográficas Unicode antes das correções de encoding
- Recompõe palavras hifenizadas e linhas de prosa fragmentadas antes da limpeza estrutural
- Colapsa sequências de 3+ linhas em branco para no máximo 2
- Normaliza separadores horizontais (`---`, `***`, `___`, `===`) para `---`
- Remove espaços inconsistentes entre `#` e o texto do heading
- Preserva marcadores `[[judicial_locator: ...]]` (primário), `[[Pág. N]]` e `<!-- page N -->` (legados)
- Preserva a estrutura de listas (ordenadas e não ordenadas)
- Preserva blocos de código (não toca no conteúdo interno)
- Normaliza bullets: `*` e `+` soltos → `-`
- Remove linhas compostas exclusivamente de caracteres de pontuação repetida
- Garante que o arquivo termine com exatamente uma quebra de linha
- Opcionalmente gera um `cleaning_report.md`

## O que esta skill NÃO faz

- Não interpreta semanticamente o conteúdo
- Não classifica o domínio ou tipo do documento
- Não adiciona frontmatter YAML
- Não extrai entidades nem cria resumos
- Não remove conteúdo por parecer repetitivo sem regra explícita
- Não inventa estrutura inexistente
- Não reescreve texto de nenhuma forma
- Não aplica nenhuma regra de domínio específico

---

## Posição no pipeline

```
[pdf-to-md]  →  [md-clean-markdown]  →  [frontmatter YAML]  →  [extração]
```

---

## Contrato de entrada

| Parâmetro        | CLI flag         | Obrig. | Padrão  | Descrição                                      |
|------------------|------------------|--------|---------|------------------------------------------------|
| `input_md`       | `--input`        | ✅     | —       | Caminho do `.md` bruto de entrada              |
| `output_md`      | `--output`       | ✅     | —       | Caminho do `.md` limpo de saída                |
| `page_markers`   | `--no-markers`   | ❌     | `true`  | Preservar `[[judicial_locator: ...]]` (primário), `[[Pág. N]]` e `<!-- page N -->` (legados) |
| `verbose`        | `--verbose`      | ❌     | `false` | Exibir log de operações no stderr              |
| `report`         | `--report`       | ❌     | `false` | Gerar `cleaning_report.md` junto ao output     |
| `max_blank_lines`| `--max-blank`    | ❌     | `2`     | Máximo de linhas em branco consecutivas        |

→ Especificação completa em [`assets/output_contract.md`](assets/output_contract.md)

## Contrato de saída

**Saída principal:** `<output_md>` — arquivo `.md` limpo e normalizado  
**Saída auxiliar (se `--report`):** `cleaning_report.md` no mesmo diretório

→ Detalhes em [`assets/output_contract.md`](assets/output_contract.md)

---

## Regras de limpeza

1. **Preservação** — nunca remover conteúdo sem regra explícita
2. **Ligaduras** — expandir `ﬀ`, `ﬁ`, `ﬂ`, `ﬃ`, `ﬄ`, `ﬅ` e `ﬆ` antes das demais correções
3. **Recomposição** — unir palavras hifenizadas e fragmentos de prosa sem atravessar estruturas Markdown
4. **Espaços finais** — remover trailing whitespace em cada linha
5. **Linhas em branco** — colapsar 3+ linhas em branco consecutivas para `max_blank_lines`
6. **Headings** — normalizar espaço entre `#` e texto (`##Título` → `## Título`)
7. **Bullets** — normalizar `*` e `+` como marcadores de lista para `-`
8. **Separadores** — unificar variantes de `<hr>` para `---`
9. **Blocos de código** — preservar integralmente, sem tocar no conteúdo interno
10. **Marcadores de página** — preservar `[[judicial_locator: ...]]` (primário), `[[Pág. N]]` e `<!-- page N -->` (legados); nunca converter entre formatos
11. **Linha final** — garantir exatamente `\n` ao final do arquivo

→ Regras detalhadas em [`assets/cleaning_rules.md`](assets/cleaning_rules.md)

---

## Scripts disponíveis

| Script                      | Descrição                                         |
|-----------------------------|---------------------------------------------------|
| `scripts/clean_markdown.py` | Limpador principal (CLI, determinístico)          |
| `scripts/validate_output.py`| Valida o `.md` limpo contra o contrato            |
| `scripts/run_example.sh`    | Executa limpeza de exemplo ponta a ponta          |
| `scripts/package_skill.sh`  | Empacota a skill em `.zip` para distribuição      |

---

## Fluxo de execução

```
.md bruto de entrada
       │
       ▼
[clean_markdown.py]
       │
       ├── lê arquivo linha a linha
       ├── detecta blocos de código (isola, não toca)
       ├── expande ligaduras e recompõe quebras artificiais
       ├── aplica regras de normalização fora dos blocos
       ├── preserva marcadores judiciais primários e legados
       └── escreve <output_md>
                │
                ├── (opcional) escreve cleaning_report.md
                └── [validate_output.py]
```

O pipeline consumidor aplica, antes da extração JSON, validação configurável
com limiar padrão de 50 caracteres úteis. Um documento vazio ou composto apenas
por frontmatter, boilerplate e localizadores recebe
`rejected: no_meaningful_content` e não é enviado ao LLM.

---

## Uso rápido

```bash
# Limpeza básica
python scripts/clean_markdown.py \
  --input  ~/devops/juridico-cli/var/input/md-clean-markdown/documento.md \
  --output ~/devops/juridico-cli/var/output/md-clean-markdown/documento_limpo.md

# Com relatório e log
python scripts/clean_markdown.py \
  --input  ~/devops/juridico-cli/var/input/md-clean-markdown/documento.md \
  --output ~/devops/juridico-cli/var/output/md-clean-markdown/documento_limpo.md \
  --report --verbose

# Exemplo pré-configurado
bash scripts/run_example.sh
```

---

## Referências internas

- [`assets/output_contract.md`](assets/output_contract.md)
- [`assets/cleaning_rules.md`](assets/cleaning_rules.md)
- [`assets/normalization_map.yaml`](assets/normalization_map.yaml)
- [`references/dicionario_variaveis.md`](references/dicionario_variaveis.md)
- [`references/exemplo_entrada.md`](references/exemplo_entrada.md)
- [`references/exemplo_saida.md`](references/exemplo_saida.md)
