---
name: reconciler_cadeia_obrigacoes_nulidade_hipoteca
agent: reconciler-cli
process_types:
  - ACAO_NULIDADE_GARANTIA_HIPOTECARIA
description: |
  Skill específica do reconciler-cli para reconstruir e avaliar a cadeia de
  obrigações em casos de nulidade/ineficácia de escrituras de confissão de dívida
  com garantia hipotecária, considerando registros imobiliários, cálculos do
  monetary-cli, documentos de juntada e fatos declarados pelo usuário.
version: 0.2
target_schema: reconciler.schema.json
---

# SKILL ESPECÍFICA – CADEIA DE OBRIGAÇÕES EM NULIDADE DE HIPOTECA

## Quando usar

Use esta skill **apenas** quando:

- `input.contexto_caso.tipo_processo == "ACAO_NULIDADE_GARANTIA_HIPOTECARIA"`, e
- `input.contexto_relacoes.relacoes_criticas[*]` trate de:
  - sucessão de dívidas com o mesmo credor (em especial Banco do Brasil);
  - reaproveitamento de bens em diferentes escrituras como garantia;
  - possíveis baixas de hipoteca sem quitação clara;
  - transferência de garantias entre pessoas físicas/JKMG/empresas do grupo familiar.

Ela complementa a SKILL genérica, especializando a forma de ler `obrigacoes_imobiliarias`
e o contexto de nulidade / excesso de mandato / uso indevido de garantias.

---

## Objetivos específicos

1. **Reconstruir a cadeia de dívidas e garantias**:
   - Identificar a obrigação originária: primeira escritura/cédula em que a
     dívida é constituída para o mesmo credor.
   - Mapear refinanciamentos, rolagens, confissões de dívida e “novas” hipotecas
     que, na prática, podem representar continuação da mesma obrigação.
   - Relacionar matrículas:
     - matrículas de origem (onde a dívida apareceu primeiro) e
     - matrículas de destino (onde a dívida reaparece com “nova” garantia).

2. **Avaliar baixas e quitações**:
   - Usar os campos já consolidados em `obrigacoes_imobiliarias[*].hipotecas_onus[*]`:
     - `quitada`, `cancelada`, `data_baixa`, `valor_presente`, `tipo_divida`, `credor`.
   - Procurar:
     - baixas/cancelamentos **sem menção clara à quitação**;
     - baixas em datas muito próximas à constituição de nova garantia com os
       mesmos bens ou devedores;
     - discrepâncias entre `valor_presente` na data da baixa e o valor da “nova” dívida.

3. **Conectar com pessoas e empresas**:
   - Ler `input.contexto_relacoes` (grupo familiar, empresas, sócios, terceiros).
   - Relacionar obrigações em que:
     - pessoa física passa a responder por dívida originalmente da empresa (ou vice-versa);
     - bens da sociedade são usados para garantir dívidas que beneficiam terceiros.

---

## Uso do schema – foco em `RelacaoCritica`

Para cada relação crítica relevante:

- Preencha `RelacaoCritica` com atenção a:
  - `matriculas_envolvidas` – associe as matrículas que aparecem na cadeia;
  - `obrigacoes_relacionadas` – IDs como `"905:R.16"`, `"7546:R.20"`, etc.;
  - `documentos_juntada_relacionados` – ex.: contratos sociais, procurações;
  - `fontes_apoio[*]` – deixe claro se a base é:
    - registro imobiliário,
    - documento de juntada,
    - evento de processo,
    - ou outro tipo de fonte;
  - `fatos_registros_imobiliarios[*]` – fatos objetivos chave:
    - constituição de hipoteca/cédula;
    - aditivos;
    - baixas/quitações;
    - substituição de garantias.

Na avaliação:

- `status`:
  - `"confirmado"`: quando a cadeia de obrigações e garantias está claramente
    documentada de forma coerente com a relação crítica.
  - `"contrariado"`: quando os registros mostram o contrário do que a relação afirma.
  - `"indicio_forte"`: quando a maioria dos elementos converge para a relação,
    mas ainda há pequenas lacunas documentais.
  - `"indicio_fraco"`: quando a relação é plausível, mas depende fortemente de
    inferência ou de fatos ainda não comprovados.
  - `"nao_localizado_nos_registros"`: quando os registros analisados não dão
    suporte objetivo à relação.

- `nivel_prova_atual`:
  - `"forte"`: documentação intensa e coerente (múltiplas fontes convergentes);
  - `"relevante"`: documentação substancial, porém com algumas lacunas críticas;
  - `"fraca"`: documentação muito incompleta ou baseada sobretudo em hipóteses.

---

## Fatos de registros x fatos declarados pelo usuário

### Fatos de registros

- Use `fatos_registros_imobiliarios[*]` para fatos como:
  - “Constituição de hipoteca em favor do Banco do Brasil em R.16 da matrícula 905”;
  - “Baixa da hipoteca R.16 na Av.44, data efetiva X”;
  - “Transferência de garantia para outra matrícula na mesma data/ato”.

- Sempre indique:
  - `matricula`;
  - `id_obrigacao`, se existir;
  - `fontes_registro` – ex.: `["905:R.16", "905:Av.44-7546"]`;
  - `folhas_registro`, se houver (ex.: `["fls. 9-10"]`).

### Fatos declarados pelo usuário

- Quando o usuário declara fatos no contexto (ex.: que uma dívida X decorre
  de refinanciamento Y, ou que uma escritura está sendo impugnada):

  1. Registre em `fatos_declarados_usuario[*]`:
     - `id_fato_usuario` – ex.: `"U-R1-01"`;
     - `descricao` – o que o usuário afirma;
     - `origem_contexto` – referência a `contexto_relacoes.json`;
     - `ligado_a_obrigacoes` – IDs de obrigações plausivelmente relacionadas;
     - `observacao_reconciler` – como esse fato dialoga com as provas existentes.

  2. **Nunca descarte o fato do usuário apenas por falta de documento
     no pipeline**. Em vez disso:
     - crie `lacunas_documentais[*]` descrevendo qual documento falta;
     - adicione itens a `checklist_documentos`/`checklist_global` para obtenção
       dos documentos (ex.: “certidão de inteiro teor da escritura X”).

  3. Não marque automaticamente `nivel_prova_atual = "fraca"` só porque a
     documentação correspondente ainda não foi processada.  
     - Avalie a coerência entre:
       - o que o usuário afirma;
       - o que já está comprovado nos registros e juntadas;
       - a ausência/presença de contradições claras.
     - Use lacunas/checklist para registrar a **necessidade de juntar** o documento
       em vez de considerar a tese “fraca por padrão”.

---

## Integração com a tese de nulidade/ineficácia da hipoteca

- Destaque, na `RelacaoCritica`, elementos que se conectam à tese:
  - uso reiterado do mesmo imóvel como garantia para o mesmo credor;
  - baixas sem menção expressa à quitação, seguidas de novas garantias;
  - mudanças de devedor (PF ↔ PJ ↔ familiares) mantendo, na prática,
    a mesma obrigação econômica.

- Use `premissas_usuario[*]` para registrar hipóteses relevantes, por exemplo:
  - “P1 – as dívidas agrícolas foram consolidadas na cédula X de 2001”;
  - “P2 – a hipoteca na matrícula 905 é apenas continuação da dívida anterior”.

- Em `comentarios_reconciler`, deixe uma síntese clara, em português técnico,
  da leitura fática da cadeia de obrigações, sem emitir juízo jurídico definitivo
  sobre nulidade (isso será resolvido em FIRAC/petition).

---

## Estilo

- Linguagem técnica, mas clara.
- Foque em cronologia, conexões objetivas e lacunas.
- Não altere o formato do JSON definido em `reconciler.schema.json`.
