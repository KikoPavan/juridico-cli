# Dicionário de Variáveis — curador-relevancia

> Referência completa de todos os campos de entrada e saída utilizados pela skill `curador-relevancia`.
> Versão: 1.0.0 | Projeto: juridico-cli

---

## 1. Campos de Entrada (`schema_entrada.json`)

### `metadata`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `processo_id` | string | ✅ | Identificador único do processo judicial. Ex: `1234567-89.2024.8.26.0000` |
| `total_pecas` | integer | ✅ | Quantidade total de peças na lista |
| `gerado_por` | string | ✅ | Deve ser `"segmentador-juridico"` |
| `timestamp` | string (date-time) | ✅ | ISO 8601 da geração da entrada |
| `modo_curadoria` | enum | ❌ | `"padrao"` ou `"sintetico"`. Padrão: `"padrao"` |
| `versao_schema` | string | ❌ | Versão do schema usado. Padrão: `"1.0.0"` |

### `pecas[*]` — por peça

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `piece_id` | string | ✅ | ID único da peça no processo. Pattern: `[a-zA-Z0-9_-]+` |
| `document_type` | string\|null | ✅ | Tipo documental classificado (ver lista abaixo) |
| `relevancia_estimada` | float [0,1] | ✅ | Score de relevância estimado pelo segmentador |
| `confianca_classificacao` | float [0,1] | ❌ | Confiança na classificação do tipo. Padrão: `1.0` |
| `impacto_processual` | enum\|null | ❌ | `"nuclear"`, `"relevante"`, `"acessorio"`, `"irrelevante"` |
| `impacto_sentenca_confirmado` | boolean | ❌ | Se `true`, peça preservada obrigatoriamente. Padrão: `false` |
| `paginas.inicio` | integer | ✅ | Página inicial da peça no documento original |
| `paginas.fim` | integer | ✅ | Página final da peça |
| `paginas.total` | integer | ❌ | Total de páginas da peça |
| `sinais_relevancia` | string[] | ❌ | Lista de sinais jurídicos identificados pelo segmentador |
| `flags.prova_documental` | boolean | ❌ | Peça é prova documental — remoção vedada. Padrão: `false` |
| `flags.decisao_judicial` | boolean | ❌ | Peça é ato decisório judicial. Padrão: `false` |
| `flags.representacao_processual` | boolean | ❌ | Peça representa parte (procuração etc). Padrão: `false` |
| `flags.duplicata_suspeita` | boolean | ❌ | Segmentador detectou possível duplicata. Padrão: `false` |
| `flags.prazo_expirado` | boolean | ❌ | Prazo associado à peça já expirou. Padrão: `false` |
| `texto_preview` | string\|null | ❌ | Trecho inicial da peça (até 500 chars) para contexto |
| `data_documento` | string\|null | ❌ | Data do documento (ISO date: `YYYY-MM-DD`) |
| `autor` | string\|null | ❌ | Autor ou subscritor identificado da peça |
| `pages_start` / `pages_end` | integer\|null | ❌ | Paginação canônica; aliases `page_number_start` / `page_number_end` preenchem somente valores vazios |
| `process_number` / `processo_id` | string\|null | ❌ | Identidade do processo preservada |
| `event` / `event_id` | string\|integer\|null | ❌ | Evento processual preservado |
| `document_code` | string\|null | ❌ | Código documental preservado |
| `anchors` | array | ❌ | Âncoras preservadas e enriquecidas com identidade judicial disponível |

#### Valores possíveis de `document_type`

| Valor | Descrição | Proteção |
|-------|-----------|----------|
| `peticao_inicial` | Petição inicial da ação | 🔒 Protegido |
| `contestacao` | Contestação da parte ré | 🔒 Protegido |
| `sentenca` | Sentença de mérito | 🔒 Protegido |
| `acordao` | Acórdão de tribunal | 🔒 Protegido |
| `laudo_pericial` | Laudo pericial técnico | 🔒 Protegido |
| `procuracao` | Instrumento de procuração | 🔒 Protegido |
| `recurso` | Recurso (apelação, agravo etc) | 🔒 Protegido |
| `ata_audiencia` | Ata de audiência | 🔒 Protegido |
| `decisao_interlocutoria` | Decisão interlocutória | 🔒 Protegido |
| `despacho` | Despacho de mero expediente | 🗑️ Removível |
| `certidao` | Certidão cartorária | 🗑️ Removível |
| `intimacao` | Intimação de prazo | 🗑️ Removível |
| `documento_prova` | Documento probatório | Via flag |
| `contrato` | Contrato ou instrumento | Via flag |
| `manifestacao` | Manifestação/impugnação | Normal |
| `null` | Não classificado | → revisar |

#### Valores possíveis de `sinais_relevancia`

| Sinal | Significado |
|-------|-------------|
| `objeto_processual` | Define o objeto da ação |
| `pedido_expresso` | Contém pedido formal |
| `fundamentacao_legal` | Tem fundamentação legal relevante |
| `prova_documental` | É ou contém prova documental |
| `contraditorio` | Essencial ao contraditório |
| `representacao_processual` | Representa parte no processo |
| `decisao_judicial` | É ato decisório |
| `valor_causa` | Define ou contesta valor da causa |
| `duplo_grau` | Relacionado a recurso |
| `tese_defesa` | Contém tese de defesa |
| `fundamentacao_tecnica` | Laudo ou avaliação técnica |
| `prazo_expirado` | Prazo vencido sem efeito |
| `documento_desconhecido` | Não identificado pelo segmentador |

---

## 2. Campos de Saída (`schema_saida.json`)

### `metadata`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `processo_id` | string | Mesmo valor da entrada |
| `modo_aplicado` | enum | Modo efetivamente usado: `"padrao"` ou `"sintetico"` |
| `timestamp` | string (date-time) | Momento da execução da curadoria |
| `versao_schema` | string | `"1.0.0"` |
| `gerado_por` | string | `"curador-relevancia"` |
| `duracao_ms` | integer\|null | Tempo de processamento em milissegundos |

### `curadoria[*]` — por peça

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `piece_id` | string | Mesmo ID da entrada |
| `document_type` | string\|null | Tipo herdado da entrada |
| `acao_curatorial` | enum | **Decisão do curador** (ver tabela abaixo) |
| `modo_aplicado` | enum | Modo que gerou esta decisão |
| `justificativa_curta` | string (≤120) | Razão objetiva e auditável da decisão |
| `impacto_processual` | enum | Classificação final de impacto (ver tabela) |
| `impacto_sentenca_confirmado` | boolean | Herdado ou confirmado pelo curador |
| `prioridade` | integer [1-5] | Prioridade de processamento (1=alta) |
| `compressao_sugerida` | enum\|null | Tipo de compressão, se `acao=resumir` |
| `encaminhamento` | string\|null | Skill `extr-*` destino sugerida |
| `audit_trail` | object | Trilha de auditoria da decisão |
| `pages_start` / `pages_end` | integer\|null | Paginação canônica preservada |
| `process_number`, `event`, `document_code` | escalares\|null | Identidade judicial preservada |
| `text`, `anchors` | string, array | Conteúdo e âncoras preservados sem perda |

#### `acao_curatorial` — Valores e Significados

| Valor | Significado | Condição típica |
|-------|-------------|-----------------|
| `manter` | Preservar integralmente | Nuclear, protegida, alta relevância |
| `resumir` | Comprimir conforme `compressao_sugerida` | Acessório longo ou modo sintético |
| `remover` | Descartar (com justificativa) | Irrelevante, expirado, duplicata |
| `revisar` | Escalar para revisão humana | Incerteza, baixa confiança, tipo nulo |

#### `impacto_processual` — Valores e Significados

| Valor | Significado |
|-------|-------------|
| `nuclear` | Determina o resultado do processo |
| `relevante` | Influencia significativamente |
| `acessorio` | Complementar; não altera mérito |
| `irrelevante` | Sem impacto identificável |

Para `peticao_inicial`, `contestacao`, `decisao`/`decisao_interlocutoria`,
`sentenca` e `recurso`, o fallback mínimo é `relevante`; um valor `nuclear`
existente nunca é rebaixado.

#### `compressao_sugerida` — Valores

| Valor | Significado |
|-------|-------------|
| `resumo_1p` | Resumo em até 1 página |
| `cabecalho_apenas` | Preservar apenas cabeçalho/identificação |
| `metadado_apenas` | Preservar apenas metadados estruturais |
| `null` | Sem compressão (ação não é `resumir`) |

#### `encaminhamento` — Skills destino

| Valor | Skill | Peças típicas |
|-------|-------|---------------|
| `extr-pedidos` | Extrator de pedidos | peticao_inicial, contestacao, recurso |
| `extr-partes` | Extrator de partes | procuracao, peticao_inicial |
| `extr-decisao` | Extrator de decisões | sentenca, acordao, laudo_pericial |
| `extr-prova` | Extrator de prova | documento_prova, contrato |
| `extr-prazos` | Extrator de prazos | certidao, intimacao, despacho |
| `null` | Sem encaminhamento | remover, revisar sem tipo |

`capa_processo` é peça administrativa: por padrão recebe `acao_curatorial: remover`,
`impacto_processual: irrelevante`, prioridade 5 e `encaminhamento: null`. Se houver
`impacto_sentenca_confirmado: true`, a proteção de preservação prevalece, mas o tipo continua
sem encaminhamento para extrator profundo.

Tipos sem rota `extr-*` reconhecida, inclusive `nao_classificado`, recebem revisão segura,
impacto no máximo `acessorio` quando não há impacto confirmado e `encaminhamento: null`.
Um `document_code` como `PED HABILIT1` é preservado para auditoria, mas não cria subtipo nem
extrator implicitamente.

### `audit_trail`

| Campo | Tipo | Descrição |
| ------- | ------ | ----------- |
| `regra_aplicada` | string | ID da regra que determinou a ação (ex: `R01_nuclear_sentenca_confirmado`) |
| `gatilhos` | string[] | Condições que ativaram a regra |
| `relevancia_entrada` | float\|null | Score de relevância recebido do segmentador |
| `confianca_entrada` | float\|null | Confiança de classificação recebida |
| `override_aplicado` | boolean | Se uma regra de segurança sobrescreveu a decisão inicial |
| `override_motivo` | string\|null | Razão do override, se aplicado |
| `timestamp` | string (date-time) | Momento da decisão |
| `erro` | string\|null | Mensagem de erro, se ocorreu |

### `sumario`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `total_entrada` | integer | Total de peças recebidas |
| `total_manter` | integer | Peças com ação `manter` |
| `total_resumir` | integer | Peças com ação `resumir` |
| `total_remover` | integer | Peças com ação `remover` |
| `total_revisar` | integer | Peças com ação `revisar` |
| `taxa_retencao` | float | Proporção de peças mantidas integralmente |
| `pecas_nucleares` | integer | Peças com `impacto_processual=nuclear` |
| `alertas` | object[] | Avisos e erros gerados durante a curadoria |

---

## 3. Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CURADOR_MODO` | `padrao` | Modo de curadoria padrão quando não especificado |

---

## 4. Catálogo de Regras

| Regra ID | Nome | Modo | Ação |
|----------|------|------|------|
| `R01_nuclear_sentenca_confirmado` | Nuclear confirmado | Universal | manter |
| `R02_tipo_documental_protegido` | Tipo protegido | Universal | manter |
| `R03_fallback_baixa_confianca` | Baixa confiança | Universal | revisar |
| `R04_prova_documental_protegida` | Flag prova | Universal | manter |
| `R05_representacao_processual_protegida` | Flag representação | Universal | manter |
| `R06_padrao_alta_relevancia` | Alta relevância | padrao | manter |
| `R07_sintetico_alta_relevancia` | Alta relevância | sintetico | manter |
| `R08_despacho_expediente_prazo_expirado` | Despacho vencido | padrao | remover |
| `R08S_sintetico_despacho_intimacao` | Despacho/intimação | sintetico | remover |
| `R09_certidao_prazo_irrelevante` | Certidão vencida | padrao | remover |
| `R09S_sintetico_certidao` | Certidão | sintetico | remover |
| `R10_duplicata_suspeita` | Duplicata | Universal | revisar |
| `R11_padrao_acessorio_longo` | Acessório longo | padrao | resumir |
| `R12_sintetico_acessorio_comprimido` | Acessório | sintetico | resumir |
| `R13_padrao_fallback_geral` | Fallback geral | padrao | manter |
| `R14_sintetico_fallback_geral` | Fallback geral | sintetico | resumir |
| `R_ERRO_PROCESSAMENTO` | Erro interno | Universal | revisar |
