## 1. Title heuristic for legal document-type line

- [x] 1.1 Em `apply_frontmatter.py`, criar função `_detect_legal_doc_type_title(body, document_type)` que, quando `document_type == "contestacao_processo"`, procura nas primeiras 40 linhas do corpo (após remover `<!-- ... -->`, `[[Pág. N]]` e `[[judicial_locator: ...]]`) uma linha isolada cujo conteúdo, após `strip()`, seja exatamente `CONTESTAÇÃO`; retorna `(title, "legal_doc_type_line")` se encontrar, senão `(None, "null")`.
- [x] 1.2 Em `main()`, chamar `_detect_legal_doc_type_title` antes de `_detect_title`; usar o resultado se não for `None`, caso contrário manter o fallback atual (`args.title` → `_detect_title`).
- [x] 1.3 Adicionar teste unitário cobrindo a linha `CONTESTAÇÃO` isolada prevalecendo sobre um H1 longo/truncado do tipo `# PROCEDIMENTO COMUM (...)` presente antes no corpo, com `document_type="contestacao_processo"`.
- [x] 1.4 Adicionar teste unitário confirmando que, sem a linha explícita `CONTESTAÇÃO`, o comportamento cai no `_detect_title` genérico (sem regressão).

## 2. Author heuristic for petition party opening pattern

- [x] 2.1 Em `apply_frontmatter.py`, criar função `_detect_petition_party_author(body)` que busca, nas primeiras 30 linhas do corpo (após remoção de marcadores), uma linha iniciada por nome em caixa alta (letras, dígitos, `.`, `-`, espaços, incluindo sufixos como `S.A.`, `LTDA`, `EIRELI`, `ME`) seguida de vírgula, condicionada à presença de `vem` seguido posteriormente de `apresentar` na mesma linha ou nas linhas seguintes próximas; retorna `(author, "regex_petition_party")` se encontrar, senão `(None, "null")`.
- [x] 2.2 Em `main()`, chamar `_detect_petition_party_author` apenas quando não houver `args.author`, `extracted_meta["user"]` (locator) nem resultado de `_detect_author` (rótulo explícito) — ou seja, como último fallback antes de `null`.
- [x] 2.3 Adicionar teste unitário cobrindo o caso real: corpo iniciando com `BANCO DO BRASIL S.A., instituição financeira ..., ... vem, ... apresentar` resultando em `author == "BANCO DO BRASIL S.A."`.
- [x] 2.4 Adicionar teste unitário confirmando que, sem o padrão `NOME, ... vem ... apresentar`, `author` permanece `None` (sem regressão).

## 3. Body preservation regression test

- [x] 3.1 Criar fixture de teste com o trecho relevante do caso real de contestação (evento 43) reproduzindo: locator judicial, H1 truncado, linha isolada `CONTESTAÇÃO`, e abertura `BANCO DO BRASIL S.A., ...`.
- [x] 3.2 Adicionar teste que executa `apply_frontmatter.py` sobre essa fixture, remove o bloco de frontmatter do output e verifica que o corpo restante é idêntico byte-a-byte ao corpo de entrada.
- [x] 3.3 Confirmar (via teste ou asserção) que `document_date` permanece `null` para essa fixture, já que não há data confiável da peça no trecho.

## 4. Validation

- [x] 4.1 Rodar `uv run pytest platform/skills/md-frontmatter-yaml/` e confirmar que todos os testes (novos e existentes) passam.
- [x] 4.2 Rodar `openspec validate --all --strict` e confirmar sucesso.
- [x] 4.3 Gerar o frontmatter para o arquivo real `var/tmp/check_pdf_legivel/clean/CONTESTAÇÃO_evento_43.md` com `--doc-type contestacao_processo` e confirmar manualmente que `title: CONTESTAÇÃO` e `author: BANCO DO BRASIL S.A.` aparecem no YAML resultante, com `document_date: null` mantido.
