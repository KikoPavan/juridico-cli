---
name: reconciler_core
agent: reconciler-cli
description: |
  Skill genérica do reconciler-cli para ler o input já normalizado em io.schema.json
  e produzir a saída também no formato io.schema.json, avaliando relações críticas
  de forma neutra, sem tese específica.
version: 0.2
target_schema: reconciler.schema.json
---

# SKILL GENÉRICA – NÚCLEO DO RECONCILER

## Escopo

Use estas instruções sempre que o reconciler-cli for acionado sem uma tese jurídica
específica (modo genérico). O objetivo é:

- ler um objeto `input` já organizado conforme o schema de entrada do reconciler;
- produzir um objeto `output` que respeite rigorosamente `reconciler.schema.json`;
- avaliar, para cada relação crítica, o estado atual da prova, sem assumir teses.

Esta skill **não** decide petições ou conclusões jurídicas definitivas; ela apenas
organiza fatos, relações e lacunas probatórias de forma estruturada.

---

## Entradas (visão conceitual)

Considere que o LLM recebe um objeto `input` com, no mínimo:

- `input.processo_meta`
- `input.contexto_caso`
- `input.contexto_relacoes`
  - incluindo `relacoes_criticas[*]` e `fatos_a_verificar` definidos pelo usuário
- `input.obrigacoes_imobiliarias` (saída do monetary-cli)
- `input.documentos_juntada`
- `input.eventos_processo`

Você **não altera** esse objeto; apenas o lê para construir o `output`.

---

## Saída (visão conceitual)

Você deve produzir um objeto `output` com, no mínimo:

- `output.versao` – ex.: `"reconciler-v1"`;
- `output.gerado_em` – timestamp, se possível;
- `output.origem` e `output.contexto_entrada` – metadados sobre arquivos usados;
- `output.relacoes_criticas` – lista obrigatória, 1 item para cada relação em
  `input.contexto_relacoes.relacoes_criticas[*]`;
- `output.notas_gerais` – observações globais;
- `output.checklist_global` – itens agregados (cartório / fora_cartorio), se aplicável.

Cada item de `output.relacoes_criticas[*]` deve respeitar **exatamente** o
subschema `RelacaoCritica` em `reconciler.schema.json`.

---

## Regras de preenchimento – `relacoes_criticas[*]`

Para cada relação crítica em `input.contexto_relacoes.relacoes_criticas[*]`:

1. Crie um objeto em `output.relacoes_criticas[*]` com:
   - `id_relacao`: copie o ID da entrada (ex.: `"R1"`);
   - `descricao_relacao`: descreva de forma objetiva o que está sendo investigado;
   - `status`: use **apenas**:
     - `"confirmado"`
     - `"contrariado"`
     - `"indicio_forte"`
     - `"indicio_fraco"`
     - `"nao_localizado_nos_registros"`
   - `nivel_prova_atual`: use **apenas**:
     - `"forte"`
     - `"relevante"`
     - `"fraca"`

2. Preencha, quando possível:
   - `titulo` – rótulo curto da relação;
   - `matriculas_envolvidas` – números de matrícula relevantes;
   - `obrigacoes_relacionadas` – IDs como `"7013:R.4"`;
   - `documentos_juntada_relacionados` – IDs como `"contrato_social_JKMG_2002"`;
   - `fontes_apoio[*]` – objetos com:
     - `tipo` (`registro_imobiliario`, `juntada`, `processo`, `outro`);
     - `referencia` (ex.: `"7013:R.4"`, `"collector_out_juntada.json:DOC_05"`);
     - `descricao` breve;
   - `fatos_registros_imobiliarios[*]` – fatos objetivos, cada um com:
     - `id_fato`, `descricao`;
     - opcionalmente: `id_obrigacao`, `matricula`, `fontes_registro`, `folhas_registro`;
   - `fatos_declarados_usuario[*]` – fatos alegados no contexto do usuário;
   - `lacunas_documentais[*]` – lacunas de prova, com impacto e documentos sugeridos;
   - `checklist_documentos` – checklist específico daquela relação;
   - `premissas_usuario[*]` – premissas relevantes declaradas no contexto;
   - `comentarios_reconciler` – síntese da situação daquela relação.

---

## Tratamento de fatos declarados pelo usuário

O reconciler **não pode ignorar** fatos que o usuário declara no contexto,
mesmo que o documento correspondente ainda não esteja no pipeline.

1. Para cada fato relevante que venha de `input.contexto_relacoes` ou de
   campos equivalentes de contexto do usuário, crie uma entrada em
   `fatos_declarados_usuario[*]` com:
   - `id_fato_usuario` – ex.: `"U1"`, `"U2"`;
   - `descricao` – a descrição literal ou parafraseada do que o usuário afirma;
   - `origem_contexto` – ex.: `"contexto_relacoes.json:R1"`;
   - `ligado_a_obrigacoes` – se souber, IDs das obrigações afetadas;
   - `observacao_reconciler` – como esse fato se encaixa (ou não) nas provas objetivas.

2. **Não rebaixar automaticamente** `status` ou `nivel_prova_atual` apenas porque
   o documento ainda não entrou no pipeline.  
   - Se o usuário afirma um fato relevante, e:
     - não há nenhum documento **contradizendo** esse fato, mas
     - o documento comprobatório ainda não foi processado,
   - então:
     - registre esse fato em `fatos_declarados_usuario[*]`;
     - crie uma ou mais `lacunas_documentais[*]` e/ou itens de `checklist_documentos`
       e/ou `checklist_global` solicitando os documentos faltantes;
     - avalie `status` e `nivel_prova_atual` principalmente com base na coerência
       global (documentos já existentes + narrativa do usuário), e não apenas pela
       ausência momentânea do documento.

3. Quando houver clara **contradição** entre o que o usuário afirma e o que consta
   dos registros, registre essa tensão em:
   - `observacao_reconciler` dentro de `fatos_declarados_usuario[*]`;
   - e, se necessário, em `comentarios_reconciler` da relação.

---

## Tratamento de lacunas e checklist

Use `lacunas_documentais` e `checklist_documentos` / `checklist_global` para
formalizar o que ainda falta obter:

- `lacunas_documentais[*]`:
  - descreva qual informação/documento falta;
  - indique `impacto_prova` (`baixo`, `medio`, `alto`, `critico`);
  - liste `documentos_sugeridos` (ex.: “certidão de inteiro teor da matrícula 905”).

- `checklist_documentos` (por relação) e `checklist_global` (nível geral):
  - separe em:
    - `cartorio` – diligências que exigem cartórios;
    - `fora_cartorio` – bancos, Receita Federal, empresas, etc.

**Importante:** lacuna documental **não significa** automaticamente “prova fraca”.
Ela indica o que ainda precisa ser juntado ou confirmado.

---

## Separação entre fatos e interpretação jurídica

- Foque em:
  - quem, quando, onde, quanto, qual matrícula, qual obrigação.
- Não discuta teses como nulidade, excesso de mandato, abuso de direito etc.;
  esses temas serão desenvolvidos por FIRAC/petition com base nas relações que
  você organizou.
