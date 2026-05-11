# Exemplo de Entrada — md-frontmatter-yaml

Markdown limpo típico após processamento por `md-clean-markdown`.
Sem frontmatter YAML. Documento genérico: manual de procedimentos.

---

## Metadados do exemplo

| Campo         | Valor                                              |
|---------------|----------------------------------------------------|
| Nome fictício | `manual_procedimentos_limpo.md`                    |
| Tipo          | Manual de procedimentos operacionais (genérico)    |
| Origem        | Saída simulada de md-clean-markdown                |

---

## Conteúdo limpo simulado (sem frontmatter)

```
[[Pág. 1]]
# MANUAL DE PROCEDIMENTOS OPERACIONAIS

Versão 3.2 — Revisado em Março de 2024
Responsável: Equipe de Infraestrutura

---

## 1. OBJETIVO

Este manual define os procedimentos padrão para execução das atividades
operacionais da unidade. Destina-se a todos os colaboradores envolvidos
nos processos de produção, controle e entrega.

[[Pág. 2]]
## 2. ESCOPO

O presente documento aplica-se a:

- Equipe de produção
- Equipe de controle de qualidade
- Equipe de logística
- Supervisores e coordenadores

## 3. DEFINIÇÕES

- **Ordem de Serviço (OS):** documento que autoriza a execução de uma atividade.
- **Não Conformidade (NC):** desvio identificado em relação ao padrão estabelecido.
- **Registro:** evidência documentada de uma atividade realizada.

[[Pág. 3]]
### 4. PROCEDIMENTO GERAL

4.1 Recebimento de Materiais

Ao receber materiais, o colaborador deve:

1. Conferir a nota fiscal com o pedido de compra
2. Verificar integridade das embalagens
3. Registrar entrada no sistema de controle

---

4.2 Execução da Atividade

Durante a execução, observe:

- Utilizar os EPIs indicados para cada função
- Preencher o formulário de OS ao início e ao fim
- Comunicar ao supervisor qualquer NC identificada

[[Pág. 4]]
## 5. REGISTROS E EVIDÊNCIAS

Todos os registros devem ser:

- Preenchidos de forma legível e completa
- Assinados pelo responsável pela execução
- Arquivados pelo prazo mínimo de 5 anos

[[Pág. 5]]
```

> **Nota:** O formato legado `<!-- page N -->` (comentário HTML) é produzido por versões
> anteriores de `md-clean-markdown`. O formato primário atual é `[[Pág. N]]`.

---

## O que será detectado automaticamente

| Campo            | Valor esperado detectado                 | Método        |
|------------------|------------------------------------------|---------------|
| `title`          | `"MANUAL DE PROCEDIMENTOS OPERACIONAIS"` | H1 do corpo   |
| `document_date`  | `"2024-03"` (parcial)                    | regex mês/ano |
| `author`         | `"Equipe de Infraestrutura"`             | regex "Responsável:" |
