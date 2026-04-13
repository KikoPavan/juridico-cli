# Documentação Técnica — segmentador-jurídico

**Versão:** 1.0.0
**Pipeline:** juridico-cli
**Etapa:** 3 de 8 (PDF → convert → clean → **segmentador-jurídico** → curador-relevância → yaml/normalizador → dispatcher → extr-*)

---

## 1. Arquitetura de Decisão

### 1.1 Fluxo de Processamento

```
Markdown Limpo (entrada)
        │
        ▼
┌─────────────────────┐
│  1. Parse de        │  Extrai marcadores <!-- page: N -->
│     Metadados       │  e YAML front matter
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  2. Varredura de    │  Sinais primários + secundários
│     Âncoras         │  por janela deslizante
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  3. Clustering de   │  Agrupa âncoras próximas
│     Fronteiras      │  em candidatos de peça
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  4. Classificação   │  Aplica dicionário de tipos
│     por Tipo        │  e calcula confiança
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  5. Extração de     │  Preenche campos do schema
│     Campos          │  por peça
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  6. Validação e     │  Verifica contra
│     Serialização    │  output-schema.json
└────────┬────────────┘
         │
         ▼
JSON + Resumo Técnico (saída)
```

### 1.2 Estratégia de Janela Deslizante

A varredura é feita com janela de **3 páginas** (atual + 1 anterior + 1 posterior) para evitar
falsos positivos em páginas com ruído. Um sinal isolado em página única só eleva a confiança
se confirmado por sinal na próxima página.

---

## 2. Catálogo de Sinais de Âncora

### 2.1 Sinais Primários (peso: 2)

| Sinal | Padrão | Tipo Sugerido |
|-------|--------|---------------|
| `PETIÇÃO INICIAL` | Literal + maiúsculas | `peticao_inicial` |
| `CONTESTAÇÃO` | Literal + maiúsculas | `contestacao` |
| `RÉPLICA` / `IMPUGNAÇÃO` | Literal | `replica` / `impugnacao` |
| `SENTENÇA` | Literal, início de parágrafo | `sentenca` |
| `ACORDÃO` | Literal | `acordao` |
| `DECISÃO INTERLOCUTÓRIA` | Literal | `decisao_interlocutoria` |
| `DESPACHO` | Sozinho em linha | `despacho` |
| `PROCURAÇÃO` / `INSTRUMENTO DE MANDATO` | Literal | `procuracao` / `mandato` |
| `EXCELENTÍSSIMO SENHOR` | Fórmula de endereçamento | Depende de contexto |
| `Publique-se. Intime-se.` | Fórmula de encerramento judicial | `sentenca` ou `despacho` |
| `pede e espera deferimento` | Fórmula de encerramento petição | `peticao_*` ou `recurso` |
| `APELAÇÃO` / `AGRAVO` | Literal + maiúsculas | `apelacao` / `agravo` |
| `EMBARGOS DE DECLARAÇÃO` | Literal | `embargos_declaracao` |

### 2.2 Sinais Secundários (peso: 1)

| Sinal | Descrição |
|-------|-----------|
| Quebra de página + linha em maiúsculas | Forte indício de início de peça |
| `Processo nº` / `Autos nº` / `Protocolo nº` | Referência processual |
| `REQUERENTE:` / `AUTOR:` / `RÉU:` / `REQUERIDO:` | Qualificação de partes |
| `OAB/[UF] [número]` | Assinatura de advogado |
| Data isolada em formato `DD/MM/AAAA` | Pode marcar encerramento |
| `Vistos.` / `Vistos e relatados.` | Abertura de decisão |
| `DO MÉRITO` / `DOS FATOS` / `DO DIREITO` | Estrutura de peça processual |

---

## 3. Matriz de Classificação por Tipo

| `document_type` | Sinais Primários Necessários | Contexto Confirmatório |
|-----------------|------------------------------|------------------------|
| `peticao_inicial` | `PETIÇÃO INICIAL` ou `EXCELENTÍSSIMO` + estrutura I/II/III | Ausência de número de processo já aberto |
| `contestacao` | `CONTESTAÇÃO` | Referência ao número do processo |
| `replica` | `RÉPLICA` | Após contestação nos autos |
| `sentenca` | `SENTENÇA` ou `Vistos.` + `Dispositivo` | Presença de `Publique-se. Intime-se.` |
| `decisao_interlocutoria` | `DECISÃO` ou `Vistos.` sem dispositivo final | Sem `Publique-se. Intime-se.` |
| `despacho` | `DESPACHO` + assinatura de juiz | Ausência de fundamentação extensa |
| `procuracao` | `PROCURAÇÃO` ou `OUTORGANTE`/`OUTORGADO` | Poderes descritos + assinatura |
| `mandato` | `INSTRUMENTO DE MANDATO` | Similar à procuração |
| `recurso` | `RECURSO` + tipo específico ausente | Genérico para recursos não identificados |
| `apelacao` | `APELAÇÃO` | Referência ao processo de origem |
| `agravo` | `AGRAVO` | Tipo de agravo pode ser refinado |
| `embargos_declaracao` | `EMBARGOS DE DECLARAÇÃO` | Referência à decisão embargada |
| `laudo_pericial` | `LAUDO` + `PERITO` | Estrutura técnica |
| `certidao` | `CERTIDÃO` ou `CERTIFICO` | Assinatura de servidor |
| `anexo` | Ausência de sinal primário + referência como doc. | Posição no final da peça antecedente |
| `nao_classificado` | Nenhum sinal primário convergente | — |

---

## 4. Regras de Fallback

### 4.1 OCR com Ruído Elevado

Quando `ocr_quality == "low"` ou quando página contém >30% de caracteres não-alfanuméricos:
1. Ignorar texto da página para classificação
2. Usar apenas marcadores de página e padrão estrutural (posição relativa)
3. Registrar em `observacoes`: `"OCR degradado na página N — classificação por sinal estrutural"`

### 4.2 Documento Sem Marcadores de Página

1. Estimar páginas por blocos de ~3000 caracteres
2. Definir `ocr_quality: "unknown"` nos metadados
3. Usar contagem estimada nos campos `pages_start` / `pages_end`
4. Registrar nos `notes` do `segmentation_meta`

### 4.3 Tipo Ambíguo

Quando dois tipos têm pontuação igual:
1. Preferir o tipo de maior especificidade (ex: `sentenca` > `decisao_interlocutoria`)
2. Registrar alternativa em `observacoes`: `"Alternativa considerada: [tipo]. Critério: [razão]."`

### 4.4 Documento com Uma Única Peça

Retornar array `pieces` com 1 elemento. Nunca omitir o JSON ou retornar objeto sem array.

### 4.5 Peças Aninhadas

Quando uma peça contém sub-documentos autônomos (ex: procuração dentro de petição):
- Criar peça filha com sufixo: `peca_001a`, `peca_001b`
- A peça pai pode ter range de páginas que inclui a filha
- Registrar em `observacoes` da peça pai: `"Contém sub-peça: peca_001a"`

---

## 5. Integração no Pipeline juridico-cli

### 5.1 Contrato de Interface

**Entrada (do `clean`):**
```
Content-Type: text/markdown
Formato: Markdown + <!-- page: N --> + YAML front matter opcional
```

**Saída (para `curador-relevância`):**
```
Content-Type: application/json
Schema: assets/output-schema.json v1.0.0
```

### 5.2 Campos Consumidos pela Próxima Etapa

| Campo | Consumidor | Uso |
|-------|------------|-----|
| `piece_id` | curador-relevância, dispatcher | Identificação e rastreamento |
| `document_type` | dispatcher | Roteamento para skill `extr-*` correta |
| `document_type_confidence` | curador-relevância | Filtro de qualidade |
| `pages_start` / `pages_end` | curador-relevância | Janela de texto para análise |
| `impacto_sentenca_proposto` | curador-relevância | Score de relevância |
| `anchors` | yaml/normalizador | Rastreabilidade de auditoria |

### 5.3 Mapeamento dispatcher → extr-*

| `document_type` | Skill Destino |
|-----------------|---------------|
| `peticao_inicial` | `extr-peticao-inicial` |
| `contestacao` | `extr-contestacao` |
| `sentenca` | `extr-decisao` |
| `decisao_interlocutoria` | `extr-decisao` |
| `procuracao` | `extr-procuracao` |
| `escritura` | `extr-escritura-imovel` |
| `nao_classificado` | `extr-processo-completo` (fallback) |

---

## 6. Considerações de Performance

- **Documentos grandes (>100 páginas):** processar em blocos de 50 páginas com overlap de 2 páginas
- **Lotes heterogêneos:** processar arquivo por arquivo; não misturar contexto entre arquivos
- **Tempo estimado:** ~2-5 segundos por página (dependente do modelo LLM utilizado)
- **Custo de tokens:** estimativa de 500-1500 tokens de entrada por página + ~300 tokens de saída por peça

---

## 7. Limitações Conhecidas

1. **Documentos em colunas múltiplas:** OCR pode gerar texto intercalado; segmentação será imprecisa
2. **Documentos manuscritos:** sinais textuais não detectáveis; retornar `nao_classificado`
3. **Peças sem cabeçalho formal:** decisões interlocutórias informais podem ser confundidas com despachos
4. **Idioma:** calibrado exclusivamente para Português Brasileiro (direito processual civil/trabalhista)
5. **Jurisdição:** otimizado para TJSP, STJ e TRTs; outras jurisdições podem ter variações terminológicas

---

## 8. Rastreabilidade e Auditoria

Cada peça deve registrar no mínimo:
- 1 âncora de página de início (`page:N`)
- 1 âncora textual de início
- 1 âncora de encerramento (quando identificável)

O campo `anchors` é a trilha de auditoria primária. O campo `observacoes` é o log secundário
para decisões não-óbvias.
