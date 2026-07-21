## ADDED Requirements

### Requirement: Consolidação multiparte preserva o contrato canônico
Para documentos longos ou multiparte, o `segmentador-juridico` MUST consolidar descritores parciais antes da materialização final. Cada peça consolidada SHALL preservar `process_number`, `event`, `document_code`, `pages_start`, `pages_end`, `judicial_locator`, arquivo de origem e ordem original das páginas quando essas evidências estiverem disponíveis. O texto integral MUST continuar sendo materializado exclusivamente do Markdown da mesma origem.

#### Scenario: Documento multiparte preserva identidade e origem
- **WHEN** janelas parciais identificam peças de eventos e códigos documentais distintos no mesmo processo
- **THEN** cada peça final mantém sua identidade judicial, seus locators, sua origem e seu intervalo real sem misturar outra origem

#### Scenario: Marcador de página permanece válido
- **WHEN** anchors ou locators são transportados à peça consolidada
- **THEN** `page_marker` nunca é vazio, `"[]"` nem representa página ausente da origem

### Requirement: Consolidação e envelope final possuem barreiras de validação distintas
A coleção compacta consolidada MUST validar contra o contrato intermediário e contra invariantes determinísticas de cobertura, ordem, identidade e limites antes de materializar texto. Depois da materialização e do enriquecimento, o envelope final MUST validar contra `platform/skills/segmentador-juridico/assets/output-schema.json` antes de ser promovido como `envelope_segmentacao.json` ou entregue ao handoff normal. Uma falha em qualquer barreira MUST impedir a promoção do arquivo afetado sem remover envelopes válidos de outras origens.

#### Scenario: Decisão consolidada inválida não é materializada
- **WHEN** a consolidação omite um descritor obrigatório, produz intervalo inválido ou viola cobertura, ordem ou identidade
- **THEN** nenhum texto é materializado e nenhum envelope final desse arquivo é promovido, enquanto o diagnóstico permanece disponível

#### Scenario: Envelope materializado viola o schema canônico
- **WHEN** a decisão compacta é válida mas o envelope enriquecido viola o schema canônico
- **THEN** `envelope_segmentacao.json` não é promovido nem entregue ao curador

#### Scenario: Arquivo válido sobrevive a outro inválido
- **WHEN** um arquivo do lote valida e outro falha na validação consolidada
- **THEN** o envelope válido permanece materializado e o inválido fica isolado para revisão

### Requirement: Regressão real é separada da suíte automatizada
A cobertura automatizada SHALL usar fake client e fixtures locais para todos os caminhos estruturados, particionados e de falha. A regressão com o `Processo.pdf` real SHALL possuir procedimento operacional preparado, MUST NOT ser executada automaticamente em testes unitários e MUST preceder o arquivamento da mudança.

#### Scenario: Suíte não chama Gemini
- **WHEN** as suítes automatizadas do segmentador são executadas
- **THEN** todas as respostas do modelo vêm de fake client e nenhuma chamada real ao Gemini ocorre

#### Scenario: Arquivamento depende do teste operacional
- **WHEN** implementação e testes automatizados estiverem concluídos mas o `Processo.pdf` ainda não tiver sido validado operacionalmente
- **THEN** a mudança permanece não arquivada
