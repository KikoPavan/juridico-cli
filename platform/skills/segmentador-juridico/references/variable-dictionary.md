# Dicionário de Variáveis — segmentador-jurídico

**Versão:** 1.1.0

---

## 1. Campos do `metadata` (Envelope de Processo)

| Campo | Tipo | Obrigatório | Descrição | Valores Aceitos |
|-------|------|-------------|-----------|-----------------|
| `processo_id` | string | ✅ | Identificador único do processo | Ex: `1234567-89.2025.8.26.0000` |
| `total_pecas` | integer | ✅ | Número de peças identificadas | ≥ 1 |
| `gerado_por` | string | ✅ | Skill que gerou o envelope | Sempre `"segmentador-juridico"` |
| `timestamp` | string (ISO 8601) | ✅ | Timestamp da segmentação | Ex: `"2026-04-08T10:00:00Z"` |
| `source_file` | string | ✅ | Nome/caminho do arquivo de origem | Qualquer string não vazia |
| `total_pages` | integer \| null | ✅ | Total de páginas do documento | ≥ 1 ou null |
| `ocr_quality` | string | ❌ | Qualidade estimada do OCR | `"high"`, `"medium"`, `"low"`, `"unknown"` |
| `schema_version` | string (semver) | ✅ | Versão do schema | Ex: `"1.1.0"` |

---

## 2. Campos de Cada `Peca`

### 2.1. Identificação e classificação

| Campo | Tipo | Obrig. | Descrição |
|-------|------|:------:|-----------|
| `piece_id` | string | ✅ | ID único: `peca_NNN` ou `peca_NNNx` (filha) |
| `document_type` | string (enum) | ✅ | Tipo jurídico classificado (ver §3) |
| `document_type_confidence` | string (enum) | ✅ | Confiança: `"high"`, `"medium"`, `"low"` |

### 2.2. Localização no documento

| Campo | Tipo | Obrig. | Descrição |
|-------|------|:------:|-----------|
| `pages_start` | integer \| null | ✅ | Página de início (≥ 1 ou null) |
| `pages_end` | integer \| null | ✅ | Página de fim (≥ 1 ou null) |
| `pages_total` | integer \| null | ✅ | `pages_end - pages_start + 1` (null se extremo null) |
| `page_number_start` | integer \| null | ❌ | Alias aceito; preenche `pages_start` somente quando o campo canônico está vazio |
| `page_number_end` | integer \| null | ❌ | Alias aceito; preenche `pages_end` somente quando o campo canônico está vazio |

Em documentos agregados, `pages_start` e `pages_end` representam a página física na ordem dos
`judicial_locator`. O atributo interno `page` pode reiniciar em cada evento. Após materializar, a
esteira reconcilia limites e identidade com os marcadores efetivamente contidos na peça e registra
ajustes no `audit_trail`.

### 2.3. Conteúdo

| Campo | Tipo | Obrig. | Descrição |
|-------|------|:------:|-----------|
| `title` | string (≤ 200) | ✅ | Título inferido ou extraído |
| `summary` | string (≤ 1000) | ✅ | Resumo funcional (1-3 frases) |
| `impacto_sentenca_proposto` | string \| null (≤ 500) | ✅ | Impacto potencial na sentença |
| `text_excerpt` | string | ✅ | Trecho inicial (~200 chars) |
| `text` | string | ✅ | **Texto COMPLETO** da peça |
| `anchors` | array de `{label, page, process_number?, event?, document_code?}` | ✅ | Âncoras de delimitação e rastreabilidade (minItems: 1) |
| `observacoes` | string \| null | ❌ | Observações de auditoria (≤ 500 chars) |

### 2.4. Proveniência

| Campo | Tipo | Obrig. | Descrição |
|-------|------|:------:|-----------|
| `source_file` | string | ✅ | Herdado de `metadata.source_file` |
| `source_path` | string | ✅ | Caminho absoluto do arquivo de origem |
| `source_sha256` | string (64 hex) | ✅ | SHA-256 hex do arquivo de origem |
| `process_group_id` | string | ✅ | ID do grupo processual |
| `origin_piece_index` | integer ≥ 0 | ✅ | Índice ordinal da peça no documento |
| `process_number` / `processo_id` | string | ❌ | Número/identificador do processo, preservado quando disponível |
| `event` / `event_id` | string \| integer | ❌ | Evento processual, preservado quando disponível |
| `document_code` | string | ❌ | Código do documento no evento, preservado quando disponível |

### 2.5. Análise

| Campo | Tipo | Obrig. | Descrição |
|-------|------|:------:|-----------|
| `relevancia_estimada` | number 0.0–1.0 | ✅ | Score de relevância |
| `confianca_classificacao` | number 0.0–1.0 | ❌ | Confiança na classificação |
| `sinais_relevancia` | string[] | ❌ | Sinais de relevância detectados |
| `flags` | object | ❌ | Flags booleanas (ver §9) |
| `data_documento` | string \| null (ISO date) | ❌ | Data do documento |
| `autor` | string \| null | ❌ | Subscritor da peça |

---

## 3. Enum: `document_type`

| Valor | Nome Completo | Descrição |
|-------|---------------|-----------|
| `peticao_inicial` | Petição Inicial | Peça inaugural do processo |
| `contestacao` | Contestação | Resposta do réu à petição inicial |
| `replica` | Réplica | Resposta do autor à contestação |
| `decisao_interlocutoria` | Decisão Interlocutória | Decisão que não encerra o processo |
| `sentenca` | Sentença | Decisão que encerra o processo em 1ª instância |
| `acordao` | Acórdão | Decisão colegiada de tribunal |
| `despacho` | Despacho | Ato judicial de impulso processual |
| `procuracao` | Procuração | Instrumento de outorga de poderes |
| `mandato` | Mandato | Instrumento de mandato judicial |
| `contrato` | Contrato | Contrato particular juntado como documento |
| `escritura` | Escritura | Escritura pública (imóvel, hipoteca etc.) |
| `laudo_pericial` | Laudo Pericial | Resultado de perícia técnica |
| `parecer` | Parecer | Opinião técnica ou jurídica |
| `recurso` | Recurso (genérico) | Recurso não identificado especificamente |
| `agravo` | Agravo | Agravo (interno, regimental, de instrumento) |
| `apelacao` | Apelação | Recurso de apelação |
| `embargos_declaracao` | Embargos de Declaração | Embargos contra decisão/acórdão |
| `impugnacao` | Impugnação | Impugnação (à contestação, ao valor etc.) |
| `memoriais` | Memoriais | Memoriais finais das partes |
| `certidao` | Certidão | Certidão emitida por servidor/cartório |
| `ata` | Ata | Ata de audiência ou sessão |
| `oficio` | Ofício | Comunicação oficial entre órgãos |
| `intimacao` | Intimação | Ato de intimação da parte |
| `citacao` | Citação | Ato de citação do réu |
| `mandado` | Mandado | Mandado judicial (de citação, prisão etc.) |
| `termo` | Termo | Termo processual |
| `anexo` | Anexo / Documento | Documento anexado sem tipo específico |
| `comprovante` | Comprovante | Comprovante (pagamento, entrega etc.) |
| `capa_processo` | Capa do Processo | Folha inicial administrativa de autuação/identificação; não é peça jurídica profunda |
| `nao_classificado` | Não Classificado | Tipo não determinável — sempre com `observacoes` |

---

## 4. Enum: `document_type_confidence`

| Valor | Critério |
|-------|----------|
| `"high"` | 2 ou mais sinais primários convergentes |
| `"medium"` | 1 sinal primário + 1+ sinais secundários |
| `"low"` | Apenas sinais secundários |

---

## 5. Enum: `ocr_quality`

| Valor | Critério |
|-------|----------|
| `"high"` | < 5% de caracteres corrompidos |
| `"medium"` | 5–30% de ruído; texto legível com erros |
| `"low"` | > 30% de ruído; segmentação comprometida |
| `"unknown"` | Sem marcadores de página; qualidade não avaliável |

---

## 6. Formato de Âncoras (`anchors`)

Cada âncora é um **objeto** com `label` e `page`:

```json
{ "label": "cabecalho", "page": 1 }
{ "label": "PETIÇÃO INICIAL", "page": 1 }
{ "label": "pede deferimento", "page": 18 }
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `label` | string | Identificador legível da âncora |
| `page` | integer ≥ 1 | Página onde a âncora ocorre |
| `process_number` | string | Processo associado, quando disponível |
| `event` | string \| integer | Evento associado, quando disponível |
| `document_code` | string | Código documental associado, quando disponível |

`metadata.document_code` e `metadata.event` só representam o documento inteiro quando houver
consenso. Em processo agregado, permanecem nulos; os valores específicos ficam em cada peça.

---

## 7. Padrão de `piece_id`

| Padrão | Regex | Exemplo |
|--------|-------|---------|
| Principal | `peca_\d{3}` | `peca_001` |
| Filha | `peca_\d{3}[a-z]` | `peca_002a` |

---

## 8. Glossário

| Termo | Definição |
|-------|-----------|
| **Envelope de Processo** | Artefato JSON `{metadata, pecas[]}` produzido pelo segmentador |
| **peça lógica** | Unidade autônoma de documento jurídico dentro do envelope |
| **âncora** | Sinal textual/estrutural que marca o início, fim ou tipo de uma peça |
| **sinal primário** | Âncora de alta confiança que sugere um tipo de documento |
| **sinal secundário** | Âncora de suporte que confirma mas não determina o tipo |
| **curador-relevância** | Próxima etapa; avalia relevância das peças segmentadas |
| **dispatcher** | Etapa que roteia peças para a skill `extr-*` adequada |

---

## 9. Flags Booleanas

| Flag | Significado |
|------|-------------|
| `prova_documental` | Peça constitui prova documental do processo |
| `decisao_judicial` | Peça contém decisão de juiz ou tribunal |
| `representacao_processual` | Documento de representação (procuração, mandato) |
| `duplicata_suspeita` | Possível duplicata de outra peça no mesmo processo |
| `prazo_expirado` | Peça relacionada a prazo já transcorrido |
