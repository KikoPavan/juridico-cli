---
base: extraction-base.md
description: "Extrai dados estruturados de procurações (v3.1): outorgantes, outorgados,
  poderes específicos, flags PF/PJ, arquivo de origem e metadados operacionais. Use
  esta skill sempre que o documento for uma procuração ou instrumento de outorga de
  poderes. Acione também para: \"extrair procuração\", \"estruturar poderes da procuração\",
  \"coletar outorgantes e outorgados\", \"pipeline collector-proc procuracao\", \"bastante
  procurador\".\n"
document_types:
- procuracao
hitl: false
key_fields:
- arquivo_origem
- schema_utilizado
- status
- tipo_evidencia
- origem
- tipo_documento
- data_outorga
- outorgantes
- outorgados
- transfere_poderes_pj
- transfere_poderes_pf
- descricao_poderes
- poderes_especificos
- fonte
llm_default: gemini_api
name: extr-procuracao
target_schema: assets/procuracao.schema.json
version: 0.2.0
---

# Instrução de Extração: Procuração (v3.1)

Seu único output é um objeto JSON conforme `assets/procuracao.schema.json`.
Leia e aplique as regras de `../_shared/proc-core.md`. As regras específicas
abaixo **prevalecem** sobre o core quando houver conflito.

---

## Regras específicas

### 0) Status
- Inicie com `status = "sucesso"`.
- Se qualquer Quality Gate falhar, mude para `status = "falha"` (mantenha os campos).

### 1) `arquivo_origem` e `fonte.arquivo_md` (crítico)
Buscar na ordem:
A) Linha explícita no início do documento (~80 linhas):
   - `SOURCE_FILENAME: <nome>.md`, `ARQUIVO_ORIGEM: <nome>.md`, `MD_FILENAME: <nome>.md`
B) Front matter YAML: campo `source_filename`
C) Único `*.md` mencionado que não seja `collector-proc.md`

- Preencher com basename (sem caminho).
- Nunca apontar para `collector-proc.md` ou paths de prompts.
- Se não encontrar: `""` e `status = "falha"`.

### 2) Metacampos fixos
- `schema_utilizado` = `"schemas/procuracao.schema.json"`
- `tipo_documento` = `"Procuração"` (somente com sinais de procuração; se não houver,
  manter `"Procuração"` e marcar `status = "falha"`).
- `tipo_evidencia` / `origem`:
  - se houver `case_id` não-vazio no front matter → `"processo"`
  - caso contrário → `"juntada"`

### 3) `data_outorga`
- Extrair data literal explícita (ex.: "28 de JUNHO de 2002").
- Preferir data do título/epígrafe ou frase de lavratura/assinatura.
- Se não houver: `""` (sem inferir).

### 4) `outorgantes[]` e `outorgados[]` — somente nomes
- Extrair **somente nomes** (sem CPF/RG/endereço/estado civil).
- "OUTORGANTE(S)" → `outorgantes`; "OUTORGADO(S)"/"PROCURADOR(ES)"/"BASTANTE PROCURADOR" → `outorgados`.
- Separar por linhas, ";", vírgulas ou "e" quando nomes forem claramente distintos.

### 5) Flags PF/PJ — somente no bloco dos OUTORGANTES
Padrão: `transfere_poderes_pf = false`, `transfere_poderes_pj = false`.

Definir `bloco_outorgantes`: trecho do cabeçalho "OUTORGANTE(S)" até o próximo
cabeçalho; ou ~1500 chars ao redor da primeira ocorrência dos nomes dos outorgantes.

Somente dentro de `bloco_outorgantes`:
- PF (`true`) se: CPF, RG, "portador(a) do RG", "inscrito(a) no CPF",
  "brasileiro(a)", "casado(a)", "residente e domiciliado(a)", "pessoa física".
- PJ (`true`) se: CNPJ, "pessoa jurídica", razão social com LTDA/S/A/EIRELI/ME/EPP
  associada ao outorgante (não a terceiros dentro dos poderes).

### 6) `poderes_especificos[]` — quebra por ponto e vírgula
- Extrair bloco principal de poderes ("confere poderes", "podendo para tanto" etc.).
- Se contiver `;`: quebrar em múltiplos itens (um por segmento, trim).
- Se segmento tiver lista clara por vírgulas iniciando com verbos: quebrar por vírgula
  somente quando cada parte iniciar com verbo e fizer sentido independente.
- Se não houver separadores: 1 item com o parágrafo integral.
- Literalidade: apenas remover quebras artificiais de linha.

### 7) `descricao_poderes`
- Construir descrição curta apenas com termos/atos presentes em `poderes_especificos`.
- Não adicionar poderes não listados.

### 8) `fonte`
- `fonte.arquivo_md` = basename obtido na regra 1.
- `fonte.fls` = marcador explícito de folha/página quando existir; senão `""`.
- `fonte.rotulo_documento` = epígrafe/título literal quando existir; senão `""`.

### 9) Opcionais
- `local` = texto literal quando explícito; senão `""`.
- `restricoes_ou_limitacoes` = lista explícita; senão `[]`.
- `assinantes` = nomes explicitamente nominados; senão `[]`.

---

## Quality Gates

| Gate | Verificação                                                                               |
|------|------------------------------------------------------------------------------------------|
| A    | Se "OUTORGANTE(S)" constar: `outorgantes` não pode estar vazio                           |
| B    | Se "OUTORGADO(S)"/"PROCURADOR" constar: `outorgados` não pode estar vazio                |
| C    | Se "poderes"/"bastante procurador" constar: `poderes_especificos` não pode estar vazio   |
| D    | `arquivo_origem` e `fonte.arquivo_md` devem ser basename `*.md`, nunca o prompt          |

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                       |
|-----------------|-------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                   |
| `output_dir`    | `var/output/proc`                                                  |
| `output_prefix` | `procuracao_out`                                                   |
| `schema_file`   | `platform/skills/extr-procuracao/assets/procuracao.schema.json`   |

## Arquivos da skill

| Arquivo                                      | Propósito                                   |
|----------------------------------------------|---------------------------------------------|
| `SKILL.md`                                   | Instrução canônica de extração (este arquivo)|
| `assets/procuracao.schema.json`              | Schema v3.1                                 |
| `assets/procuracao.consolidated.schema.json` | Schema consolidado                          |
| `references/dicionario_campos.md`            | Dicionário de campos                        |
| `scripts/validate_output.py`                 | Validação                                   |

## Uso pelo runtime

1. Carregar documento (Markdown) de `input_dir`.
2. Carregar instrução de extração de `SKILL.md` via `bundle_loader`.
3. A skill produz JSON v3.1 conforme `assets/procuracao.schema.json`.
4. Validar: `scripts/validate_output.py --input <output.json>`.
5. Gravar em `output_dir/<output_prefix>_<id>.json`.
