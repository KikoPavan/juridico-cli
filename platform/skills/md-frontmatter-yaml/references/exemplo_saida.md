# Exemplo de Saída — md-frontmatter-yaml

Arquivo `.md` esperado após aplicação de frontmatter a
`manual_procedimentos_limpo.md` (ver `exemplo_entrada.md`).

---

## Arquivo gerado: `manual_procedimentos_final.md`

```markdown
---
title: "MANUAL DE PROCEDIMENTOS OPERACIONAIS"
document_type: document
source_file: manual_procedimentos_limpo.md
source_path: /root/devops/juridico-cli/var/input/md-frontmatter-yaml/manual_procedimentos_limpo.md
document_date: "2024-03"
author: "Equipe de Infraestrutura"
language: pt-BR
tags:
  []
status: raw
created_by_skill: md-frontmatter-yaml
---

<!-- page 1 -->
# MANUAL DE PROCEDIMENTOS OPERACIONAIS

Versão 3.2 — Revisado em Março de 2024
Responsável: Equipe de Infraestrutura

---

## 1. OBJETIVO

Este manual define os procedimentos padrão para execução das atividades
operacionais da unidade. Destina-se a todos os colaboradores envolvidos
nos processos de produção, controle e entrega.

<!-- page 2 -->
## 2. ESCOPO

O presente documento aplica-se a:

- Equipe de produção
- Equipe de controle de qualidade
- Equipe de logística
- Supervisores e coordenadores

[... corpo completo preservado ...]

<!-- page 5: empty -->
```

---

## Checklist de conformidade

- [x] Arquivo começa com `---\n` (abertura do frontmatter)
- [x] Bloco YAML fechado com `---\n`
- [x] `title` detectado via H1
- [x] `document_date` detectado via regex (mês/ano)
- [x] `author` detectado via padrão "Responsável:"
- [x] `source_file` preenchido com nome do arquivo
- [x] `source_path` preenchido com caminho absoluto
- [x] `created_by_skill: md-frontmatter-yaml` presente
- [x] YAML válido (parseável por pyyaml)
- [x] Corpo do documento preservado integralmente
- [x] Marcadores de página presentes no corpo
- [x] Sem campos jurídicos especializados
