# **Reliability Report: extr-escritura-hipotecaria**

_Framework: ReliabilityBench v1.0_

## **1. Definição de Oráculo (Ground Truth)**

O sucesso da extração é definido pela paridade absoluta com o schema
`assets/escritura_hipotecaria.schema.json` e as regras de `_shared/extraction-base.md`.

## **2. Métricas de Resiliência**

### **A. Consistência de Extração (k=3)**

- **Teste:** Executar a extração do mesmo documento 3 vezes.
- **Critério:** O JSON de saída deve ser identicamente binário em 100% dos campos de "Valor" e "Gravame".
- **Falha:** Divergência aciona re-sumarização do contexto via `TurboQuant`.

### **B. Robustez Semântica (ε-Invariance)**

- **Teste:** Alterar a ordem das instruções no `SKILL.md` ou trocar sinônimos nas regras de "Literalidade".
- **Critério:** O agente não deve inferir dados ou omitir campos `null` obrigatórios, independentemente da variação do prompt.

### **C. Tolerância a Falhas (λ-Stability)**

- **Timeout:** Máximo de 15s para extração completa em Haiku 4.5.
- **Recuperação:** Em caso de falha de parsing JSON, o orquestrador deve injetar o erro no sistema e solicitar apenas a correção do bloco malformado (Partial Correction).

## **3. Guardrails de Memória (TurboQuant)**

- **Integridade de Vetor:** Verificação de similaridade cosseno entre o vetor original e o vetor quantizado.
- **Limite de Distorção:** Erro médio quadrático (MSE) inferior a 0.05 para garantir que "Hipoteca" não seja confundido com "Alienação" no banco de dados Qdrant.

## **4. Logs de Auditoria**

- Todo erro de orquestração deve ser registrado em `platform/logs/reliability.log` com o dump do prompt enviado e a resposta bruta do Haiku.
