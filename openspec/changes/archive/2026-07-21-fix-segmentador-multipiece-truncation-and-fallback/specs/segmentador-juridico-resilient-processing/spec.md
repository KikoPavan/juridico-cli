## ADDED Requirements

### Requirement: Todos os Markdown elegíveis são processados isoladamente
O estágio `segmentador-juridico` SHALL considerar todos os arquivos Markdown elegíveis do diretório em ordem estável. Cada arquivo MUST manter origem, hash, identidade de processo, artefatos e estado de falha próprios; arquivos ou processos diferentes MUST NOT ser consolidados entre si. Uma falha por arquivo MUST NOT impedir a tentativa segura dos demais arquivos.

#### Scenario: Diretório com três arquivos processa todos
- **WHEN** o diretório contém três Markdown elegíveis
- **THEN** o estágio registra uma tentativa e um resultado individual para cada um dos três arquivos

#### Scenario: Falha é isolada por origem
- **WHEN** o segundo de três arquivos falha na segmentação ou validação
- **THEN** o primeiro e o terceiro ainda podem produzir seus envelopes finais válidos, enquanto o segundo fica identificado para revisão

### Requirement: Risco de truncamento seleciona estratégia específica do segmentador
O estágio MUST avaliar antes da chamada ao modelo o tamanho da entrada, a quantidade de páginas e a disponibilidade de marcadores estruturais. Documentos pequenos e de peça única SHALL preservar o caminho atual de chamada estruturada única. Documentos com alto risco de truncamento SHALL usar uma estratégia interna de particionamento do segmentador e MUST NOT acionar `PeticaoBlockStrategy`, `ContestacaoBlockStrategy`, `DecisaoBlockStrategy` nem registrar o segmentador como extrator jurídico.

#### Scenario: Documento curto mantém caminho atual
- **WHEN** um Markdown curto está abaixo dos limites de risco e representa uma única peça
- **THEN** o fake client recebe uma única chamada estruturada com o documento completo

#### Scenario: Documento longo usa janelas próprias
- **WHEN** o preflight classifica um Markdown como alto risco de truncamento e existem marcadores de página suficientes
- **THEN** o estágio produz janelas do segmentador antes de analisar o conteúdo

#### Scenario: Extração por Blocos não é usada
- **WHEN** uma chamada parcial ou completa do segmentador falha
- **THEN** nenhuma estratégia registrada de petição, contestação ou decisão é resolvida ou executada como fallback

### Requirement: Particionamento preserva unidades reais da origem
O particionamento SHALL usar páginas ou marcadores estruturais reais e MUST preservar a ordem absoluta da origem, `judicial_locator`, `process_number`, `event`, `document_code`, `pages_start`, `pages_end` e arquivo de origem. Cortes cegos no meio de marcador ou criação de páginas inexistentes MUST NOT ocorrer. Sobreposição SHALL ser limitada à fronteira necessária para reconhecer continuidade.

#### Scenario: Janela respeita marcadores de página
- **WHEN** o Markdown possui marcadores válidos para todas as páginas
- **THEN** cada janela começa e termina em limites estruturais reais e referencia somente páginas existentes

#### Scenario: Marcadores insuficientes causam revisão segura
- **WHEN** uma entrada longa não possui evidência suficiente para formar janelas verificáveis
- **THEN** o arquivo é encaminhado para revisão e nenhuma página ou peça é inventada

### Requirement: Peças parciais são consolidadas deterministicamente
O estágio MUST ordenar descritores parciais pela posição original e SHALL unir descritores de janelas adjacentes somente quando origem, processo, intervalo, identidade documental e continuidade sustentarem que representam a mesma peça. Uma peça que cruza janelas MUST resultar em uma única peça final. Mudanças confiáveis de evento, código, tipo ou cabeçalho MUST preservar peças adjacentes distintas.

#### Scenario: Peça atravessa duas janelas
- **WHEN** duas janelas sobrepostas descrevem a mesma peça contínua na fronteira
- **THEN** a consolidação produz uma única peça com o intervalo integral da origem

#### Scenario: Peças adjacentes distintas não são unidas
- **WHEN** descritores contíguos possuem mudança confiável de evento, código ou cabeçalho documental
- **THEN** a consolidação mantém duas peças distintas

#### Scenario: Intervalos finais são consistentes
- **WHEN** a consolidação termina com evidência suficiente para todas as peças
- **THEN** os intervalos seguem a ordem da origem sem lacunas ou sobreposições indevidas fora da sobreposição descartada

### Requirement: Fallback determinístico multiparte é conservador
Após falha das chamadas permitidas, o fallback próprio do segmentador SHALL poder produzir múltiplas peças quando mudanças de evento, código documental, cabeçalho judicial ou início documental reconhecível estiverem ancorados em páginas e posições reais. Na ausência de evidência suficiente, o estágio MUST falhar de forma controlada, marcar revisão e MUST NOT presumir peça única nem inventar tipo ou limite.

#### Scenario: Sinais estruturais sustentam múltiplas peças
- **WHEN** locators e cabeçalhos confiáveis delimitam petição, procuração e decisão em uma mesma origem
- **THEN** o fallback produz três descritores compactos ordenados com seus limites reais

#### Scenario: Evidência ambígua não gera envelope
- **WHEN** os sinais disponíveis não permitem decidir uma fronteira ou identidade documental
- **THEN** nenhum envelope final é promovido e a origem é registrada para revisão

### Requirement: Diagnóstico identifica origem e tentativa
Logs e artefatos de falha SHALL identificar ao menos estágio, arquivo, tentativa, estratégia, timestamp e erro de API ou parsing. O estágio SHALL registrar páginas, tamanho, decisão de particionamento, janelas, peças parciais, consolidação, validação e fallbacks. Uma tentativa MUST NOT sobrescrever silenciosamente o diagnóstico de outro arquivo ou tentativa.

#### Scenario: Duas falhas mantêm diagnósticos distintos
- **WHEN** dois arquivos falham na mesma execução
- **THEN** existem artefatos ou metadados correlacionáveis distintos para cada origem e tentativa

#### Scenario: Erro truncado é reproduzível
- **WHEN** uma resposta falha com `Unterminated string`
- **THEN** o diagnóstico associa esse erro à origem, ao estágio, à estratégia e à tentativa responsáveis

