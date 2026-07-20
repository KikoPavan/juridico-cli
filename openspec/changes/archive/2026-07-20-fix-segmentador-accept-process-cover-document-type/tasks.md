## 1. Contrato do segmentador

- [x] 1.1 Adicionar `capa_processo` ao enum de `document_type` em `platform/skills/segmentador-juridico/assets/output-schema.json` e confirmar validação Draft 7.
- [x] 1.2 Inspecionar `scripts/validate_output.py` e alinhar qualquer lista manual de tipos válidos, sem duplicar o enum quando o validador já delegar ao schema.
- [x] 1.3 Documentar `capa_processo` como peça administrativa em `SKILL.md`, `references/variable-dictionary.md` e demais referências diretamente afetadas da skill.

## 2. Curadoria e roteamento seguro

- [x] 2.1 Adicionar regra de alta precedência no `curador-relevancia` para classificar capa sem impacto confirmado como irrelevante, baixa prioridade e ação remover com justificativa auditável.
- [x] 2.2 Garantir que `capa_processo` receba `encaminhamento: null` e nunca seja mapeada para uma skill `extr-*`, preservando a política de impacto confirmado.
- [x] 2.3 Atualizar a documentação e, se aplicável, schemas/referências do curador para registrar o tratamento administrativo da capa.
- [x] 2.4 Alterar somente o roteamento de `capa_processo` no normalizador para uma rota segura não profunda e manter `cabecalho_processo` inalterado.
- [x] 2.5 Verificar que o normalizador ignora sem erro capas removidas e usa revisão manual/não roteável quando recebe excepcionalmente outra ação.

## 3. Regressões

- [x] 3.1 Estender a fixture multipiece mínima para representar `capa_processo` seguida por peças processuais reais, preservando os `judicial_locator`.
- [x] 3.2 Adicionar teste do segmentador que valide e persista `envelope_segmentacao.json` com a capa como primeira peça.
- [x] 3.3 Adicionar testes do curador para ação, impacto, prioridade, justificativa, audit trail, ausência de encaminhamento profundo e proteção por impacto confirmado.
- [x] 3.4 Adicionar testes do normalizador para capa removida e para fallback seguro não profundo.

## 4. Validação operacional e estática

- [x] 4.1 Localizar e executar o teste real de `Processo.md`, registrando claramente indisponibilidade de fixture, credencial ou runtime caso exista bloqueio externo.
  - A chamada online chegou ao fallback por blocos e foi interrompida após espera HTTP prolongada; a reprodução local com o `Processo.md` e o envelope debug reais gerou e validou um envelope de 6 peças com `capa_processo` em `peca_001`.
- [x] 4.2 Executar os testes focados do schema, segmentador multipiece, curador e normalizador.
- [x] 4.3 Executar Ruff em todos os arquivos Python alterados e corrigir os achados.
- [x] 4.4 Executar `git diff --check` e corrigir problemas de whitespace.
- [x] 4.5 Executar `openspec validate --all --strict` e resolver todas as violações relacionadas à mudança.
