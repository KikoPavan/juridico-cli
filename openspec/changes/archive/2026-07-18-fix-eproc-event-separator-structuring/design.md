## Context

O caminho de PDF legível `pdf-to-md → md-clean-markdown → md-frontmatter-yaml` já produz um `judicial_locator`, mas o layout real do separador eproc/TJSP apresenta primeiro uma sequência de rótulos e depois uma sequência de valores. A implementação atual interpreta os rótulos isoladamente, mantém os campos vazios no corpo e não enriquece o primeiro marcador. A spec canônica `eproc-page-structuring` define a extração e a serialização; este desenho limita-se a corrigir sua implementação no pipeline existente.

## Goals / Non-Goals

**Goals:**

- Detectar de forma determinística o bloco de separação pelo cabeçalho e pelo conjunto ordenado de rótulos conhecidos.
- Associar valores aos campos canônicos, separando o papel do usuário somente no delimitador textual do layout real.
- Enriquecer o primeiro `judicial_locator` com os metadados extraídos e `kind="event_separator"`, preservando `page` e os demais atributos aplicáveis.
- Substituir o bloco reconhecido por uma representação chave/valor legível e sem campos vazios.
- Cobrir a regressão com fixture realista e testes focados em cada fronteira do fluxo.

**Non-Goals:**

- Adicionar MarkItDown ou mudar o conversor do PDF.
- Alterar OCR, Gemini, extração JSON ou comportamento para PDFs não legíveis.
- Reorganizar módulos, etapas ou responsabilidades arquiteturais do pipeline.
- Reabrir mudanças arquivadas ou ampliar a normalização geral de Markdown.

## Decisions

1. **Reconhecimento conservador no caminho já responsável pela limpeza/estruturação.** O bloco só será transformado quando o cabeçalho de página de separação e os rótulos esperados formarem o padrão conhecido. Isso evita interpretar listas comuns como metadados. A alternativa de um parser genérico de pares posicionais foi rejeitada por ampliar o escopo e elevar falsos positivos.

2. **Mapeamento posicional validado para o layout agrupado.** Após reconhecer os rótulos `Evento`, `Data`, `Usuário`, `Processo` e `Sequência Evento`, os valores subsequentes serão consumidos na mesma ordem. O título do evento será associado ao evento a partir da linha destacada entre o conjunto de rótulos e os demais valores. A alternativa de depender apenas de expressões regulares independentes por linha não resolve rótulos e valores separados.

3. **Separação controlada de usuário e papel.** No valor real, o sufixo ` - MAGISTRADO` será separado em `event_user_role`, preservando todo o prefixo em `event_user`. A separação deve se apoiar no formato reconhecido e não remover partes arbitrárias de nomes. Campos não presentes permanecem ausentes, conforme a spec canônica.

4. **Um único modelo de metadados alimenta marcador e bloco legível.** Os dados extraídos serão usados para atualizar o primeiro `judicial_locator` e para reescrever o separador em chave/valor. Isso impede divergência entre o marcador e o corpo. A serialização reutilizará a implementação canônica de `judicial_locator`, incluindo ordem e escape, em vez de concatenar o marcador manualmente.

5. **Correção local, sem nova etapa.** A implementação permanecerá nas funções existentes de `pdf-to-md`, `md-clean-markdown` e utilitários do marcador que já participam do fluxo; `md-frontmatter-yaml` deve apenas receber e preservar o resultado. Não será criado módulo, runtime ou dependência nova.

## Risks / Trade-offs

- [Variações do layout eproc quebrarem o reconhecimento posicional] → Exigir âncoras do separador, tolerar apenas variações de espaço/Markdown necessárias e manter campos ausentes sem inferência.
- [Separar incorretamente hífens pertencentes ao nome do usuário] → Dividir pelo delimitador final associado a um papel reconhecível no padrão, com teste usando o valor real completo.
- [Duplicar ou sobrescrever atributos do primeiro marcador] → Analisar o marcador existente, fazer merge explícito dos campos do separador e serializar pela API canônica.
- [A reescrita remover conteúdo jurídico após o separador] → Delimitar estritamente o intervalo consumido e testar a preservação do conteúdo posterior.
- [Testes excessivamente acoplados à formatação incidental] → Asserir campos estruturados e propriedades essenciais do bloco, mantendo uma integração exata apenas para a fixture de regressão.
