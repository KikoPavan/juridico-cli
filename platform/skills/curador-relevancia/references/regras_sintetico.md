# Regras de Negócio — Modo `sintetico`

> Detalhamento das regras aplicadas quando `modo=sintetico`.
> Projeto: juridico-cli / skill: curador-relevancia | Versão: 1.0.0

---

## Filosofia do Modo `sintetico`

O modo `sintetico` é **agressivo e orientado a eficiência**. Prioriza fortemente as peças de alto impacto, comprime acessórios e descarta o máximo de ruído processual possível sem violar as proteções jurídicas universais.

**Princípio central:** Redução máxima de contexto. Apenas o que importa para o resultado do processo merece atenção integral. Todo o resto é comprimido ou descartado — sempre com justificativa.

**Casos de uso ideais:**
- Processos com centenas de páginas
- Pré-análise rápida antes de distribuição para skills especializadas
- Geração de sumarização para pareceres ou relatórios gerenciais

---

## Limiares de Operação

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `relevancia_manter` | `0.60` | Score mínimo para manutenção automática (vs. 0.40 no padrão) |
| `relevancia_remover` | `0.40` | Score máximo para descarte de removíveis (vs. 0.30 no padrão) |
| `confianca_minima` | `0.60` | Mesmo limiar do modo padrão (segurança jurídica mantida) |
| `paginas_resumir` | `1` | Qualquer peça acessória é candidata à compressão |

---

## Cadeia de Regras (ordem de aplicação)

### Fase 1 — Proteções Universais (idênticas ao modo `padrao`)

As proteções universais **nunca são alteradas** pelo modo sintético:

| Regra | Condição | Ação |
|-------|----------|------|
| R01 | `impacto_sentenca_confirmado = true` | `manter` |
| R04 | `flags.prova_documental = true` | `manter` |
| R05 | `flags.representacao_processual = true` | `manter` |
| R02 | `document_type` em lista protegida | `manter` |
| R10 | `flags.duplicata_suspeita = true` | `revisar` |
| R03 | `confianca < 0.60` ou `type = null` | `revisar` |

> Ver detalhes em `regras_padrao.md` — Fase 1.

---

### Fase 2 — Regras Específicas do Modo `sintetico`

#### R08S — Despachos e Intimações
- **Condição:** `document_type ∈ {despacho, intimacao}` AND `relevancia_estimada < 0.40`
- **Ação:** `remover`
- **Justificativa:** Atos de mero expediente abaixo do limiar sintético — descartados por padrão.
- **Diferença do padrão:** Não exige `prazo_expirado=true`; limiar elevado para 0.40.

#### R09S — Certidões no Modo Sintético
- **Condição:** `document_type = "certidao"` AND `relevancia_estimada < 0.40`
- **Ação:** `remover`
- **Justificativa:** Certidões com baixa relevância são descartadas sem exigência de prazo_expirado.

#### R07 — Alta Relevância Sintética
- **Condição:** `relevancia_estimada >= 0.60`
- **Ação:** `manter`
- **Justificativa:** Apenas relevância elevada garante manutenção integral no modo sintético.

#### R12 — Acessório no Modo Sintético
- **Condição:** `impacto_processual ∈ {acessorio, irrelevante}` OU `0.40 <= relevancia < 0.60`
- **Ação:** `resumir`
- **Compressão:** `cabecalho_apenas`
- **Justificativa:** Peças na zona intermediária de relevância são comprimidas ao mínimo identificável.

---

### Fase 3 — Fallback Geral do Modo `sintetico`

#### R14 — Fallback Compressor
- **Condição:** Nenhuma regra anterior disparou
- **Ação:** `resumir` (não `manter` como no padrão)
- **Compressão:** `cabecalho_apenas`
- **Justificativa:** No modo sintético, a dúvida leva à compressão, não à manutenção.

---

## Comparação Modo `padrao` vs `sintetico`

| Aspecto | `padrao` | `sintetico` |
|---------|----------|-------------|
| Limiar para manter | 0.40 | 0.60 |
| Limiar para remover | 0.30 | 0.40 |
| Fallback geral | `manter` | `resumir` |
| Despachos | Remove com prazo_expirado | Remove sem prazo_expirado se rel < 0.40 |
| Certidões | Remove com prazo_expirado | Remove se rel < 0.40 |
| Acessórios | Resume se > 3 páginas | Resume qualquer acessório |
| Compressão padrão | `resumo_1p` | `cabecalho_apenas` |
| Nível de conservadorismo | Alto | Baixo |

---

## Fluxograma de Decisão (modo `sintetico`)

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
├─ (despacho|intimacao) + relevancia < 0.40? → REMOVER (R08S)
├─ certidao + relevancia < 0.40? → REMOVER (R09S)
├─ relevancia >= 0.60? → MANTER (R07)
├─ acessorio|irrelevante OU 0.40 <= rel < 0.60? → RESUMIR cabecalho_apenas (R12)
│
└─ (nenhuma regra disparou) → RESUMIR cabecalho_apenas (R14, fallback)
```

---

## Garantias de Segurança Jurídica no Modo `sintetico`

Mesmo no modo mais agressivo:

1. **Tipos documentais protegidos nunca são removidos** (R02 — universal)
2. **Provas documentais nunca são removidas** (R04 — universal)
3. **Representação processual é preservada** (R05 — universal)
4. **Impacto confirmado na sentença = manutenção obrigatória** (R01 — universal)
5. **Classificações incertas nunca são descartadas** — vão para `revisar` (R03)
6. **Toda remoção tem justificativa** — incluindo a indicação da regra aplicada

---

## Casos de Borda no Modo `sintetico`

| Caso | Tratamento | Regra |
|------|-----------|-------|
| Sentença com relevância 0.50 | `manter` | R02 (tipo protegido) |
| Despacho com relevância 0.55 | `resumir` (R12, zona intermediária) | R12 |
| Certidão com relevância 0.45 | `resumir` (R12) — acima de 0.40 | R12 |
| Peça sem tipo, rel. 0.80 | `revisar` (R03) — tipo nulo | R03 |
| Manifestação com rel. 0.65 | `manter` (R07) | R07 |
| Contrato sem flag prova | `manter` (rel >= 0.60 → R07) ou `resumir` | R07 ou R12 |
