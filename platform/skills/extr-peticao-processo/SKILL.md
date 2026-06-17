---
base: extraction-base.md
description: "Extrai dados estruturados e ultra-granulares de petições judiciais (inicial, incidental,
  manifestação, emenda): identificação da peça, partes, representações, valor da causa, fatos cronológicos, fundamentos legais, teses jurídicas, imóveis e matrículas, garantias, pedidos individualizados e tutela de urgência. Use esta skill sempre que o documento for uma petição inicial, emenda à inicial, manifestação, petição intermediária ou qualquer peça postulatória."
document_types:
- peticao_processo
hitl: false
key_fields:
- process_number
- parties
- representations
- peticao_identification
- valor_da_causa
- fatos
- fundamentos
- provas_e_requerimentos
- pedidos
- atos_juridicos
- documentos_citados
- pessoas_mencionadas
- empresas_mencionadas
- imoveis_e_matriculas
- garantias_e_gravames
- fundamentos_legais
- teses_juridicas
- fatos_cronologicos
- processos_relacionados
- pedidos_individualizados
- tutela_urgencia
- provas_requeridas
- riscos_ou_pontos_de_atencao
llm_default: gemini_api
name: extr-peticao-processo
target_schema: assets/peticao_processo.schema.json
version: 0.3.0
---

# Instrução de Extração: Petição Judicial (Granularidade Avançada)

Seu único output é um objeto JSON válido conforme `assets/peticao_processo.schema.json`.
Leia e aplique todas as regras de `../_shared/proc-core.md` antes de prosseguir.

---

## Diretrizes Críticas de Qualidade

### 1) Literalidade Contínua (Stricta Regra contra Reticências)
- Ao preencher qualquer campo que requeira transcrição do documento (como `trecho_literal` ou `quote` em `anchors`), **NUNCA** insira reticências (`...` ou `…`) para abreviar ou simplificar blocos de texto relevante.
- A transcrição deve ser contínua e corresponder **exatamente** aos caracteres gravados no documento para a referida seção. Se for necessário capturar um bloco extenso, capture-o por inteiro ou divida-o em múltiplos itens, mas não use reticências artificiais.
- Se o trecho contiver dados sensíveis ou rasuras originais e for vital transcrevê-lo, faça-o integralmente de forma literal.

### 2) Tratamento de Informações Ausentes (Opcionalidade)
- **Não invente dados**: Se um dado não constar expressamente no texto, **não o inclua no JSON**.
- Não utilize strings vazias, valores "null" ou placeholders para propriedades ausentes. Simplesmente **omita a propriedade** do objeto JSON.
- Campos como `data`, `cri`, `credor`, `devedor`, `valor_garantido`, `cnpj`, `sede`, e `proprietario_atual` não são obrigatórios nos respectivos objetos do schema. Devem ser omitidos se não forem informados literalmente.

### 3) Preservação de Papéis Literais
- Para `pessoas_mencionadas`, `empresas_mencionadas` e `garantias_e_gravames`, você deve extrair e preservar o termo literal usado para qualificar o papel ou a relação das partes no texto (campo `papel_literal`), por exemplo: "sócia", "tabelião designado", "interveniente garante", "co-executado", "credor hipotecário", "esposa".
- O campo `papel_normalizado` é opcional e serve para categorizar de forma ampla no enum fechado.

### 4) Riscos e Pontos de Atenção Restritos ao Documento
- O campo `riscos_ou_pontos_de_atencao` **não** deve refletir uma opinião jurídica livre elaborada por você.
- Extraia **exclusivamente** riscos, ressalvas, perigos ou pontos de atenção que a petição em si indique expressamente (ex.: perigo de dano iminente por leilão judicial de bens, alienação a terceiros de boa-fé).
- Nunca infira riscos jurídicos novos sem respaldo textual direto. Sempre exija `trecho_literal` e `anchors` comprovando a indicação expressa do risco.

### 5) Estrutura Rígida de Âncoras (Proibido o uso de 'fonte')
- Toda âncora em `anchors` deve obrigatoriamente seguir a estrutura do schema: `kind`, `page_marker`, `quote`.
- **NUNCA** use a palavra-chave `fonte` (ex.: `"fonte": { ... }`) ou qualquer outra nomenclatura customizada.

---


## Regras de Preenchimento dos Novos Campos Granulares

1. **`atos_juridicos`**: Registre atos civis ou processuais descritos na petição (ex.: outorga de procuração, lavratura de escritura, encerramento de sociedade, abertura de crédito). A data do ato é opcional; omita se não constar.
2. **`documentos_citados`**: Liste de forma individualizada todos os documentos mencionados na fundamentação ou listados como anexos (ex.: Contrato Social, Procuração, Escritura de Hipoteca, Certidões das Matrículas).
3. **`pessoas_mencionadas`** e **`empresas_mencionadas`**: Colete todas as pessoas físicas e jurídicas indicadas no texto, registrando o `papel_literal`, qualificações descritas e IDs de documentos (CPF, CNPJ, RG) se constarem de forma explícita.
4. **`imoveis_e_matriculas`**: Estruture cada imóvel mencionado no texto. O campo `matricula` e `descricao` (descrição física e características literais do bem) são exigidos. O Cartório de Registro de Imóveis (`cri`) e o `proprietario_atual` são opcionais e devem ser omitidos se não constarem literalmente.
5. **`garantias_e_gravames`**: Onerações de bens indicadas. O `tipo` (ex.: hipoteca, penhora) e as `imoveis_matriculas` (as matrículas às quais a garantia está vinculada) são obrigatórios. `credor`, `devedor` e `valor_garantido` são opcionais.
6. **`fundamentos_legais`**: Artigos, súmulas ou enunciados explicitamente invocados. Divida em `diploma` (ex.: Código Civil de 1916), `artigo`, `paragrafo_inciso_alinea` (ex.: §1º) e o `texto_citado` literal correspondente.
7. **`teses_juridicas`**: Colete cada tese argumentada (ex.: nulidade absoluta por falta de poderes especiais, ato ultra vires societário). Exige título, resumo interpretativo e o trecho literal contínuo da fundamentação.
8. **`fatos_cronologicos`**: Reúna a cronologia dos fatos históricos relatados (ex.: data de outorga da procuração, data de lavratura da escritura, encerramento da empresa). O campo `data` é opcional (pode ser omitido se for impreciso); `fato` (resumo) e `trecho_literal` são obrigatórios.
9. **`processos_relacionados`**: Indique outros processos citados, relacionando-os (ex.: por dependência, processo a ser suspenso).
10. **`pedidos_individualizados`**: Separe de forma muito granular cada pedido feito pela autora (tutela provisória, citação, procedência do pedido principal para anular escritura, condenação em honorários de sucumbência, protesto por provas, intimações). **NÃO simplifique nem agrupe pedidos enumerados**.
11. **`tutela_urgencia`**: Detalhe se há pedido de tutela provisória/urgência/cautelar. Mapeie de forma individual os requisitos comprovados (como probabilidade do direito e perigo de dano), extraindo os argumentos e os respectivos trechos literais contínuos.
12. **`provas_requeridas`**: Indique os meios de prova que a parte protesta produzir (ex.: prova documental, pericial, testemunhal).
13. **`riscos_ou_pontos_de_atencao`**: Conforme indicado nas diretrizes, extraia somente menções explícitas a perigos de dano ou riscos no texto.

---

## Retrocompatibilidade com Campos Antigos
- Mantenha o preenchimento dos campos `fatos`, `fundamentos`, `provas_e_requerimentos` e `pedidos` de acordo com a estrutura genérica pré-existente (como `AnchoredTextItem` e `Pedido` simples) de modo a garantir que ferramentas antigas que consomem esses campos continuem funcionando. Os novos campos granulares atuam como uma expansão paralela.

---

## Configuração de runtime

| Parâmetro       | Valor padrão                                                                 |
|-----------------|------------------------------------------------------------------------------|
| `input_dir`     | `var/input/proc`                                                             |
| `output_dir`    | `var/output/proc`                                                            |
| `output_prefix` | `peticao_proc_out`                                                           |
| `schema_file`   | `platform/skills/extr-peticao-processo/assets/peticao_processo.schema.json`  |


## Arquivos da skill

| Arquivo                                            | Propósito                                     |
|----------------------------------------------------|-----------------------------------------------|
| `SKILL.md`                                         | Instrução canônica de extração (este arquivo) |
| `assets/peticao_processo.schema.json`              | Schema de extração individual                 |
| `assets/peticao_processo.consolidated.schema.json` | Schema de consolidação                        |
| `references/dicionario_campos.md`                  | Dicionário de campos detalhado                |
| `scripts/validate_output.py`                       | Validação contra o schema                     |

