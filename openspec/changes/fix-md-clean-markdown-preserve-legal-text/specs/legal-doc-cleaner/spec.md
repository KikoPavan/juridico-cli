## ADDED Requirements

### Requirement: fix_encoding não altera caracteres Unicode válidos do texto de entrada

`LegalDocCleaner.fix_encoding` SHALL corrigir apenas sequências de mojibake conhecidas (bytes UTF-8 mal-interpretados como Latin-1). O método MUST NOT substituir caracteres Unicode válidos presentes no texto de entrada, incluindo letras acentuadas como `Ã` (U+00C3), `Õ` (U+00D5), e qualquer outro ponto de código que seja um caractere legítimo do Português Brasileiro.

#### Scenario: AÇÃO não é corrompido
- **WHEN** `fix_encoding` recebe a string `"AÇÃO DECLARATÓRIA"`
- **THEN** retorna `"AÇÃO DECLARATÓRIA"` sem alteração (Ã permanece U+00C3)

#### Scenario: NÃO não é corrompido
- **WHEN** `fix_encoding` recebe a string `"NÃO contém"`
- **THEN** retorna `"NÃO contém"` sem alteração

#### Scenario: QUALIFICAÇÃO não é corrompida
- **WHEN** `fix_encoding` recebe a string `"QUALIFICAÇÃO"`
- **THEN** retorna `"QUALIFICAÇÃO"` sem alteração

#### Scenario: PROCURAÇÃO não é corrompida
- **WHEN** `fix_encoding` recebe a string `"PROCURAÇÃO"`
- **THEN** retorna `"PROCURAÇÃO"` sem alteração

#### Scenario: PRETENSÃO não é corrompida
- **WHEN** `fix_encoding` recebe a string `"PRETENSÃO"`
- **THEN** retorna `"PRETENSÃO"` sem alteração

#### Scenario: marcadores de página não são alterados
- **WHEN** `fix_encoding` recebe a string `"[[Pág. 3]]"`
- **THEN** retorna `"[[Pág. 3]]"` sem alteração

---

### Requirement: patterns_to_remove não consomem quebras de linha adjacentes

Os padrões em `LegalDocCleaner.patterns_to_remove` SHALL usar `[ \t]*` (espaço e tab horizontais apenas) como quantificador final, nunca `\s*`. Isso garante que a remoção de um cabeçalho ou rodapé repetido não consuma o `\n` da linha seguinte, evitando a junção de headings Markdown ou parágrafos com o texto anterior.

#### Scenario: remoção de COMARCA não cola heading seguinte
- **WHEN** `remove_headers_footers` processa texto contendo `"DE CERQUEIRA CÉSAR – SP\nCOMARCA DE CERQUEIRA CÉSAR\n# DECLARATÓRIA DE NULIDADE"`
- **THEN** o output não contém `"SP# DECLARATÓRIA"` em uma única linha

#### Scenario: remoção de FORO não cola heading seguinte
- **WHEN** `remove_headers_footers` processa texto contendo `"declaratória.\nFORO DE CERQUEIRA CÉSAR\n# DA PROCURAÇÃO SEM PODERES ESPECIAIS"`
- **THEN** o output não contém `"declaratória.#"` em uma única linha

#### Scenario: heading removido deixa newline intacto
- **WHEN** qualquer padrão de `patterns_to_remove` é aplicado a uma linha que termina com `\n`
- **THEN** o `\n` ao final da linha removida permanece no texto (como linha vazia ou colapsa com normalize_whitespace), nunca juntando o texto anterior ao texto seguinte

---

### Requirement: clean_document preserva conteúdo jurídico válido end-to-end

`LegalDocCleaner.clean_document` SHALL produzir um arquivo de saída que preserve os acentos e a estrutura de headings do arquivo de entrada. Palavras com `ÃO` (AÇÃO, NÃO, QUALIFICAÇÃO, PROCURAÇÃO, PRETENSÃO) MUST aparecer no output com os mesmos caracteres Unicode do input.

#### Scenario: pipeline completo preserva acentos
- **WHEN** `clean_document` processa um arquivo `.md` contendo `"AÇÃO DECLARATÓRIA\nNÃO contém\nQUALIFICAÇÃO\nPROCURAÇÃO\nPRETENSÃO"`
- **THEN** o arquivo de saída contém `"AÇÃO"`, `"NÃO"`, `"QUALIFICAÇÃO"`, `"PROCURAÇÃO"`, `"PRETENSÃO"` com os mesmos caracteres de entrada

#### Scenario: pipeline completo não introduz padrões corrompidos
- **WHEN** `clean_document` processa o arquivo `var/input/md/Petição Declaração de Nulidade.md`
- **THEN** o arquivo de saída não contém nenhum dos padrões: `AÇÁO`, `NÁO`, `QUALIFICAÇÁO`, `PROCURAÇÁO`, `PRETENSÁO`, `SP#`, `declaratória.#`
