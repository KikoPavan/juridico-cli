## Why

O pipeline real de PDF legível não estrutura corretamente uma página de separação eproc/TJSP já coberta pela spec canônica `eproc-page-structuring`: os rótulos ficam vazios, seus valores são deixados soltos e o primeiro `judicial_locator` perde os metadados do evento. A correção é necessária para fazer a implementação cumprir o contrato existente no caso real `DESPACHO-DECISÃO_evento_32.pdf`.

## What Changes

- Reconhecer, no fluxo `pdf-to-md → md-clean-markdown → md-frontmatter-yaml`, o layout em que os rótulos da página de separação aparecem agrupados antes dos respectivos valores.
- Associar evento, título, data, usuário, papel, processo e sequência aos campos estruturados já definidos pela spec canônica.
- Preservar esses dados no primeiro `judicial_locator`, identificando-o com `kind="event_separator"`.
- Reescrever o bloco da página de separação como chave/valor legível, sem rótulos vazios nem valores soltos.
- Adicionar uma fixture baseada no bloco real e testes focados dos componentes afetados.
- Manter fora de escopo MarkItDown, OCR, Gemini, extração JSON e mudanças na arquitetura do pipeline.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `eproc-page-structuring`: explicitar, como cenário de regressão do contrato existente, o layout real com rótulos agrupados, a marcação `kind="event_separator"` e sua representação chave/valor legível; não há nova capacidade.

## Impact

- Código e testes do caminho de PDF legível em `pdf-to-md`, `md-clean-markdown`, `md-frontmatter-yaml` e utilitários de `judicial_locator` diretamente envolvidos na estruturação e preservação do marcador.
- Fixture de regressão para o bloco real da página de separação do evento 32.
- Nenhuma nova dependência, API ou alteração arquitetural.
- Devem ser consultadas a spec canônica `openspec/specs/eproc-page-structuring/spec.md` e, conforme necessário para os contratos de integração, `openspec/specs/pdf-to-md/spec.md`, `openspec/specs/md-clean-markdown/spec.md` e `openspec/specs/judicial-locator/spec.md`.
