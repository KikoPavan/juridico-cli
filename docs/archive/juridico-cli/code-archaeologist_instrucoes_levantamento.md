> [!NOTE]
> **DOCUMENTO AUXILIAR — INSTRUÇÃO DE FERRAMENTA**
> Instruções operacionais para o agente `code-archaeologist`. Não é fonte de arquitetura.
> **Fonte canônica:** `docs/architecture/juridico_cli_arquitetura_consolidada_corrigida_v2.md`

---

# Instruções de Levantamento do Estado Atual — `code-archaeologist`

## Objetivo
Executar um levantamento técnico completo, fiel e auditável do estado atual do projeto `juridico-cli`, produzindo um **espelho do que existe hoje**. O resultado servirá de base para reformulação posterior envolvendo:

1. atualização do método de uso de **skills**;
2. implantação de **Arquiteturas Recursivas (RLM)**;
3. implantação de **memória**.

Nesta etapa, o agente **não deve propor arquitetura futura**, **não deve corrigir o projeto** e **não deve preencher lacunas por suposição**.

---

## Regra central de atuação
O agente deve trabalhar como um arqueólogo técnico do código e da documentação, identificando **apenas o que está comprovado por evidência concreta**.

Toda afirmação deve ser sustentada por evidência observável em:
- arquivos;
- diretórios;
- código-fonte;
- configs;
- prompts;
- skills;
- schemas;
- contratos de entrada e saída;
- scripts de execução;
- documentação.

Quando algo não puder ser comprovado, classificar explicitamente como **não comprovado**.

---

## Escopo do levantamento
O agente deve levantar, no mínimo, os itens abaixo.

### 1. Visão geral do projeto
Levantar:
- objetivo funcional atual do projeto;
- macroarquitetura existente;
- organização por apps, pipelines, agentes, módulos e utilitários;
- fronteiras entre processamento, ingestão, pesquisa, jurídico e suporte.

### 2. Estrutura física e lógica
Mapear:
- árvore dos diretórios relevantes;
- localização dos apps, pipelines, agentes, prompts, skills, schemas, loaders, artefatos e arquivos executáveis;
- separações existentes entre partes do sistema;
- zonas legadas e zonas já migradas.

### 3. Inventário dos componentes
Para cada componente relevante, levantar:
- nome;
- caminho;
- função atual;
- entradas;
- saídas;
- dependências;
- modo de acionamento;
- estágio real de implementação.

Incluir, se existirem:
- apps;
- pipelines;
- collectors;
- loaders;
- converters;
- cleaners;
- analyzers;
- validadores;
- jobs;
- scripts auxiliares;
- registries;
- prompts;
- skills;
- configs;
- schemas;
- bancos e índices;
- mecanismos de persistência.

### 4. Fluxo real ponta a ponta
Descrever o fluxo efetivo atual, do input ao output.

Levantar:
- origem dos arquivos;
- transformação por etapa;
- staging intermediário;
- pontos manuais;
- dependências entre etapas;
- caminhos de input/output;
- artefatos gerados;
- validações;
- persistência;
- carga final;
- pontos de quebra do fluxo.

Diferenciar claramente:
- o que está automatizado;
- o que é parcial;
- o que depende de ação manual;
- o que está apenas estruturado, mas não operacionalmente integrado.

### 5. Estado atual do uso de skills
Fazer inventário detalhado do uso de skills no projeto.

Levantar:
- onde há skills;
- como são definidas;
- como são chamadas;
- por quais agentes ou fluxos;
- dependências com prompts, configs e execução;
- limitações do modelo atual;
- inconsistências de padrão;
- ausência de skills onde seriam esperadas;
- pontos de acoplamento que dificultem futura reformulação.

### 6. Estado atual de memória
Levantar de forma explícita a existência ou ausência de mecanismos de memória, incluindo:
- memória de curto prazo;
- memória de sessão;
- memória persistente;
- cache;
- vetores;
- armazenamento contextual;
- estado compartilhado entre agentes;
- histórico reaproveitável;
- registries de execução;
- mecanismos equivalentes.

Se não houver implementação concreta, declarar isso claramente.

### 7. Aderência entre plano/documentação e implementação real
Comparar o que está descrito em planos e documentação com o que existe de fato no projeto.

Para cada ponto relevante, classificar como:
- aderente;
- parcialmente aderente;
- não aderente;
- não verificável.

### 8. Bloqueios para evolução futura
Sem propor solução, levantar:
- pontos que dificultam atualização do método de skills;
- pontos que dificultam implantação de RLM;
- pontos que dificultam implantação de memória;
- acoplamentos rígidos;
- ausência de contratos claros;
- ausência de estados intermediários reaproveitáveis;
- ausência de observabilidade e rastreabilidade;
- dependências manuais críticas.

### 9. Ativos reaproveitáveis
Listar o que pode ser reaproveitado na futura reformulação, como:
- módulos úteis;
- prompts;
- skills;
- schemas;
- contratos;
- registries;
- validadores;
- loaders;
- collectors;
- convenções já estáveis.

### 10. Componentes que exigem refatoração
Listar os componentes que, pelo estado atual, exigem refatoração para suportar:
- novo método de skills;
- RLM;
- memória;
- fluxo unificado;
- contratos consistentes;
- execução auditável.

---

## Classificação obrigatória
Toda análise deve usar explicitamente uma destas classificações:
- **implementado**
- **parcial**
- **manual**
- **legado**
- **inexistente**
- **não comprovado**

Não usar termos vagos no lugar dessas classificações quando estiver avaliando componentes, fluxos ou capacidades.

---

## Regras de evidência
Sempre que afirmar algo, o agente deve:
- indicar o arquivo, diretório, módulo, config ou artefato que sustenta a afirmação;
- diferenciar evidência direta de inferência técnica;
- não transformar hipótese em fato;
- apontar quando a documentação diverge da implementação.

---

## Restrições
O agente **não deve**:
- desenhar arquitetura futura;
- propor plano de migração;
- sugerir melhorias;
- reescrever componentes;
- corrigir o projeto;
- assumir intenção não comprovada;
- declarar como existente algo apenas planejado.

---

## Estrutura obrigatória da saída
O relatório final deve ser salvo em Markdown e conter exatamente esta estrutura:

# Espelho do Estado Atual do Projeto `juridico-cli`

## 1. Resumo Executivo
- estado geral do projeto;
- grau de maturidade atual;
- principais aderências;
- principais lacunas.

## 2. Visão Geral do Projeto

## 3. Mapa da Arquitetura Atual

## 4. Inventário dos Componentes

## 5. Fluxo Real Ponta a Ponta

## 6. Estado Atual do Uso de Skills

## 7. Estado Atual de Memória

## 8. Aderência entre Plano e Implementação

## 9. Bloqueios para Evolução com Skills, RLM e Memória

## 10. Ativos Reaproveitáveis

## 11. Componentes que Exigem Refatoração

## 12. Tabela-Resumo Final
Usar a tabela abaixo:

| Componente | Estado Atual | Evidência | Impacto na Reforma |
|---|---|---|---|

## 13. Matriz Consolidada de Classificação
Consolidar os itens classificados como:
- implementado;
- parcial;
- manual;
- legado;
- inexistente;
- não comprovado.

---

## Resultado esperado
Entregar um diagnóstico que funcione como **espelho fiel, técnico e auditável do estado atual do projeto**, apto a sustentar uma etapa posterior de reformulação arquitetural.
