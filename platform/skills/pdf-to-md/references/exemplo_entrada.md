# Exemplo de Entrada — pdf-to-md

Documento neutro e genérico usado como entrada de referência.
Não representa nenhum domínio especializado.

---

## Metadados do arquivo de exemplo

| Campo         | Valor                                        |
|---------------|----------------------------------------------|
| Nome fictício | `relatorio_manutencao_predial_2024.pdf`      |
| Páginas       | 4                                            |
| Tipo          | Relatório técnico de manutenção predial      |
| Origem        | Simulado para fins de teste da skill         |

---

## Conteúdo simulado (representação textual do PDF)

### Página 1

```
RELATÓRIO DE MANUTENÇÃO PREDIAL
Período: Janeiro a Março de 2024
Responsável: Equipe de Infraestrutura

1. INTRODUÇÃO

Este relatório apresenta as atividades de manutenção realizadas no
Edifício Central durante o primeiro trimestre de 2024. As intervenções
foram programadas conforme o Plano Anual de Manutenção (PAM) aprovado
em dezembro de 2023.

O objetivo é garantir a operacionalidade das instalações, a segurança
dos ocupantes e a preservação do patrimônio.
```

### Página 2

```
2. ATIVIDADES REALIZADAS

2.1 Manutenção Elétrica

Foram realizadas as seguintes intervenções no sistema elétrico:
• Substituição de 48 lâmpadas LED nos corredores do térreo e 1º andar
• Revisão do quadro de distribuição do bloco B
• Teste de carga nos grupos geradores (3 unidades)

2.2 Manutenção Hidráulica

• Limpeza das caixas d'água superior e inferior (capacidade: 30.000 L)
• Troca de registros com vazamento: 7 unidades no bloco A
• Desobstrução de ralos no estacionamento coberto
```

### Página 3

```
3. OCORRÊNCIAS NÃO PROGRAMADAS

12/01/2024 — Falha no elevador social (bloco A): acionamento da assistência
28/01/2024 — Infiltração no teto da sala 204: impermeabilização emergencial
15/02/2024 — Curto-circuito no DPS do bloco C: substituição imediata
03/03/2024 — Bomba de recalque parada: reparo e teste de funcionamento

4. INDICADORES

• Total de ordens de serviço abertas: 34
• Ordens concluídas no prazo: 31 (91,2%)
• Ordens em acompanhamento: 3
• Custo total do período: R$ 47.380,00
```

### Página 4

```
5. RECOMENDAÇÕES

1. Substituição preventiva do painel de controle do elevador social
   — estimativa: R$ 12.000,00

2. Vistoria completa na impermeabilização da cobertura do bloco B

3. Revisão do contrato de manutenção do sistema de climatização,
   com degradação de 18% em relação ao ano anterior

6. CONCLUSÃO

O primeiro trimestre de 2024 transcorreu dentro dos parâmetros esperados.
As metas preventivas foram atingidas em 91,2% dos casos.

Responsável técnico: Eng. Roberto Almeida — CREA-SP 123.456/D
```

---

## Comando de execução do exemplo

```bash
bash scripts/run_example.sh
```

O script gera um PDF sintético a partir deste conteúdo e executa
a conversão completa com validação do arquivo de saída.
