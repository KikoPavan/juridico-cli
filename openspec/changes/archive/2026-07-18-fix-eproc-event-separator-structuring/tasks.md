## 1. Regressão reproduzível

- [x] 1.1 Localizar os pontos existentes de estruturação de página e serialização de `judicial_locator` no fluxo `pdf-to-md → md-clean-markdown → md-frontmatter-yaml`, confirmando que a correção não alcança OCR, MarkItDown, Gemini ou JSON.
- [x] 1.2 Criar fixture com o bloco Markdown real de `DESPACHO-DECISÃO_evento_32.pdf`, incluindo o localizador incompleto, os rótulos agrupados e os valores subsequentes.
- [x] 1.3 Adicionar teste de regressão inicialmente falho que exija o mapeamento completo do evento 32, a separação entre usuário e papel e a ausência de rótulos vazios/valores soltos.

## 2. Estruturação do separador

- [x] 2.1 Implementar o reconhecimento conservador da página de separação eproc/TJSP com rótulos agrupados no caminho de PDF legível existente.
- [x] 2.2 Mapear os valores reconhecidos para evento, título, data, usuário, papel, processo e sequência, preservando como ausentes os campos que não estiverem no bloco.
- [x] 2.3 Reescrever somente o intervalo reconhecido em formato chave/valor legível, preservando qualquer conteúdo posterior e eliminando os rótulos vazios e valores soltos correspondentes.

## 3. Localizador e integração do pipeline

- [x] 3.1 Fazer merge dos metadados do separador no primeiro `judicial_locator`, preservando `page="1"`, incluindo `kind="event_separator"` e reutilizando análise, escape e ordem da serialização canônica.
- [x] 3.2 Garantir por testes que `md-clean-markdown` produz o bloco estruturado e que `md-frontmatter-yaml` recebe/preserva o primeiro localizador enriquecido sem alterar a arquitetura das etapas.
- [x] 3.3 Adicionar ou ajustar testes focados de `judicial_locator` e `pdf-to-md` para cobrir round-trip dos novos atributos e o caso real de ponta a ponta no caminho legível.

## 4. Validação

- [x] 4.1 Executar os testes focados de `judicial_locator`, `md-clean-markdown` e `pdf-to-md`, corrigindo eventuais regressões dentro do escopo.
- [x] 4.2 Executar os testes focados de `md-frontmatter-yaml` afetados pela preservação do localizador enriquecido.
- [x] 4.3 Executar `openspec validate --all --strict` e confirmar que todas as specs e mudanças permanecem válidas.
- [x] 4.4 Revisar o diff final e confirmar que não há alterações em MarkItDown, OCR, Gemini/JSON, arquitetura do pipeline ou mudanças arquivadas.
