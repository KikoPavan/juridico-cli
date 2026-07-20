## 1. Persistência auditável

- [x] 1.1 Definir o nome estável do artefato bruto/debug e persistir uma cópia serializável do envelope compacto válido antes da primeira materialização.
- [x] 1.2 Garantir que o diretório e o artefato debug sobrevivam a uma exceção de peça, sem criar ou sobrescrever `envelope_segmentacao.json` com conteúdo parcial.

## 2. Materialização multipiece

- [x] 2.1 Indexar os `judicial_locator` do Markdown por posição, página e identidade judicial, preservando o marcador textual original.
- [x] 2.2 Implementar a resolução ordenada por limites canônicos, aliases, anchors, início da próxima peça e fallback inequívoco por página.
- [x] 2.3 Recortar do localizador inicial ao final inclusive, preservando texto, ordem, marcadores e páginas `event_separator` intermediárias.
- [x] 2.4 Integrar a materialização contextual da coleção em `run_segmentador_stage` sem usar texto integral do LLM nem alterar os componentes fora de escopo.
- [x] 2.5 Enriquecer a exceção final com `piece_id`, `document_type`, limites, anchors e inventário compacto dos localizadores disponíveis.

## 3. Regressão multipiece

- [x] 3.1 Adicionar fixture Markdown mínima com vários `judicial_locator`, página separadora quando pertinente e pelo menos três intervalos de peça.
- [x] 3.2 Adicionar resposta compacta controlada com três peças e teste que confirme texto materializado para `peca_003` sem conteúdo inventado.
- [x] 3.3 Verificar no teste que o artefato debug e `envelope_segmentacao.json` final são salvos no sucesso e que os `judicial_locator` permanecem no texto.
- [x] 3.4 Adicionar teste de falha que confirme o diagnóstico completo e a preservação do artefato debug antes da exceção.

## 4. Validação

- [x] 4.1 Executar os testes focados do segmentador e da rastreabilidade da nova esteira.
- [x] 4.2 Executar Ruff nos arquivos Python alterados e corrigir todos os achados.
- [x] 4.3 Executar `git diff --check` e corrigir problemas de whitespace.
- [x] 4.4 Executar `openspec validate --all --strict` e resolver todas as violações relacionadas à mudança.
