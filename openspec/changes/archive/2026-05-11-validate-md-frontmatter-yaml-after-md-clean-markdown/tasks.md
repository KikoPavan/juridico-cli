## 1. Corrigir detecção de título em apply_frontmatter.py

- [x] 1.1 Em `_detect_title()` (linha ~69), adicionar remoção de marcadores `[[Pág. N]]` após a remoção de HTML comments: `clean = re.sub(r"\[\[Pág\.\s*\d+\]\]", "", clean).strip()`
- [x] 1.2 Verificar manualmente que `_detect_title()` retorna o título correto para a linha `[[Pág. 1]] # Relatório Anual` (expected: `"Relatório Anual"`)

## 2. Atualizar exemplos de referência

- [x] 2.1 Editar `references/exemplo_entrada.md`: substituir ocorrências de `<!-- page N -->` por `[[Pág. N]]` nas seções de conteúdo simulado; manter `<!-- page N -->` apenas em nota explicativa sobre formato legado
- [x] 2.2 Editar `references/exemplo_saida.md`: atualizar o corpo para refletir as mesmas mudanças de `exemplo_entrada.md` (marcadores `[[Pág. N]]` no corpo, frontmatter YAML no topo)

## 3. Atualizar SKILL.md

- [x] 3.1 Na seção "O que esta skill faz" de `SKILL.md`, adicionar item explícito: "Preserva marcadores de página `[[Pág. N]]` (primário) e `<!-- page N -->` (legado) integralmente no corpo de saída"

## 4. Atualizar run_example.sh

- [x] 4.1 Verificar que o arquivo de entrada usado por `run_example.sh` contém pelo menos um marcador `[[Pág. N]]`; se não contiver, atualizar o arquivo de entrada ou o script para apontar para `references/exemplo_entrada.md`
- [x] 4.2 Adicionar ao final de `run_example.sh` a chamada: `python scripts/validate_output.py --input <output> --original <input> --strict`

## 5. Validação end-to-end

- [x] 5.1 Executar `bash scripts/run_example.sh` e confirmar exit code 0
- [x] 5.2 Confirmar que a linha "Corpo preservado integralmente" reporta "Corpo idêntico ao original" na saída de `validate_output.py`
- [x] 5.3 Confirmar que marcadores `[[Pág. N]]` aparecem no arquivo de saída sem alteração
- [x] 5.4 Executar `openspec validate --all --strict` e confirmar que não há erros

## 6. Criar spec formal em openspec/specs/

- [x] 6.1 Criar diretório `openspec/specs/md-frontmatter-yaml/`
- [x] 6.2 Criar `openspec/specs/md-frontmatter-yaml/spec.md` com o conteúdo final consolidado (conforme `specs/md-frontmatter-yaml/spec.md` desta change, sem os prefixos `## ADDED`)
