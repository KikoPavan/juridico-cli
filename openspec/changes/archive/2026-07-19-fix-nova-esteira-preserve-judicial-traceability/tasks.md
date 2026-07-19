## 1. Contratos e canonicalização do segmentador

- [x] 1.1 Atualizar o schema, o dicionário de campos e o adaptador/saída do `segmentador-juridico` para aceitar `page_number_start`/`page_number_end`, preencher apenas `pages_start`/`pages_end` ausentes ou nulos e preservar valores canônicos explícitos.
- [x] 1.2 Estender os contratos de envelope e anchors para transportar `process_number`/`processo_id`, `event_id`/`event`, `document_code` e `page` disponíveis até o curador, sem alterar `pdf-to-md`, `md-clean-markdown` ou o provider Gemini.
- [x] 1.3 Adicionar testes de schema/canonicalização cobrindo aliases, precedência dos campos canônicos e enriquecimento parcial/completo de anchors.

## 2. Propagação e proteção curatorial

- [x] 2.1 Atualizar os schemas e a transformação do `curador-relevancia` para conservar paginação, texto, anchors e identidade judicial recebidos do segmentador.
- [x] 2.2 Implementar fallback mínimo `relevante` para `peticao_inicial`, `contestacao`, `decisao`, `sentenca` e `recurso` quando o impacto estiver ausente, nulo ou vier apenas do default genérico, preservando classificações `nuclear` existentes.
- [x] 2.3 Adicionar testes do curador para cada tipo protegido, para preservação de `nuclear` e para um tipo não protegido que continue sujeito às regras atuais.

## 3. Markdown normalizado rastreável

- [x] 3.1 Atualizar o `yaml-normalizador-juridico` e seu schema/validador para renderizar `process_number` (com fallback de `processo_id`), `event` (com fallback de `event_id`) e `document_code` no frontmatter final.
- [x] 3.2 Aplicar no normalizador a mesma precedência de paginação e a defesa do impacto protegido, sem substituir valores explícitos não nulos por fallback.
- [x] 3.3 Garantir que a composição do Markdown final preserve literalmente todos os `[[judicial_locator: ...]]` presentes no texto recebido e que anchors gerados carreguem os atributos judiciais disponíveis.
- [x] 3.4 Adicionar testes unitários do `yaml-normalizador-juridico` para frontmatter judicial, aliases de páginas, precedência de fontes, impacto protegido e preservação do corpo/localizadores.

## 4. Regressão e validação

- [x] 4.1 Adicionar a fixture `Petição Inicial_evento_1.md` sanitizada ou uma fixture mínima equivalente com páginas 1–15 e locator de processo/evento/documento, evitando versionar PII desnecessária.
- [x] 4.2 Adicionar e executar o teste focado ponta a ponta `segmentador-juridico → curador-relevancia → yaml-normalizador-juridico`, confirmando `pages_start: 1`, `pages_end: 15`, identidade judicial no frontmatter e locator intacto no corpo.
- [x] 4.3 Executar a suíte do `yaml-normalizador-juridico` e corrigir qualquer regressão dentro do escopo da nova esteira.
- [x] 4.4 Confirmar pelo diff que `pdf-to-md`, `md-clean-markdown`, `extr-peticao-processo` e o provider Gemini não foram alterados.
- [x] 4.5 Executar `openspec validate --all --strict` e registrar resultado sem erros antes de concluir a implementação.
