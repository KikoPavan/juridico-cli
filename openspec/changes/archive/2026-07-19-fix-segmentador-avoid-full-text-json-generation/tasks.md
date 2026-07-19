## 1. Contrato compacto de segmentação

- [x] 1.1 Definir o schema intermediário compacto usado por `run_segmentador_stage`, aceitando identidade lógica, classificação, limites/aliases de página, título/excerpt, relevância, anchors e identidade judicial, sem `text` ou `text_content` integral.
- [x] 1.2 Atualizar as instruções da skill `segmentador-juridico` e a chamada do orquestrador para pedir somente descritores compactos ao LLM.
- [x] 1.3 Validar a raiz e a coleção da resposta intermediária, impedindo que estruturas genéricas de extração sem envelope/peças sejam promovidas a saída do segmentador.

## 2. Materialização determinística

- [x] 2.1 Implementar helpers para agrupar e resolver `judicial_locator` por identidade e página, preservando processo, evento, código de documento e marcadores originais.
- [x] 2.2 Implementar o recorte ordenado do Markdown original por limites/anchors e preencher deterministicamente o texto completo de cada peça.
- [x] 2.3 Canonicalizar paginação e enriquecer peças/anchors com localizadores e proveniência, preservando valores canônicos explícitos não nulos.
- [x] 2.4 Implementar fallback de peça única para um único grupo inequívoco de localizadores, com inferência conservadora de `document_type` por heading, `document_code` ou nome do arquivo.
- [x] 2.5 Materializar metadados e defaults obrigatórios e validar o envelope final com `platform/skills/segmentador-juridico/assets/output-schema.json` antes da persistência.

## 3. Testes de regressão

- [x] 3.1 Adicionar testes unitários para resposta compacta, reconstrução de intervalos, canonicalização e rejeição de estrutura genérica incompatível.
- [x] 3.2 Adicionar teste de `run_segmentador_stage` com `Petição Inicial_evento_1.md` ou fixture mínima equivalente, simulando falha/resposta incompatível do LLM e verificando a geração de `envelope_segmentacao.json`.
- [x] 3.3 Verificar no teste que o envelope possui `metadata` e `pecas`, que o texto integral vem do Python, e que `judicial_locator`, `process_number`, `event`, `document_code`, `pages_start`, `pages_end` e anchors são preservados.
- [x] 3.4 Validar no teste o arquivo gerado com `jsonschema.Draft7Validator` contra o `output-schema.json` canônico.
- [x] 3.5 Confirmar por testes de regressão que `extr-peticao-processo`, `md-clean-markdown`, `md-frontmatter-yaml`, OCR e provider Gemini permanecem inalterados.

## 4. Verificação final

- [x] 4.1 Executar os testes focados do segmentador e da nova esteira jurídica.
- [x] 4.2 Executar Ruff nos arquivos Python afetados e corrigir os achados introduzidos pela mudança.
- [x] 4.3 Executar `git diff --check` e corrigir problemas de whitespace.
- [x] 4.4 Executar `openspec validate --all --strict` e resolver todas as falhas relacionadas à mudança.
