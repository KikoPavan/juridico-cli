> [!NOTE]
> **DOCUMENTO AUXILIAR OPERACIONAL**
> Referência de classificação de schemas do projeto. Complementa, mas não substitui, o documento canônico da arquitetura.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Classificação de Schemas — juridico-cli

> Gerado em: 2026-04-02
> Baseado em inspeção real de arquivos e grep de referências.

---

## Contexto de autoridade

| Localização | Papel |
| --- | --- |
| `platform/skills/<bundle>/assets/` | Schema autoritativo de cada bundle extr-* |
| `packages/shared-schemas/` | Schemas globais, defs reutilizáveis, contratos cross-app |
| `schemas/` (raiz) | Legado pré-migração — cópia byte-a-byte de `packages/shared-schemas/` |
| `agents/*/` | Contratos I/O de agentes legados — congelados |
| `apps/data-processing/…/contracts/` | Contratos internos do app migrado |

---

## Legenda de categorias

| Código | Significado |
| --- | --- |
| `authoritative_bundle_schema` | Fonte da verdade em `platform/skills/<bundle>/assets/` |
| `authoritative_shared_schema` | Fonte da verdade em `packages/shared-schemas/` — global ou cross-app |
| `duplicate_to_remove_later` | Cópia no lugar errado; remover na Fase 4 |
| `app_local_schema` | Contrato local de um app/agente; não é compartilhado |

---

## Grupo A — Schemas de extração 1:1 duplicados

> Existem simultaneamente em `packages/shared-schemas/` **e** em `platform/skills/extr-*/assets/`.
> A cópia autoritativa é a do bundle. As cópias em `shared-schemas/` e em `schemas/` (raiz) são `duplicate_to_remove_later`.

| Arquivo | Localização atual | Localização autoritativa | Quem referencia | Categoria (bundle copy) | Categoria (shared-schemas copy) | Ação recomendada |
| --- | --- | --- | --- | --- | --- | --- |
| `cabecalho_processo.schema.json` | `shared-schemas/` + `extr-cabecalho-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-cabecalho-processo/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | Fase 4: atualizar `skill_registry.yaml`; remover cópias de `shared-schemas/` e `schemas/` |
| `cabecalho_processo.consolidated.schema.json` | `shared-schemas/` + `extr-cabecalho-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-cabecalho-processo/assets/` | pipeline validate stage | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `peticao_processo.schema.json` | `shared-schemas/` + `extr-peticao-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-peticao-processo/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `peticao_processo.consolidated.schema.json` | `shared-schemas/` + `extr-peticao-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-peticao-processo/assets/` | pipeline validate stage | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `contestacao_processo.schema.json` | `shared-schemas/` + `extr-contestacao-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-contestacao-processo/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `contestacao_processo.consolidated.schema.json` | `shared-schemas/` + `extr-contestacao-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-contestacao-processo/assets/` | pipeline validate stage | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `decisao_processo.schema.json` | `shared-schemas/` + `extr-decisao-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-decisao-processo/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `decisao_processo.consolidated.schema.json` | `shared-schemas/` + `extr-decisao-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-decisao-processo/assets/` | pipeline validate stage | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `mandato_processo.schema.json` | `shared-schemas/` + `extr-mandato-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-mandato-processo/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `mandato_processo.consolidated.schema.json` | `shared-schemas/` + `extr-mandato-processo/assets/` + `schemas/` (raiz) | `platform/skills/extr-mandato-processo/assets/` | pipeline validate stage | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `procuracao.schema.json` | `shared-schemas/` + `extr-procuracao/assets/` + `schemas/` (raiz) | `platform/skills/extr-procuracao/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `procuracao.consolidated.schema.json` | `shared-schemas/` + `extr-procuracao/assets/` + `schemas/` (raiz) | `platform/skills/extr-procuracao/assets/` | pipeline validate stage | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `contrato_social.schema.json` | `shared-schemas/` + `extr-contrato-social/assets/` + `schemas/` (raiz) | `platform/skills/extr-contrato-social/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `escritura_imovel.schema.json` | `shared-schemas/` + `extr-escritura-imovel/assets/` + `schemas/` (raiz) | `platform/skills/extr-escritura-imovel/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |
| `escritura_hipotecaria.schema.json` | `shared-schemas/` + `extr-escritura-hipotecaria/assets/` + `schemas/` (raiz) | `platform/skills/extr-escritura-hipotecaria/assets/` | `skill_registry.yaml` (`schema_ref`) | `authoritative_bundle_schema` | `duplicate_to_remove_later` | idem |

---

## Grupo B — Schemas apenas em `platform/skills/*/assets/` (sem cópia em shared-schemas)

| Arquivo | Localização atual | Localização autoritativa | Quem referencia | Categoria | Ação recomendada |
| --- | --- | --- | --- | --- | --- |
| `jus-diagnose/assets/irac_schema.json` | `platform/skills/jus-diagnose/assets/` | `platform/skills/jus-diagnose/assets/` | `irac_analyzer.py`, `SKILL.md` | `authoritative_bundle_schema` | Manter; não é extração 1:1, não vai para shared-schemas |
| `jus-breve/assets/firac_schema.json` | `platform/skills/jus-breve/assets/` | `platform/skills/jus-breve/assets/` | `firac_analyzer.py`, `SKILL.md` | `authoritative_bundle_schema` | Manter |
| `legal-data-extractor/assets/schema.json` | `platform/skills/legal-data-extractor/assets/` | `platform/skills/legal-data-extractor/assets/` | `dictionary.md`, `SKILL.md` | `authoritative_bundle_schema` | Manter |

---

## Grupo C — Schemas globais/agregados em `packages/shared-schemas/`

> Devem **permanecer** em `shared-schemas/`. Nenhum bundle extr-* único os possui.

| Arquivo | Localização atual | Localização autoritativa | Quem referencia | Categoria | Justificativa |
| --- | --- | --- | --- | --- | --- |
| `defs/common.schema.json` | `packages/shared-schemas/defs/` | `packages/shared-schemas/defs/` | Múltiplos schemas via `$ref` (`processo`, `cabecalho`, `peticao`, `contestacao`, `decisao`, `mandato`) | `authoritative_shared_schema` | Definições base reutilizáveis (`NonEmptyString`, `UUID`, `SHA256`, `Anchor`, datas ISO) |
| `cadeia_obrigacoes.schema.json` | `packages/shared-schemas/` + `schemas/` (raiz) | `packages/shared-schemas/` | `agents/petition-cli/config.yaml`, `agents/compliance-cli/config.yaml`, `agents/case-law-cli/config.yaml` | `authoritative_shared_schema` | Grafo cross-extractor de obrigações; consumido por múltiplos agentes legados |

---

## Grupo D — Casos especiais

### `processo.schema.json` — reclassificado

**Regra confirmada:** consumido exclusivamente pelo módulo `extr-processo`; sem reutilização cross-module.

**Consumidores reais verificados:**

| Consumidor | Caminho referenciado | Status |
| --- | --- | --- |
| `platform/skills/extr-processo/scripts/validate_output.py:16` | `assets/processo.schema.json` (ASSET_SCHEMA) | Correto — bundle-local |
| `platform/skills/extr-processo/SKILL.md` | `assets/processo.schema.json` | Correto |
| `platform/skills/extr-processo/SKILL.md` (instrução de extração) | `assets/processo.schema.json` | Correto — incorporado ao SKILL.md |
| `platform/skill-runtime/skill_registry.yaml:33` | `packages/shared-schemas/processo.schema.json` | **Único ponto a corrigir** |
| `platform/skills/extr-processo/scripts/validate_output.py:19` | `schemas/processo.schema.json` (CANONICAL_SCHEMA) | Residual — fixup pendente |
| `agents/collector-proc/config.yaml:52,200` | `schemas/processo.schema.json` | Legado congelado |
| `apps/data-processing/…/collector_proc/config.yaml:52,200` | `schemas/processo.schema.json` | App migrado — fixup pendente |
| `apps/data-processing/…/collector_proc/io.schema.json:109` | `../../schemas/processo.schema.json` | App migrado — fixup pendente |

**Classificação final:**

| Cópia | Categoria | Justificativa |
| --- | --- | --- |
| `platform/skills/extr-processo/assets/processo.schema.json` | **`authoritative_bundle_schema`** | Referência direta de `validate_output.py:16`, `SKILL.md`, `agent.md` — todos internos ao bundle |
| `packages/shared-schemas/processo.schema.json` | **`duplicate_to_remove_later`** | Referenciada apenas por `skill_registry.yaml:33` — corrigível com 1 linha |
| `schemas/processo.schema.json` (raiz) | **`duplicate_to_remove_later`** | Referenciada por legado congelado e por `validate_output.py:19` (CANONICAL_SCHEMA residual) |

**Diff proposto para `skill_registry.yaml`:**

```diff
--- a/platform/skill-runtime/skill_registry.yaml
+++ b/platform/skill-runtime/skill_registry.yaml
@@ -30,7 +30,7 @@
   extr-processo:
     path: "platform/skills/extr-processo"
     profile: "large_context"
-    schema_ref: "packages/shared-schemas/processo.schema.json"
+    schema_ref: "platform/skills/extr-processo/assets/processo.schema.json"
```

**Fixups adicionais registrados** (não são Fase 4 — alinhamento interno do bundle e app migrado):

| Arquivo | Linha | Problema | Correção futura |
| --- | --- | --- | --- |
| `platform/skills/extr-processo/scripts/validate_output.py` | 19 | `CANONICAL_SCHEMA` aponta para `schemas/` raiz legada | Substituir por `ASSET_SCHEMA` (já declarada na linha 16) |
| `apps/data-processing/…/collector_proc/config.yaml` | 52, 200 | `schema_file: "schemas/processo.schema.json"` | Atualizar para `platform/skills/extr-processo/assets/processo.schema.json` |
| `apps/data-processing/…/collector_proc/io.schema.json` | 109 | `$ref: "../../schemas/processo.schema.json"` | Atualizar para path do bundle |

### `v1_procuracao.schema.json`

| Cópia | Categoria | Justificativa |
| --- | --- | --- |
| `packages/shared-schemas/v1_procuracao.schema.json` | **`duplicate_to_remove_later`** | Schema v1 com `$id: example.com` — supersedido por `procuracao.schema.json` (`$id: juridico-cli.local`); zero referência em código ativo |
| `schemas/v1_procuracao.schema.json` (raiz) | **`duplicate_to_remove_later`** | idem |

---

## Grupo E — Contratos I/O de agentes legados (`agents/*/io.schema.json`)

> Congelados. Não tocar até Fase 4.

| Arquivo | Localização atual | Localização autoritativa | Quem referencia | Categoria |
| --- | --- | --- | --- | --- |
| `agents/collector-proc/io.schema.json` | `agents/collector-proc/` | local | agente legado apenas | `app_local_schema` |
| `agents/collector-cad_obr/io.schema.json` | `agents/collector-cad_obr/` | local | agente legado apenas | `app_local_schema` |
| `agents/firac-cli/io.schema.json` | `agents/firac-cli/` | local | agente legado apenas | `app_local_schema` |
| `agents/law-cli/io.schema.json` | `agents/law-cli/` | local | agente legado apenas | `app_local_schema` |
| `agents/case-law-cli/io.schema.json` | `agents/case-law-cli/` | local | agente legado apenas | `app_local_schema` |
| `agents/petition-cli/io.schema.json` | `agents/petition-cli/` | local | agente legado apenas | `app_local_schema` |
| `agents/compliance-cli/io.schema.json` | `agents/compliance-cli/` | local | agente legado apenas | `app_local_schema` |
| `agents/evidence-agent/io.schema.json` | `agents/evidence-agent/` | local | agente legado apenas | `app_local_schema` |

---

## Grupo F — Contratos internos de `apps/data-processing`

| Arquivo | Localização atual | Localização autoritativa | Quem referencia | Categoria | Ação recomendada |
| --- | --- | --- | --- | --- | --- |
| `collectors/collector_proc/io.schema.json` | `apps/data-processing/src/…/collector_proc/` | local | collector_proc migrado | `app_local_schema` | Manter |
| `collectors/collector_cad_obr/io.schema.json` | `apps/data-processing/src/…/collector_cad_obr/` | local | collector_cad_obr migrado | `app_local_schema` | Manter |
| `contracts/extraction_result.schema.json` | `apps/data-processing/src/data_processing/contracts/` | local | pipeline validate stage | `app_local_schema` | Candidato a `packages/shared-schemas/` se `apps/legal-core` passar a consumir |
| `contracts/ingestion_job.schema.json` | `apps/data-processing/src/data_processing/contracts/` | local | pipeline internamente | `app_local_schema` | Manter local |
| `contracts/normalized_doc.schema.json` | `apps/data-processing/src/data_processing/contracts/` | local | converter stage | `app_local_schema` | Manter local |

---

## Sumário executivo

| Categoria | Quantidade | Composição |
| --- | --- | --- |
| `authoritative_bundle_schema` | 19 | 15 schemas 1:1 (Grupo A, bundle copies) + 3 únicos (Grupo B) + `processo` (Grupo D, reclassificado) |
| `authoritative_shared_schema` | 2 | `defs/common`, `cadeia_obrigacoes` |
| `duplicate_to_remove_later` | 18 | 15 cópias de Grupo A em `shared-schemas/` + `processo` em `shared-schemas/` + `processo` em `schemas/` raiz + `v1_procuracao` |
| `app_local_schema` | 13 | 8 agentes legados + 5 contratos de `apps/data-processing` |

> **Terceira camada de duplicação:** o diretório `schemas/` na raiz é uma cópia byte-a-byte pré-migração de `packages/shared-schemas/`. +19 arquivos adicionais `duplicate_to_remove_later` não listados individualmente.

---

## Bloqueio para Fase 4 — dependência em `skill_registry.yaml`

`platform/skill-runtime/skill_registry.yaml` referencia atualmente **10 schemas** via `schema_ref: packages/shared-schemas/…`.

Antes de remover qualquer cópia de `shared-schemas/`, o `skill_registry.yaml` deve ser atualizado para apontar para `platform/skills/<bundle>/assets/`. Os dois passos devem ocorrer **no mesmo commit** para evitar janela de referência quebrada:

```yaml
# ANTES (atual)
extr-cabecalho-processo:
  schema_ref: "packages/shared-schemas/cabecalho_processo.schema.json"

# DEPOIS (Fase 4)
extr-cabecalho-processo:
  schema_ref: "platform/skills/extr-cabecalho-processo/assets/cabecalho_processo.schema.json"
```

**Fase 4 não está autorizada.** Não executar nenhum dos passos acima sem gate explícito do usuário.
