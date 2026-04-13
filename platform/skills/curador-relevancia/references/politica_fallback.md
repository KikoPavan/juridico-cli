# Política de Fallback e Limites de Segurança Jurídica

> Projeto: juridico-cli / skill: curador-relevancia | Versão: 1.0.0

---

## 1. Princípio Geral

A skill `curador-relevancia` opera como sistema de apoio à decisão — **não como substituto do operador jurídico**. Toda decisão curatorial está sujeita a revisão humana, especialmente em contextos sensíveis.

---

## 2. Hierarquia de Prioridade das Regras

```
1. Regras de Segurança (R01, R02, R03, R04, R05)   ← INVIOLÁVEIS
2. Regra de Duplicata (R10)                         ← Cautela
3. Regras de modo específico (R06–R12)
4. Fallback geral do modo (R13 ou R14)              ← Último recurso
```

As regras de segurança **nunca são sobrescritas** por nenhuma outra — nem pelo modo, nem por configurações externas.

---

## 3. Gatilhos de Fallback

### 3.1 Baixa Confiança de Classificação (`R03`)

**Gatilho:** `confianca_classificacao < 0.60`

**Comportamento:**
- Ação forçada: `revisar`
- `override_aplicado = true`
- `override_motivo` documenta o motivo
- Nenhuma ação de remoção ou compressão é aplicada

**Razão:** O curador não pode tomar decisão curatorial segura se não confia na classificação do tipo documental recebida do segmentador.

---

### 3.2 Tipo Documental Ausente (`R03`)

**Gatilho:** `document_type = null`

**Comportamento:** Idêntico ao de baixa confiança — `revisar` obrigatório.

**Razão:** Sem tipo documental, é impossível aplicar regras de proteção adequadas.

---

### 3.3 Override por Sentença Confirmada (`R01`)

**Gatilho:** Curador inicial decide `remover` ou `resumir`, mas `impacto_sentenca_confirmado = true`

**Comportamento:**
- Decisão é sobrescrita para `manter`
- `override_aplicado = true`
- `compressao_sugerida = null`
- `override_motivo = "impacto_sentenca_confirmado=true: preservação obrigatória"`

---

### 3.4 Erro de Processamento Interno

**Gatilho:** Exceção Python não tratada durante `curar_peca()`

**Comportamento:**
- Ação: `revisar`
- Regra: `R_ERRO_PROCESSAMENTO`
- `audit_trail.erro` contém a mensagem de exceção (primeiros 120 chars)
- O pipeline não é interrompido — a peça é sinalizada para revisão humana

**Razão:** Robustez operacional. Um erro em uma peça não pode travar o processamento do processo inteiro.

---

### 3.5 Fallback Geral por Modo

**Modo `padrao` — R13:**
- Ação: `manter`
- Aplicado quando nenhuma regra específica disparou
- Conservador por design

**Modo `sintetico` — R14:**
- Ação: `resumir` com `cabecalho_apenas`
- Aplicado quando nenhuma regra específica disparou
- Compressivo por design

---

## 4. Limites de Segurança Jurídica

### O que o curador NUNCA faz

| Ação Proibida | Razão |
|---------------|-------|
| Remover tipos documentais protegidos | Violaria o contraditório e a ampla defesa |
| Remover provas documentais | Violaria direitos processuais fundamentais |
| Descartar peça com `impacto_sentenca_confirmado=true` | Risco de perda de fundamento de decisão |
| Remover peça com `confianca < 0.60` | Incerteza impede decisão segura |
| Remover sem justificativa | Violaria a trilha de auditoria obrigatória |
| Alterar o texto original de qualquer peça | Fora do escopo da skill |
| Inferir mérito jurídico | Fora do escopo da skill |

### O que o curador NÃO garante

| Limitação | Consequência |
|-----------|-------------|
| Não realiza análise de mérito | A relevância é operacional, não jurídica |
| Não detecta contradições entre peças | Análise semântica cruzada está fora do escopo |
| Não valida autenticidade documental | Documentos falsos podem ser marcados como relevantes |
| Não conhece estratégia do caso | Pode marcar como acessório algo estrategicamente importante |
| Não rastreia alterações após segmentação | Opera apenas nos dados recebidos |

---

## 5. Recomendações de Uso Seguro

### Para processos de alto risco (ex: execuções fiscais, processos criminais)

- Use sempre o modo `padrao`
- Revise manualmente todas as peças com `acao_curatorial = revisar`
- Não descarte automaticamente peças com `acao_curatorial = remover` sem revisão humana prévia

### Para triagem em massa (ex: mutirões de saneamento)

- O modo `sintetico` é adequado para uma primeira triagem
- Peças com `acao_curatorial = remover` podem ser movidas para pasta de revisão antes do descarte definitivo
- Nunca descartar automaticamente sem período de quarentena

### Para integração automatizada no pipeline

- Sempre executar `validar_saida.py` antes de passar para o `yaml/normalizador`
- Monitorar `sumario.alertas` para sinais críticos
- Implementar quarentena de peças `remover` por no mínimo 30 dias antes de exclusão permanente

---

## 6. Trilha de Auditoria — Compromissos

Toda decisão curatorial produz `audit_trail` com:

1. **`regra_aplicada`** — identificador único e rastreável da regra
2. **`gatilhos`** — condições exatas que ativaram a regra
3. **`relevancia_entrada`** e **`confianca_entrada`** — valores originais preservados
4. **`override_aplicado`** — se houve sobrescrita de segurança
5. **`timestamp`** — momento exato da decisão

Esses dados permitem auditoria completa de qualquer decisão curatorial em qualquer momento futuro.
