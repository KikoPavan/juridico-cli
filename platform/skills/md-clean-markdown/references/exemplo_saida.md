# Exemplo de Saída — md-clean-markdown

Markdown limpo esperado após processamento de `manual_procedimentos_bruto.md`
(ver `exemplo_entrada.md`).

Serve como referência de conformidade para `validate_output.py`
e para avaliação visual da qualidade da limpeza.

---

## Arquivo gerado: `manual_procedimentos_limpo.md`

```markdown
<!-- page 1 -->
# MANUAL DE PROCEDIMENTOS OPERACIONAIS

Versão 3.2 — Revisado em Março de 2024
Departamento de Operações

---

## 1. OBJETIVO

Este manual define os procedimentos padrão para execução das atividades
operacionais da unidade. Destina-se a todos os colaboradores envolvidos
nos processos de produção, controle e entrega.

---

<!-- page 2 -->
## 2. ESCOPO

O presente documento aplica-se a:

- Equipe de produção
- Equipe de controle de qualidade
- Equipe de logística
- Supervisores e coordenadores

## 3. DEFINIÇÕES

Abaixo estão os principais termos utilizados neste manual:

- **Ordem de Serviço (OS):** documento que autoriza a execução de uma atividade.
- **Não Conformidade (NC):** desvio identificado em relação ao padrão estabelecido.
- **Registro:** evidência documentada de uma atividade realizada.

<!-- page 3 -->
### 4. PROCEDIMENTO GERAL

4.1 Recebimento de Materiais

Ao receber materiais, o colaborador deve:

1. Conferir a nota fiscal com o pedido de compra
2. Verificar integridade das embalagens
3. Registrar entrada no sistema de controle
4. Encaminhar para o setor responsável

---

4.2 Execução da Atividade

Durante a execução, observe:

- Utilizar os EPIs indicados para cada função
- Preencher o formulário de OS ao início e ao fim
- Comunicar ao supervisor qualquer NC identificada

<!-- page 4 -->
## 5. RESPONSABILIDADES

| Função          | Responsabilidade                        |
|-----------------|------------------------------------------|
| Operador        | Executar conforme procedimento           |
| Supervisor      | Validar e registrar as OSs               |
| Coordenador     | Garantir conformidade geral do processo  |

---

## 6. REGISTROS E EVIDÊNCIAS

Todos os registros devem ser:

- Preenchidos de forma legível e completa
- Assinados pelo responsável pela execução
- Arquivados pelo prazo mínimo de 5 anos

<!-- page 5: empty -->
```

---

## Checklist de transformações aplicadas

| Transformação                          | Antes                          | Depois               |
|----------------------------------------|--------------------------------|----------------------|
| Trailing whitespace removido           | `"Operações   "`               | `"Operações"`        |
| Heading sem espaço corrigido           | `"#MANUAL"`                    | `"# MANUAL"`         |
| Heading sem espaço corrigido           | `"##2. ESCOPO"`                | `"## 2. ESCOPO"`     |
| Bullets `*` → `-`                      | `"* Equipe de produção"`       | `"- Equipe de produção"` |
| Bullets `+` → `-`                      | `"+ Equipe de logística"`      | `"- Equipe de logística"` |
| Separador `===...` → `---`             | `"==========================="`| `"---"`              |
| Separador `* * *` → `---`              | `"* * *"`                      | `"---"`              |
| Separador `_ _ _` → `---`             | `"_ _ _"`                      | `"---"`              |
| Linha pontilhada removida              | `"................."`           | *(linha removida)*   |
| Linhas em branco excessivas colapsadas | 4+ linhas em branco seguidas   | máx. 2 linhas        |
| Marcador de página preservado          | `"<!-- page 1 -->"`            | `"<!-- page 1 -->"` (intocado) |
| Marcador vazio preservado              | `"<!-- page 5: empty -->"`     | `"<!-- page 5: empty -->"` (intocado) |
