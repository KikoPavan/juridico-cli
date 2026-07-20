## ADDED Requirements

### Requirement: Contestação Block Strategy Produces Only Schema-Permitted Properties
Quando a Extração por Blocos for acionada para `bundle_id="extr-contestacao-processo"`, o sistema SHALL usar uma estratégia própria (`ContestacaoBlockStrategy` ou equivalente) cujos blocos e consolidação produzem exclusivamente propriedades presentes em `platform/skills/extr-contestacao-processo/assets/contestacao_processo.schema.json` (`document_type`, `process_number`, `parties`, `representations`, `contestacao_identification`, `preliminares`, `merito`, `provas_e_requerimentos`, `pedidos_finais`, `anchors`).

#### Scenario: Consolidated result contains no petição-only fields
- **WHEN** a extração por blocos de contestação é executada para um documento real
- **THEN** o JSON consolidado não contém `peticao_identification`, `valor_da_causa`, `fatos`, `pedidos`, `pedidos_individualizados`, `tutela_urgencia`, `provas_requeridas` nem `riscos_ou_pontos_de_atencao`

#### Scenario: Consolidated result validates against the contestação schema
- **WHEN** o JSON consolidado de uma extração por blocos de contestação é validado contra `contestacao_processo.schema.json`
- **THEN** a validação não produz erro `Unevaluated properties are not allowed`

### Requirement: Contestação Blocks Derived From Schema and SKILL.md
Os blocos usados pela estratégia de contestação SHALL ser derivados das propriedades reais do schema de contestação e das regras descritas em `platform/skills/extr-contestacao-processo/SKILL.md` (identificação mínima, partes/representantes, preliminares, mérito/impugnações, provas e requerimentos, pedidos finais), e NÃO MUST reutilizar a definição de blocos de `extr-peticao-processo`.

#### Scenario: Preliminares block only requests preliminares-related content
- **WHEN** o bloco responsável por `preliminares` é processado
- **THEN** o prompt enviado ao modelo solicita apenas conteúdo relativo a preliminares, sem mencionar pedidos, tutela de urgência ou fatos de petição inicial

#### Scenario: Mérito block only requests mérito-related content
- **WHEN** o bloco responsável por `merito` é processado
- **THEN** o prompt enviado ao modelo solicita apenas argumentos de mérito/impugnação, sem mencionar campos exclusivos de petição inicial

### Requirement: Deterministic Fallback for Contestação Omits Absent Data Instead of Inventing It
Quando o fallback determinístico local da estratégia de contestação não encontrar conteúdo correspondente a preliminares, mérito ou pedidos finais no Markdown, o sistema SHALL retornar listas vazias para os campos correspondentes, e NÃO MUST preencher esses campos com conteúdo de petição inicial, texto fixo de caso real anterior, ou dado inferido não presente no documento.

#### Scenario: No preliminares section found returns empty list
- **WHEN** o Markdown de uma contestação não contém seção identificável de preliminares
- **THEN** o fallback determinístico retorna `preliminares` como lista vazia, sem inventar conteúdo

#### Scenario: Fallback never emits petição-shaped defaults
- **WHEN** o fallback determinístico de contestação é acionado por falha de um bloco
- **THEN** nenhum campo do resultado corresponde à estrutura de defaults usada pelo fallback de petição (`peticao_identification`, `valor_da_causa`, `tutela_urgencia`)

### Requirement: Official Contestação Validator Accepts Block-Mode Results
O resultado produzido pela extração por blocos de contestação SHALL passar na validação de `platform/skills/extr-contestacao-processo/scripts/validate_output.py` sem erros, para um documento de contestação real.

#### Scenario: Real contestação case validates via the official script
- **WHEN** `validate_output.py --input <resultado.json>` é executado sobre o resultado de uma extração por blocos de contestação bem-sucedida
- **THEN** o script reporta `OK` e código de saída `0`
