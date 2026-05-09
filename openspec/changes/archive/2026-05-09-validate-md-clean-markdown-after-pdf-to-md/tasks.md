## 1. Atualizar lógica de detecção de marcadores em clean_markdown.py

- [x] 1.1 Ler `platform/skills/md-clean-markdown/scripts/clean_markdown.py` completo e identificar todas as ocorrências de `PAGE_MARKER_RE` e `_is_page_marker`
- [x] 1.2 Estender `PAGE_MARKER_RE` para incluir `\[\[Pág\.\s*\d+\]\]` como alternativa via `|`, preservando o padrão legado `<!-- page N -->`
- [x] 1.3 Verificar que `_is_page_marker()` usa `re.search()` (não `re.match()`), garantindo detecção de marcadores inline — não alterar a lógica, apenas confirmar
- [x] 1.4 Atualizar a string de help do argumento `--no-markers` para mencionar ambos os formatos

## 2. Atualizar validate_output.py

- [x] 2.1 Ler `platform/skills/md-clean-markdown/scripts/validate_output.py` completo e mapear todos os pontos onde marcadores de página são mencionados ou verificados
- [x] 2.2 Adicionar verificação de integridade de marcadores: extrair todos os marcadores do arquivo de entrada com `PAGE_MARKER_RE` e confirmar que cada um está presente no arquivo de saída
- [x] 2.3 Garantir que o mesmo `PAGE_MARKER_RE` atualizado (tarefa 1.2) seja usado no validador — não duplicar o regex

## 3. Atualizar documentação da skill

- [x] 3.1 Atualizar `SKILL.md`: na descrição da skill e na lista de regras de limpeza, substituir referência exclusiva a `<!-- page N -->` por "marcadores `[[Pág. N]]` (primário) e `<!-- page N -->` (legado)"
- [x] 3.2 Atualizar `assets/cleaning_rules.md` Regra 7: adicionar `[[Pág. N]]` como formato primário, manter `<!-- page N -->` como legado, e adicionar a proibição absoluta de conversão entre formatos
- [x] 3.3 Atualizar `assets/output_contract.md`: refletir os dois formatos reconhecidos no contrato formal de preservação de marcadores
- [x] 3.4 Atualizar `assets/normalization_map.yaml` se o arquivo listar formatos de marcadores de página

## 4. Substituir exemplos de referência

- [x] 4.1 Reescrever `references/exemplo_entrada.md` usando `[[Pág. N]]` como marcador primário; manter `<!-- page N -->` como exemplo legado secundário; basear o conteúdo no arquivo real `var/output/pdf-to-md/arquivo_escaneado.md`
- [x] 4.2 Reescrever `references/exemplo_saida.md` com o output esperado correspondente ao novo `exemplo_entrada.md`, mostrando que os marcadores `[[Pág. N]]` foram preservados intactos

## 5. Validação ponta a ponta

- [x] 5.1 Executar `clean_markdown.py` usando `var/output/pdf-to-md/arquivo_escaneado.md` como entrada e um arquivo temporário como saída
- [x] 5.2 Confirmar que todos os marcadores `[[Pág. N]]` do arquivo de entrada estão presentes e inalterados no arquivo de saída
- [x] 5.3 Executar `validate_output.py` sobre a saída gerada na tarefa 5.1 e confirmar que não há erros de marcador
- [x] 5.4 Executar `run_example.sh` e confirmar que o exemplo pré-configurado completa sem erros
