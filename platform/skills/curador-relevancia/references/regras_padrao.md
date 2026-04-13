# Regras de Negócio — Modo `padrao`

> Detalhamento completo das regras aplicadas quando `modo=padrao`.
> Projeto: juridico-cli / skill: curador-relevancia | Versão: 1.0.0

---

## Filosofia do Modo `padrao`

O modo `padrao` é **conservador por design**. Seu objetivo é preservar o máximo possível de conteúdo processual relevante, descartando apenas o que é claramente irrelevante e estritamente inofensivo remover.

**Princípio central:** Na dúvida, manter. Peças marcadas como `revisar` ou `manter` nunca causam perda de informação processual crítica.

---

## Limiares de Operação

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `relevancia_manter` | `0.40` | Score mínimo para manutenção automática |
| `relevancia_remover` | `0.30` | Score máximo para descarte de removíveis |
| `confianca_minima` | `0.60` | Confiança mínima para classificação sem revisão |
| `paginas_resumir` | `3` | Páginas mínimas para compressão de acessórios |

---

## Cadeia de Regras (ordem de aplicação)

As regras são aplicadas **sequencialmente**. A primeira que disparar encerra a análise da peça.

### Fase 1 — Proteções Universais (sempre aplicadas primeiro)

#### R01 — Nuclear com Sentença Confirmada
- **Condição:** `impacto_sentenca_confirmado = true`
- **Ação:** `manter`
- **Justificativa:** Peça com impacto confirmado na sentença; preservação obrigatória em qualquer modo.
- **Override:** Sobrescreve qualquer decisão anterior do curador.

#### R04 — Prova Documental (flag)
- **Condição:** `flags.prova_documental = true`
- **Ação:** `manter`
- **Justificativa:** Prova documental é inviolável pelo princípio constitucional do contraditório e ampla defesa.
- **Nota:** Mesmo que `relevancia_estimada` seja baixa.

#### R05 — Representação Processual
- **Condição:** `flags.representacao_processual = true`
- **Ação:** `manter`
- **Justificativa:** Procurações e instrumentos de mandato são essenciais à validade do processo.

#### R02 — Tipo Documental Protegido
- **Condição:** `document_type` ∈ `{peticao_inicial, contestacao, sentenca, acordao, laudo_pericial, procuracao, recurso, ata_audiencia, decisao_interlocutoria}`
- **Ação:** `manter`
- **Justificativa:** Tipos documentais nucleares ao processo; nunca removíveis.

#### R10 — Duplicata Suspeita
- **Condição:** `flags.duplicata_suspeita = true`
- **Ação:** `revisar`
- **Justificativa:** Possível duplicata requer confirmação humana antes de qualquer descarte.
- **Risco de remoção direta:** Poderia descartar a cópia "verdadeira" por engano.

#### R03 — Fallback por Baixa Confiança
- **Condição:** `confianca_classificacao < 0.60` **OU** `document_type = null`
- **Ação:** `revisar`
- **Override:** Obrigatório; decisão é escalada para revisão humana independentemente da relevância.
- **Justificativa:** Incerteza de classificação impede decisão curatorial segura.

---

### Fase 2 — Regras Específicas do Modo `padrao`

#### R08 — Despacho de Expediente com Prazo Expirado
- **Condição:** `document_type = "despacho"` AND `relevancia_estimada < 0.30` AND `flags.prazo_expirado = true`
- **Ação:** `remover`
- **Justificativa:** Despachos de mero expediente com prazo expirado não têm conteúdo processual residual.
- **Cuidado:** Condições são cumulativas — todas precisam ser verdadeiras.

#### R09 — Certidão de Prazo Irrelevante
- **Condição:** `document_type = "certidao"` AND `relevancia_estimada < 0.30` AND `flags.prazo_expirado = true`
- **Ação:** `remover`
- **Justificativa:** Certidões de prazo expirado são meramente cartoriais e sem valor probatório residual.

#### R11 — Peça Acessória Longa
- **Condição:** `impacto_processual = "acessorio"` AND `paginas.total > 3`
- **Ação:** `resumir`
- **Compressão:** `resumo_1p`
- **Justificativa:** Peças acessórias longas adicionam ruído sem impacto no mérito; compressão preserva conteúdo essencial.

#### R06 — Alta Relevância Padrão
- **Condição:** `relevancia_estimada >= 0.40`
- **Ação:** `manter`
- **Justificativa:** Relevância acima do limiar padrão; manutenção integral.

---

### Fase 3 — Fallback Geral do Modo `padrao`

#### R13 — Fallback Conservador
- **Condição:** Nenhuma regra anterior disparou
- **Ação:** `manter`
- **Justificativa:** Modo padrão é conservador; peças sem regra específica são mantidas por segurança.

---

## Fluxograma de Decisão (modo `padrao`)

```
Peça recebida
│
├─ impacto_sentenca_confirmado = true? → MANTER (R01)
├─ flags.prova_documental = true? → MANTER (R04)
├─ flags.representacao_processual = true? → MANTER (R05)
├─ document_type em lista protegida? → MANTER (R02)
├─ flags.duplicata_suspeita = true? → REVISAR (R10)
├─ confianca < 0.60 ou tipo = null? → REVISAR (R03)
│
├─ despacho + relevancia < 0.30 + prazo_expirado? → REMOVER (R08)
├─ certidao + relevancia < 0.30 + prazo_expirado? → REMOVER (R09)
├─ acessorio + paginas > 3? → RESUMIR resumo_1p (R11)
├─ relevancia >= 0.40? → MANTER (R06)
│
└─ (nenhuma regra disparou) → MANTER (R13, fallback)
```

---

## Casos de Borda e Tratamento

| Caso | Tratamento | Justificativa |
|------|-----------|---------------|
| Peça com relevância 0.0 e tipo nulo | `revisar` (R03) | Tipo nulo = incerteza |
| Despacho com relevância 0.50 | `manter` (R06) | Acima do limiar; conservador |
| Procuração com relevância 0.20 | `manter` (R02) | Tipo protegido prevalece |
| Certidão com relevância 0.35 | `manter` (R06) | Acima do limiar de remoção |
| Certidão com relevância 0.20 sem prazo_expirado | `manter` (R13) | Condição de prazo não satisfeita |
| Peça sem `impacto_processual` | curador calcula via `relevancia_estimada` | Fallback de cálculo interno |

---

## Garantias do Modo `padrao`

1. **Nenhuma peça é removida sem justificativa** — regra R08/R09 exigem condições triplas.
2. **Tipos protegidos nunca são removidos** — R02 é universal e precedente.
3. **Incerteza nunca gera descarte** — R03 força `revisar` antes de qualquer remoção.
4. **Impacto confirmado na sentença é inviolável** — R01 sobrescreve qualquer decisão.
