# Regras Base de Extração Jurídico-CLI (Transversal)

> Este documento contém diretrizes estritas que devem ser agregadas a todos os prompts de extração de dados tabulares/padronizados executados pelos bundles `extr-*`. O modelo deve cumprir estas determinações integralmente e sem exceções.

1. **Schema como Lei (Schema as Law)**
   - O schema validacional fornecido (JSON) dita a estrutura absoluta e imutável da saída.
   - Você deve retornar **exatamente** as chaves solicitadas e respeitar suas tipagens.
   - Nunca omita, exclua ou deixe de retornar um campo obrigatório estabelecido pelo schema.
   - **É terminantemente proibida a criação de novos campos** ou propriedades que não existam previamente no escopo do schema.
   - Sempre que o schema exigir propriedades de rastreabilidade de evidência para uma informação extraída, obedeça integralmente, garantindo o preenchimento inegociável da fonte de origem, de modo especial os atributos de contexto `fonte.arquivo_md` e `fonte.ancora`.

2. **Paridade Funcional e Literalidade**
   - Transcreva termos, nomes e informações documentais conservando a sua **literalidade textual integral**.
   - Em hipótese alguma infira, modifique, resuma ou corrija eventuais falhas do texto fonte original. Extraia exatamente o que está escrito no documento.

3. **Cotação de Valores (Moeda Literal)**
   - Extraia a moeda e os respectivos valores financeiros de forma **literal**, preservando da forma exata como constam no texto original.
   - É terminantemente proibido realizar conversão numérico-universal (float base) como padrão. Fica proibida qualquer conversão ou transição de moeda histórica autônoma.

4. **Segurança de Ausência (Null Safe)**
   - Caso a informação requerida **não seja fornecida explicitamente** ou seja imprecisa no documento alvo, reaja da seguinte forma:
     - Para um **campo singular ausente**, retorne o valor `null`.
     - Para uma **lista/array ausente**, retorne `[]`.
   - Jamais preencha chaves indefinidas com "Não informado", "N/A", "Desconhecido" ou string vazia `""`.

5. **Retorno Cru e Puro (JSON Exclusivo)**
   - O payload de saída gerado deve retornar uma representação crua unicamente no formato JSON puro, validado pelo schema.
   - Fica vetada qualquer inserção de resumos, conclusões, explicações iniciais/finais ou bloco de resposta envolto em marcações markdown como ````json```` se não requerido ativamente pelo pipeline que o chama. Só o JSON cru deve ser emitido.
