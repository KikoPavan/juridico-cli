---
name: yaml-normalizador-juridico
version: "1.1.0"
skill_type: "llm"
description: >
  Normaliza peças jurídicas curadas em artefatos Markdown individuais com frontmatter YAML
  padronizado, rastreável e pronto para roteamento pelo dispatcher de skills no pipeline
  do juridico-cli. Recebe uma Peça Curada Individual (objeto flat extraído de pecas[] do
  Envelope Curado do curador-relevancia) — nunca recebe o envelope inteiro.
  Ative para: normalizar peças, frontmatter jurídico, preparar para dispatcher,
  yaml normalizador, pipeline juridico-cli.
input_stage: "curated_pieces"
output_stage: "normalized_markdown"
tags:
  - normalizacao
  - frontmatter
  - yaml
  - juridico
  - pipeline
  - roteamento
guardrails:
  - "Não realizar extração de campos jurídicos profundos (papel das extr-*)"
  - "Nunca reverter ou modificar a acao_curatorial recebida do curador"
  - "Peças com acao_curatorial=remover não geram artefato de saída"
  - "skill_key sempre derivada do routing_map.yaml; nunca inventada"
  - "created_by_skill sempre = yaml-normalizador-juridico"
  - "Sempre validar frontmatter contra assets/io.schema.json"
---

# yaml-normalizador-juridico

## Identidade

Skill de normalização jurídica posicionada entre o `curador-relevancia` e o `dispatcher de skill`
no pipeline do `juridico-cli`. Recebe uma **Peça Curada Individual** (objeto JSON flat extraído
de `pecas[i]` do Envelope Curado); produz um arquivo `.md` com frontmatter YAML padronizado.

**Esta skill não realiza extração jurídica profunda.** Esse papel pertence às skills `extr-*`.

---

## Posição no Pipeline

```
PDF → convert → clean → segmentador-jurídico
  → curador-relevancia
  → [yaml-normalizador-juridico]  ← você está aqui
  → dispatcher-skill → extr-* → json por peça
```

---

## Entrada: Peça Curada Individual

Objeto JSON flat — **não envelope** — extraído de `pecas[i]` do Envelope Curado:

```json
{
  "piece_id": "peca_001",
  "document_type": "peticao_inicial",
  "acao_curatorial": "manter",
  "modo_aplicado": "padrao",
  "justificativa_curta": "Peça fundamental — contém causa de pedir.",
  "impacto_processual": "nuclear",
  "impacto_sentenca_confirmado": true,
  "prioridade": 1,
  "compressao_sugerida": null,
  "encaminhamento": "extr-peticao-processo",
  "audit_trail": [
    { "stage": "segmentador-juridico", "timestamp": "...", "action": "...", "notes": "..." },
    { "stage": "curador-relevancia", "timestamp": "...", "action": "...", "notes": "..." }
  ],
  "text": "...texto completo da peça...",
  "anchors": [{ "label": "cabecalho", "page": 1 }],
  "pages_start": 1,
  "pages_end": 18,
  "source_file": "processo.pdf",
  "source_path": "/data/processos/processo.pdf",
  "source_sha256": "a3f5e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3",
  "process_group_id": "proc-2024-0042",
  "origin_piece_index": 0
}
```

Schema completo: `assets/io.schema.json`

---

## Saída: Arquivo Markdown com Frontmatter YAML

Para cada peça elegível (não marcada como `remover`): **um arquivo `.md`** com:

1. **Frontmatter YAML** no topo, delimitado por `---`
2. **Corpo textual** da peça abaixo, sem alterações substantivas

Nome do arquivo: `{process_group_id}__{piece_id}.md`

---

## Enums Canônicos

| Campo | Valores |
|-------|---------|
| `acao_curatorial` | `manter`, `resumir`, `remover`, `revisar` |
| `impacto_processual` | `nuclear`, `relevante`, `acessorio`, `irrelevante` |
| `prioridade` | integer 1–5 (1 = mais alta) |
| `compressao_sugerida` | `resumo_1p`, `cabecalho_apenas`, `metadado_apenas`, `null` |
| `modo_aplicado` | `padrao`, `sintetico` |

---

## Regras de Normalização

Ver `assets/normalization_rules.md`. Princípios:

1. **Não inventar metadados.** Usar `null` ou omitir conforme contrato.
2. **Preservar texto da peça** sem alterações além de sanitização mínima de whitespace.
3. **Respeitar a decisão do curador** — nunca reverter `acao_curatorial`.
4. **Peças `remover`**: não gerar arquivo; logar.
5. **Peças `revisar`**: gerar com `review_status: pending_review`.
6. **Datas**: normalizar para ISO-8601 quando identificável.
7. **skill_key**: derivada exclusivamente do `routing_map.yaml`.

---

## Política de Roteamento

Ver `assets/routing_map.yaml` para mapeamento `document_type` → `skill_key`.

---

## Como Usar

```bash
python scripts/apply_yaml_normalization.py \
  --input peca_curada.json \
  --output-dir output/normalized
```

### Validação

```bash
python scripts/validate_yaml_normalizador_juridico.py \
  --input-dir output/normalized
```

---

## Arquivos desta Skill

```
yaml-normalizador-juridico/
├── SKILL.md
├── scripts/
│   ├── apply_yaml_normalization.py          ← engine principal
│   └── validate_yaml_normalizador_juridico.py ← validador pós-geração
├── references/
│   ├── example_input.json                    ← peça curada individual de exemplo
│   ├── example_output.md                     ← .md gerado de exemplo
│   ├── exemplo_fluxo.md                      ← fluxo ponta a ponta
│   └── field_dictionary.md                   ← dicionário de campos
└── assets/
    ├── io.schema.json                        ← schema I/O
    ├── frontmatter_template.jinja2           ← template de referência
    ├── normalization_rules.md                ← regras detalhadas
    ├── output_contract.md                    ← contrato do frontmatter
    └── routing_map.yaml                      ← mapeamento document_type → skill_key
```

---

## Guardrails

- ❌ Não realizar extração de campos jurídicos profundos
- ❌ Não alterar `acao_curatorial` recebida
- ❌ Não criar arquitetura paralela ao pipeline
- ✅ Validar frontmatter contra `io.schema.json`
- ✅ Registrar `created_by_skill: yaml-normalizador-juridico`
- ✅ Preservar `audit_trail` acrescentando entrada desta skill

---

> Esta skill normaliza formato — **não realiza análise jurídica de mérito**.
> A decisão final sobre conteúdo probatório é sempre do operador jurídico.
