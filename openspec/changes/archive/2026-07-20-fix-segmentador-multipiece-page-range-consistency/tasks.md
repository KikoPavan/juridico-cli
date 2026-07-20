## 1. Recorte e reconciliação por peça

- [x] 1.1 Reproduzir com o envelope debug real os recortes excessivos da capa 1–2 e do despacho 27–28, registrando as sequências de localizadores que causam ambiguidade.
- [x] 1.2 Alterar a resolução por páginas para selecionar uma sequência contígua e encerrar antes do primeiro localizador fora do intervalo ou pertencente inequivocamente à próxima peça.
- [x] 1.3 Tratar `event_separator` somente quando estiver dentro do intervalo ou explicitamente associado à fronteira, sem incorporar texto de páginas externas.
- [x] 1.4 Recalcular `pages_start/pages_end`, `event`, `document_code` e anchors a partir dos localizadores efetivamente materializados em cada peça.
- [x] 1.5 Registrar em `audit_trail` os limites/identidade propostos, os valores reconciliados e o motivo sempre que houver ajuste.

## 2. Metadados globais consistentes

- [x] 2.1 Calcular `metadata.total_pages` como o máximo entre frontmatter confiável, maior página dos localizadores de origem e maior `pages_end` reconciliado.
- [x] 2.2 Derivar `metadata.event` e `metadata.document_code` somente por consenso global confiável, produzindo valor nulo/ausente em documentos agregados.
- [x] 2.3 Impedir que fragmentos malformados como `umento` sejam promovidos a código documental global ou sobrescrevam códigos internos das peças.

## 3. Segurança de peças não roteáveis

- [x] 3.1 Identificar no curador peças sem encaminhamento `extr-*` reconhecido e limitar seu impacto automático a `acessorio` quando não houver impacto confirmado.
- [x] 3.2 Aplicar ação `revisar` ou `resumir`, prioridade segura e `encaminhamento: null` a `nao_classificado`/`PED HABILIT1`, sem inventar subtipo ou extrator.
- [x] 3.3 Preservar a proteção de impacto confirmado sem criar roteamento inexistente.
- [x] 3.4 Garantir no normalizador que qualquer rota não reconhecida gere `REVISAR_MANUAL`, `review_status: unroutable` e `status: needs_review`, nunca `ready`.
- [x] 3.5 Atualizar documentação diretamente afetada do segmentador, curador e normalizador com as invariantes de reconciliação e não roteáveis.

## 4. Regressões multipiece

- [x] 4.1 Ampliar a fixture/resposta compacta multipiece com páginas repetidas, capa, `PED HABILIT1` e despacho, preservando localizadores reais mínimos.
- [x] 4.2 Testar que `total_pages` é maior ou igual ao maior `pages_end` e que o código global não contém `umento` nem código específico sem consenso.
- [x] 4.3 Testar para cada peça que todos os localizadores materializados pertencem ao intervalo esperado ou possuem exceção de separador auditada.
- [x] 4.4 Testar que a capa é removida, a peça `PED HABILIT1` segue para revisão segura e nenhuma peça não roteável fica pronta para extração.
- [x] 4.5 Testar o fluxo determinístico até `envelope_segmentacao.json`, `envelope_curadoria.json` e os Markdowns normalizados válidos.

## 5. Validação operacional e estática

- [x] 5.1 Executar o fluxo real de `Processo.md`; em caso de instabilidade externa do Gemini, complementar com replay do envelope debug real e registrar ambos os resultados.
  - A tentativa online entrou no fallback por blocos após respostas truncadas e atingiu o limite de 180 segundos. O replay com `Processo.md` e envelope debug reais gerou envelopes segmentado/curado válidos e cinco Markdowns normalizados válidos.
- [x] 5.2 Executar os testes focados do segmentador, curador, normalizador e rastreabilidade judicial.
- [x] 5.3 Executar Ruff em todos os arquivos Python alterados e corrigir os achados.
- [x] 5.4 Executar `git diff --check` e corrigir problemas de whitespace.
- [x] 5.5 Executar `openspec validate --all --strict` e resolver todas as violações relacionadas à mudança.
