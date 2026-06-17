# Dicionário de Campos — peticao_processo.schema.json

Derivado de `assets/peticao_processo.schema.json` (v3).

## Tipos recorrentes

| Tipo             | Estrutura                                                                       |
|------------------|---------------------------------------------------------------------------------|
| AnchoredString   | `{value: string, anchors: [Anchor...]}`                                         |
| AnchoredTextItem | `{text: string, label?: string, anchors: [Anchor...]}`                          |
| Anchor           | `{kind: folha ou pagina ou secao ou outro, page_marker: string, quote: string}` |

---

## Objeto raiz (Campos de Expansão e Legados)

| Campo                          | Tipo                           | Obrigatório  | Descrição                                                          |
|--------------------------------|--------------------------------|--------------|--------------------------------------------------------------------|
| `document_type`                | const                          | **sim**      | Sempre `"peticao_processo"`.                                       |
| `process_number`               | AnchoredString                 | não          | Número do processo (quando constar).                               |
| `parties`                      | array PartySummary             | não          | Partes identificadas na petição (legado).                          |
| `representations`              | array Representation           | não          | Advogados/representantes (legado).                                 |
| `peticao_identification`       | AnchoredString                 | não          | Identificação textual da peça (ex.: "PETIÇÃO INICIAL").            |
| `valor_da_causa`               | AnchoredString                 | não          | Valor da causa como texto literal.                                 |
| `fatos`                        | array AnchoredTextItem         | não          | Fatos narrados (legado).                                           |
| `fundamentos`                  | array AnchoredTextItem         | não          | Fundamentos (legado).                                              |
| `provas_e_requerimentos`       | array AnchoredTextItem         | não          | Provas e requerimentos (legado).                                   |
| `pedidos`                      | array Pedido                   | não          | Pedidos principais/expressos (legado).                             |
| `atos_juridicos`               | array AtoJuridico              | não          | Atos civis ou processuais narrados (ex.: outorga de procuração).   |
| `documentos_citados`           | array DocumentoCitado          | não          | Documentos citados ou juntados nos anexos.                         |
| `pessoas_mencionadas`          | array PessoaMencionada         | não          | Pessoas físicas citadas e seus papéis literais.                    |
| `empresas_mencionadas`         | array EmpresaMencionada        | não          | Pessoas jurídicas citadas e seus papéis literais.                  |
| `imoveis_e_matriculas`         | array ImovelMatricula          | não          | Imóveis, descrição literal e matrículas imobiliárias.              |
| `garantias_e_gravames`         | array GarantiaGravame          | não          | Onerações de bens (ex.: hipotecas de terceiro grau).               |
| `fundamentos_legais`           | array FundamentoLegal          | não          | Artigos de lei, súmulas e diplomas legais citados estruturadamente.|
| `teses_juridicas`              | array TeseJuridica             | não          | Argumentos e teses tecidas na peça com citação literal contínua.   |
| `fatos_cronologicos`           | array FatoCronologico          | não          | Linha do tempo dos fatos descritos com trecho literal.             |
| `processos_relacionados`       | array ProcessoRelacionado      | não          | Outros processos de conexão ou dependência indicados.              |
| `pedidos_individualizados`     | array PedidoIndividualizado    | não          | Pedidos individuais (principais e acessórios) estruturados.        |
| `tutela_urgencia`              | TutelaUrgencia                 | não          | Pleito de tutela de urgência/cautelar e seus requisitos legais.    |
| `provas_requeridas`            | array ProvaRequerida           | não          | Meios de prova protestados pela parte.                             |
| `riscos_ou_pontos_de_atencao`  | array RiscoPontoAtencao        | não          | Riscos jurídicos ou operacionais expressamente indicados no texto. |
| `anchors`                      | array Anchor                   | não          | Âncoras gerais da petição.                                         |


---

## Estrutura dos Novos Tipos (`$defs`)

### 1. `AtoJuridico`
- `nome` (string, **obrigatório**): Tipo de ato (ex.: "Escritura Pública de Hipoteca").
- `data` (string, opcional): Data do ato (ex.: "2002-06-28" ou texto literal).
- `detalhes` (string, opcional): Resumo interpretativo do ato.
- `anchors` (array, **obrigatório**): Âncoras que sustentam a menção ao ato.

### 2. `DocumentoCitado`
- `nome` (string, **obrigatório**): Nome do documento (ex.: "Contrato Social da JKMG").
- `tipo_documento` (enum, **obrigatório**): `contrato_social` | `procuracao` | `escritura` | `certidao_matricula` | `contrato_credito` | `peticao` | `outro`.
- `detalhes` (string, opcional): Detalhes sobre o documento.
- `anchors` (array, **obrigatório**): Âncoras que comprovam a citação.

### 3. `PessoaMencionada`
- `nome` (string, **obrigatório**): Nome completo da pessoa física.
- `papel_literal` (string, **obrigatório**): O papel exato atribuído no texto (ex.: "sócia", "viúva", "procurador").
- `papel_normalizado` (enum, opcional): `autor` | `reu` | `procurador` | `tabeliao` | `advogado` | `socio` | `outro`.
- `qualificacao` (string, opcional): Informações de qualificação civil literal.
- `documento_id` (string, opcional): CPF, RG ou outro documento mencionado.
- `anchors` (array, **obrigatório**): Âncoras comprovando a menção.

### 4. `EmpresaMencionada`
- `nome` (string, **obrigatório**): Nome empresarial ou fantasia da PJ.
- `papel_literal` (string, **obrigatório**): Papel exato usado no texto (ex.: "interveniente garante", "ré").
- `papel_normalizado` (enum, opcional): `autor` | `reu` | `interveniente_garante` | `outro`.
- `cnpj` (string, opcional): CNPJ mencionado.
- `sede` (string, opcional): Endereço físico ou cidade da sede.
- `anchors` (array, **obrigatório**): Âncoras associadas.

### 5. `ImovelMatricula`
- `matricula` (string, **obrigatório**): Número de matrícula do imóvel.
- `cri` (string, opcional): Cartório de Registro de Imóveis (CRI).
- `descricao` (string, **obrigatório**): Descrição física literal ou resumida conforme consta.
- `proprietario_atual` (string, opcional): Proprietário de acordo com a peça.
- `anchors` (array, **obrigatório**): Âncoras que comprovam os dados do imóvel.

### 6. `GarantiaGravame`
- `tipo` (string, **obrigatório**): Tipo de garantia (ex.: "hipoteca").
- `grau` (string, opcional): Grau da garantia (ex.: "terceiro grau").
- `credor` (string, opcional): Credor / beneficiário.
- `devedor` (string, opcional): Devedor / outorgante.
- `papel_literal` (string, opcional): Descrição textual do papel.
- `imoveis_matriculas` (array string, **obrigatório**): Lista de números de matrícula onerados.
- `valor_garantido` (string, opcional): Valor da dívida ou da garantia.
- `anchors` (array, **obrigatório**): Âncoras da garantia.

### 7. `FundamentoLegal`
- `diploma` (string, **obrigatório**): Nome da lei ou diploma (ex.: "Código Civil de 1916").
- `artigo` (string, **obrigatório**): Artigo citado (ex.: "1295").
- `paragrafo_inciso_alinea` (string, opcional): Detalhamento do parágrafo, inciso ou alínea.
- `texto_citado` (string, **obrigatório**): Transcrição literal do artigo sem reticências.
- `anchors` (array, **obrigatório**): Âncoras associadas.

### 8. `TeseJuridica`
- `titulo` (string, **obrigatório**): Título resumido da tese.
- `descricao_interpretativa` (string, **obrigatório**): Explicação resumida em termos interpretativos.
- `trecho_literal` (string, **obrigatório**): Citação de texto literal da petição que sustenta a tese.
- `normas_correlatas` (array string, opcional): Normas invocadas (ex.: `["art. 661, §1º do CC/2002"]`).
- `anchors` (array, **obrigatório**): Âncoras correspondentes.

### 9. `FatoCronologico`
- `data` (string, opcional): Data em que o fato ocorreu (AAAA-MM-DD ou textual).
- `fato` (string, **obrigatório**): Resumo interpretativo do acontecimento.
- `trecho_literal` (string, **obrigatório**): Trecho literal comprobatório do fato.
- `anchors` (array, **obrigatório**): Âncoras associadas.

### 10. `PedidoIndividualizado`
- `tipo` (enum, **obrigatório**): `tutela_urgencia` | `citacao` | `procedencia_principal` | `sucumbencia` | `provas` | `outro`.
- `descricao_interpretativa` (string, **obrigatório**): Resumo do que é pleiteado.
- `trecho_literal` (string, **obrigatório**): Texto literal do pedido como grafado na petição.
- `valor` (string, opcional): Valor do pedido se houver.
- `anchors` (array, **obrigatório**): Âncoras do pedido.

### 11. `TutelaUrgencia`
- `requerida` (boolean, **obrigatório**): `true` se houve pedido de tutela.
- `tipo` (enum, **obrigatório**): `cautelar` | `antecipada` | `outra`.
- `descricao_interpretativa` (string, **obrigatório**): Resumo interpretativo do pedido liminar.
- `trecho_literal` (string, **obrigatório**): Texto do pedido liminar.
- `requisitos_demonstrados` (array, **obrigatório**): Requisitos estruturados (`requisito`: `probabilidade_direito`\|`perigo_dano`\|`reversibilidade`\|`outro`, `argumento`, `trecho_literal`).
- `anchors` (array, **obrigatório**): Âncoras comprovando a tutela.

### 12. `ProvaRequerida`
- `tipo_prova` (enum, **obrigatório**): `documental` | `pericial` | `depoimento_pessoal` | `testemunhal` | `outro`.
- `detalhes` (string, **obrigatório**): Resumo da finalidade ou descrição.
- `trecho_literal` (string, **obrigatório**): Texto literal da petição.
- `anchors` (array, **obrigatório**): Âncoras correspondentes.

### 13. `RiscoPontoAtencao`
- `descricao` (string, **obrigatório**): Risco ou ponto de atenção extraído expressamente do texto.
- `trecho_literal` (string, **obrigatório**): Citação literal comprovando o risco.
- `anchors` (array, **obrigatório**): Âncoras correspondentes.

