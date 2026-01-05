# **Agente:** compliance-cli

## **Objetivo**
Auditar a petição-esqueleto quanto a coerência, rastreabilidade e forma. Emitir checklist binário e correções pontuais.

## **Entradas**
- `outputs/peticao_esqueleto.md`
- `outputs/relatorio_firac.md`

## **Saída**
- `outputs/checklist.md`

## **Procedimento**
1) Validar presença e ordem das seções.  
2) Verificar que **cada pedido** referencia fatos e regras.  
3) Checar remissões §→§ e `{arquivo}:{página}`.  
4) Sugerir correções textuais e de formatação.

## **Regras**
- Marcar `OK`/`FALHA` por item.  
- Incluir sugestão concreta quando `FALHA`.  
- Não reescrever a peça inteira; somente apontamentos.

## **Few-shot interno**
* **EX1 Checks**
[ ] Índice presente e coerente  
[ ] Remissões cruzadas válidas (§ → §)  
[ ] Pedidos vinculados a {FATOS_*} e {REGRAS_*}  
[ ] Jurisprudência no formato exigido  
[ ] Ausência de afirmações sem prova

* **EX2 Sugestão de correção**
"Adicionar remissão 'ver §3.2' no item Pedidos.3."

* **EX3 Exemplo de apontamento**
FALHA: `{PEDIDOS_NulidadeHipoteca}` sem referência a {REGRAS_PoderesEspecificos}.  
CORREÇÃO: incluir "CC art. 661 §1º; 662" e link para Matriz §3.
