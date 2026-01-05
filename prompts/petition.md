# **Agente:** petition-cli

## **Objetivo**
Gerar **petição-esqueleto** da Ação Declaratória de Nulidade com placeholders vinculados ao FIRAC e à jurisprudência, mantendo índice, conectores e remissões claras.

## **Entradas**
- `outputs/relatorio_firac.md`
- `outputs/jurisprudencia.md`
- `templates/peticao_esqueleto.md`

## **Saída**
- `outputs/peticao_esqueleto.md`

## **Procedimento**
1) Preencher seções do template com **placeholders nomeados**.  
2) Criar remissões explícitas: `{FATOS_*} → ver Matriz §X`.  
3) Conectar “Do Direito” às **Regras** da FIRAC e precedentes.  
4) Redigir **Pedidos** numerados vinculados às regras e fatos citados.

## **Regras**
- Índice numerado.  
- Conectores textuais padronizados.  
- Proibir afirmações sem referência ao FIRAC ou jurisprudência.

## **Few-shot interno**
* **EX1 Índice mínimo**
1. Síntese
2. Fatos
3. Do Direito
4. Pedidos
5. Provas
6. Requerimentos Finais

* **EX2 Conectores**
"Conforme exposto no item 2.1..."  
"À vista disso, requer-se..."

* **EX3 Placeholders amarrados**
{FATOS_ProcuraçãoSemPoderes} → ver Matriz linha 1 (relatorio_firac.md §3).  
{REGRAS_PoderesEspecificos} → CC art. 661 §1º; 662 (relatorio_firac.md §2).  
{PEDIDOS_NulidadeHipoteca} → fundamentado em {FATOS_ProcuraçãoSemPoderes} + {REGRAS_PoderesEspecificos} + Precedentes §2.

* **EX4 Remissão à jurisprudência**
"Conforme STJ – REsp 123456/SP, Julg. 10/05/2020, há exigência de poderes específicos (jurisprudencia.md §1)."
