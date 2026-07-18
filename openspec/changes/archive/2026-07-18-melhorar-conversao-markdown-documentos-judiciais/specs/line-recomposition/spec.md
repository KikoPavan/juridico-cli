## ADDED Requirements

### Requirement: Recompor palavras hifenizadas por quebra de linha
O sistema SHALL remover o hífen e a quebra de linha quando eles dividirem artificialmente uma palavra e a linha seguinte começar com letra minúscula. O sistema MUST preservar hifens semânticos e limites estruturais de Markdown.

#### Scenario: Palavra dividida é recomposta
- **WHEN** o texto contém `juris-\nprudência`
- **THEN** o resultado MUST conter `jurisprudência`

#### Scenario: Hífen semântico é preservado
- **WHEN** uma linha termina com uma expressão hifenizada completa e a próxima linha inicia com maiúscula
- **THEN** o sistema MUST preservar o hífen e a quebra de linha

### Requirement: Recompor linhas fragmentadas de prosa
O sistema SHALL unir uma linha de prosa sem pontuação terminal à linha seguinte quando esta começar com letra minúscula. A recomposição MUST NOT atravessar linhas vazias, marcadores de página, headings, itens de lista, blocos de código ou outros limites estruturais de Markdown.

#### Scenario: Fragmentação de OCR é recomposta
- **WHEN** uma linha de prosa termina sem pontuação e a linha seguinte começa com letra minúscula
- **THEN** o sistema MUST substituir a quebra artificial por um único espaço

#### Scenario: Estrutura Markdown não é atravessada
- **WHEN** duas linhas de prosa são separadas por um heading, item de lista, linha vazia ou `[[judicial_locator: ...]]`
- **THEN** o sistema MUST preservar o limite estrutural

### Requirement: Recomposição de linhas é idempotente
O sistema SHALL produzir o mesmo resultado ao aplicar a recomposição uma ou mais vezes ao mesmo texto.

#### Scenario: Segunda aplicação não altera o resultado
- **WHEN** um texto fragmentado é recomposto duas vezes
- **THEN** o resultado da segunda aplicação MUST ser idêntico ao da primeira
