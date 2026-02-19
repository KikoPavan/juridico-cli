---
name: procuracao
agent: collector-proc
version: "0.2.0"
target_schema: "schemas/procuracao.schema.json"
document_types:
  - procuracao
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
  - local
  - restricoes_ou_limitacoes
  - assinantes
validation_rules:
  - literalidade
  - nao_inferir_poderes
  - nao_inventar_partes
  - preservar_texto_de_clausulas
  - fonte_deve_ser_md_de_origem
  - nao_apontar_para_prompt
---

# SKILL — procuracao (v3.1)

## Finalidade

Gerar um JSON **compatível com o schema v3.1** de procuração, contendo os campos do conteúdo v0 (listas/descrições) + metacampos operacionais.

Regras gerais:
- Não inferir fatos.
- Campos obrigatórios devem sempre existir.
- Quando algo não estiver explícito: listas -> `[]` (apenas se permitido pelo schema), strings -> `""`, booleans -> `false`.
- Como o schema v3.1 exige certos campos não vazios, se não houver base textual suficiente, preencher o melhor possível **sem inventar** e marcar `status="falha"` (mas ainda retornando JSON válido).

## Regras específicas (além do CORE)

### 0) Inicialização de status
- Inicie com `status = "sucesso"`.
- Se qualquer Quality Gate falhar, troque para `status = "falha"` (não apague campos).

### 1) Como obter `arquivo_origem` e `fonte.arquivo_md` (crítico)

Objetivo: preencher com **basename** do arquivo `.md` real do documento (sem caminho).

Ordem de busca (usar o primeiro que existir):

A) Linha explícita no corpo do documento (preferencial quando o runner remove YAML):
- procurar no início do texto (primeiras ~80 linhas) um destes formatos:
  - `SOURCE_FILENAME: <nome>.md`
  - `ARQUIVO_ORIGEM: <nome>.md`
  - `ARQUIVO_MD: <nome>.md`
  - `MD_FILENAME: <nome>.md`
- extrair `<nome>.md` como basename.

B) Front matter YAML (se estiver presente em `{{DOCUMENT_TEXT}}`):
- localizar o bloco entre `---` e `---`
- extrair `source_filename`
- converter para basename removendo caminho (`/` ou `\`).

C) Fallback controlado por evidência:
- procurar por ocorrências de algo que pareça `*.md` no início do documento;
- se existir **exatamente um** candidato `*.md` e ele não for `collector-proc.md`, usar esse candidato como basename.

Preenchimento:
- `arquivo_origem` = basename encontrado
- `fonte.arquivo_md` = basename encontrado

Proibições:
- nunca apontar para `collector-proc.md` ou qualquer caminho em `agents/collector-proc/prompts/`.

Se nenhum basename puder ser obtido:
- preencher com `""` e marcar `status="falha"` (Quality Gate D).

### 2) Metacampos fixos e origem
- `schema_utilizado` = `"schemas/procuracao.schema.json"`
- `tipo_documento` = `"Procuração"` (somente se o texto tiver sinais de procuração: “PROCURAÇÃO”, “OUTORGANTE/OUTORGADO”, “BASTANTE PROCURADOR”)
  - se não houver sinais suficientes, manter `"Procuração"` mas marcar `status="falha"`.

- `origem` e `tipo_evidencia`:
  - se houver `case_id` no front matter e ele não estiver vazio -> `"processo"`
  - caso contrário -> `"juntada"`
  - nunca usar “desconhecido” neste schema.

### 3) `data_outorga` (literal)
- Extrair a data literal quando explícita (ex.: “28 de JUNHO de 2002”, “28/06/2002”).
- Preferir a data que estiver no título/epígrafe ou na frase de lavratura/assinatura.
- Se não houver data explícita, usar `""` (sem inferir).

### 4) `outorgantes[]` e `outorgados[]` — nomes literais, sem qualificação
- Extrair **somente nomes** (não incluir CPF/RG/endereço/estado civil).
- Buscar blocos:
  - “OUTORGANTE(S)” -> alimenta `outorgantes`
  - “OUTORGADO(S)” / “PROCURADOR(ES)” / “BASTANTE PROCURADOR” -> alimenta `outorgados`
- Separação:
  - separar por linhas, “;”, vírgulas, ou “e” quando houver nomes claramente distintos.
- Se o texto estiver incompleto: não inventar.

### 5) Flags PF/PJ — analisar somente no bloco dos OUTORGANTES (evitar contaminação por terceiros)
Padrão: `transfere_poderes_pf = false`, `transfere_poderes_pj = false`.

Defina `bloco_outorgantes`:
- se existir cabeçalho “OUTORGANTE(S)”, use o trecho do cabeçalho até antes do próximo cabeçalho (“OUTORGADO”, “PODERES”, “MANDATO”, etc.).
- se não existir, use até ~1500 caracteres ao redor da primeira ocorrência dos nomes em `outorgantes`.

Somente dentro de `bloco_outorgantes`:

- PF (`transfere_poderes_pf = true`) se houver indício explícito:
  - “CPF”, “RG”, “portador(a) do RG”, “inscrito(a) no CPF”
  - “brasileiro(a)”, “casado(a)”, “residente e domiciliado(a)”
  - “pessoa física”

- PJ (`transfere_poderes_pj = true`) se houver indício explícito:
  - “CNPJ”
  - “pessoa jurídica”
  - razão social com sufixos (LTDA, S/A, EIRELI, ME, EPP) **associados ao outorgante**, não a terceiros

Proibição:
- Não marcar PJ por “BANCO ... S/A” dentro dos poderes.

### 6) `poderes_especificos[]` — regra crítica (quebra como v0 quando houver estrutura)
- Extrair o bloco principal de poderes (frase “confere poderes”, “poderes para”, “podendo para tanto”, etc.).
- Se o bloco contiver `;` (ponto e vírgula): **quebrar obrigatoriamente** em múltiplos itens:
  - cada segmento entre `;` vira um item (trim), desde que represente uma ação/poder.
- Se um segmento contiver lista clara por vírgulas iniciando com verbos (ex.: “apresentar provas, atender solicitações, cumprir exigências”):
  - quebrar por vírgula **somente** quando cada parte iniciar com verbo/ação e fizer sentido independente.
- Se não houver separadores claros:
  - permitir 1 item com o parágrafo literal integral.
- Manter literalidade (permitido apenas remover quebras artificiais de linha).
- Se houver “Confissão de Dívidas” ou “Banco do Brasil”, garantir que apareça em pelo menos um item.

### 7) `descricao_poderes` — derivada apenas de `poderes_especificos`
- Construir uma descrição curta usando apenas termos/atos presentes em `poderes_especificos`.
- Não adicionar poderes não listados.

### 8) `fonte.fls` e `fonte.rotulo_documento`
- `fonte.fls`: extrair marcador explícito se existir (“fls.”, “[Pág.]”, “[[Folha]]”, ou marcador do pipeline como “L.:063 / P.:152”); senão `""`.
- `fonte.rotulo_documento`: usar epígrafe/título literal se existir; senão `""`.

### 9) Opcionais quando explícitos
- `local`: preencher se explícito; senão `""`.
- `restricoes_ou_limitacoes[]`: listar restrições explícitas; senão `[]`.
- `assinantes[]`: listar nomes de assinantes explícitos; senão `[]`.

## Quality Gates (anti-regressão)

### Gate A — Partes
- Se existir “OUTORGANTE(S)” no texto: `outorgantes` não pode ser vazio.
- Se existir “OUTORGADO(S)”/“PROCURADOR” no texto: `outorgados` não pode ser vazio.

### Gate B — Poderes
- Se existir “poderes”/“confere poderes”/“mandato”/“bastante procurador”: `poderes_especificos` e `descricao_poderes` não podem ficar vazios.

### Gate C — Poder especial
- Se existir “Confissão de Dívidas” ou “Banco do Brasil”: algum item em `poderes_especificos` deve conter literalmente esse trecho (ou parte inequívoca).

### Gate D — Fonte correta (obrigatório)
- `arquivo_origem` e `fonte.arquivo_md` devem ser basename `*.md` (sem caminho) e não podem apontar para o prompt.
- Se estiverem vazios, marcar `status="falha"` (não inventar).
