## 1. Código — extrator

- [x] 1.1 Alterar `self.dirs["input_processed_fm"]` em `extractor.py` de `var/output/processed_fm` para `var/output/md-frontmatter-yaml`
- [x] 1.2 Renomear chave do dicionário de `input_processed_fm` para `input_md_frontmatter` (ou nome descritivo equivalente)
- [x] 1.3 Ajustar mensagens de log para refletir o novo caminho
- [x] 1.4 Adicionar fallback residual para `var/output/processed_fm` como terceira opção (removível em change futura)

## 2. Documentação — Documento Mestre

- [x] 2.1 Adicionar seção com o fluxo canônico de diretórios do pipeline documental: `var/input/raw/` → `var/input/md/` → `var/output/processed/` → `var/output/md-frontmatter-yaml/` → `var/output/extracted/`
- [x] 2.2 Deixar explícito que `var/output/processed_fm/` não é caminho canônico

## 3. Documentação — Runbook Operacional

- [x] 3.1 Adicionar seção com o fluxo canônico de diretórios operacionais
- [x] 3.2 Deixar explícito que `var/output/processed_fm/` não é caminho oficial

## 4. Verificação

- [x] 4.1 Executar `uv run python` com import do extrator para validar que não há quebra de sintaxe
- [x] 4.2 Verificar que nenhum arquivo referencia `processed_fm` como caminho oficial (apenas fallback residual)
