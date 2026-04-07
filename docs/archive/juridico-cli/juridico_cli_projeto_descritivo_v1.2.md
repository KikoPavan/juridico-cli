> [!WARNING]
> **DOCUMENTO HISTÓRICO — NÃO É A FONTE PRINCIPAL DA ARQUITETURA**
> Este documento descreve uma arquitetura experimental (TurboQuant, ReliabilityBench, Mem0) que foi descartada.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# **juridico-cli**

**Projeto Descritivo e Estrutural v1.2**
_Arquitetura co-located · Memória Híbrida TurboQuant · Framework ReliabilityBench_

Versão 1.2 · Março 2026  
_Revisão: Integração de Resiliência e Otimização de Memória_

## **1. Visão Executiva**

O `juridico-cli` é um monorepo de processamento jurídico baseado em agentes
especializados. A v1.2 introduz a **Camada de Memória Híbrida**, que combina a
persistência do Mem0 com a compressão matemática do **TurboQuant**, permitindo alta
performance em hardware local.

| Atributo      | Valor                                           |
| :------------ | :---------------------------------------------- |
| Hardware alvo | i7-6700HQ · GTX 950M 4GB · WSL2/Ubuntu 24       |
| Memória       | Híbrida (Mem0 + TurboQuant Online Quantization) |
| Orquestração  | Router Duplo + ReliabilityBench Framework       |
| Deployment    | Google Antigravity Ready                        |

## **2. Arquitetura de Memória Híbrida**

[cite_start]Para suportar o volume de dados jurídicos no hardware disponível, o projeto utiliza três níveis de memória[cite: 418, 419]:

1. [cite_start]**Sessão (ADK):** Memória de trabalho de curto prazo para o loop ReAct atual[cite: 134, 196].
2. [cite_start]**Episódica (Mem0):** Persistência de experiências e aprendizados de extração entre sessões[cite: 120, 802].
3. **TurboQuant (Performance):** Todos os vetores são comprimidos em tempo real (Online Vector Quantization). Isso garante "Distorção Quase Ideal", reduzindo drasticamente o consumo de RAM sem perder a precisão dos termos jurídicos.

## **3. Orquestração e Resiliência (ReliabilityBench)**

A orquestração segue os princípios do **ReliabilityBench** para garantir estabilidade operacional no Antigravity:

- **Loop ReAct Puro:** Foco em Razão e Ação para minimizar falhas de estado.
- **Oráculo de Schema:** Validação determinística imediata após cada extração `extr-*`.
- **Métrica $R(k, \epsilon, \lambda)$:**
  - **Consistência ($k$):** Verificação de paridade em múltiplas execuções.
  - **Robustez ($\epsilon$):** Invariância contra mudanças nas instruções base (AMR).
  - **Tolerância ($\lambda$):** Backoff exponencial automático para limites de taxa e latência de rede.

## **4. Estrutura de Bundles Co-located**

Cada skill jurídica (ex: `extr-escritura-hipotecaria`) é autossuficiente e contém seu próprio agente, assets e scripts de validação. O `bundle_loader.py` injeta as regras transversais de `_shared/extraction-base.md` (Literalidade, Null Seguro e Moeda Literal) no início de cada chamada.
