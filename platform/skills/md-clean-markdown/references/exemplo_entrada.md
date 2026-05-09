# Exemplo de Entrada — md-clean-markdown

Markdown bruto típico após conversão de PDF por `pdf-to-md`.
Contém ruído visual e inconsistências de formatação comuns.

Baseado no arquivo real `var/output/pdf-to-md/arquivo_escaneado.md`.

---

## Metadados do exemplo

| Campo         | Valor                                                   |
|---------------|---------------------------------------------------------|
| Nome fictício | `registro_imovel_bruto.md`                              |
| Tipo          | Certidão de registro imobiliário (genérico)             |
| Origem        | Saída real de pdf-to-md com marcadores [[Pág. N]]       |

---

## Conteúdo bruto simulado

O texto abaixo representa o conteúdo como saído de `pdf-to-md` —
com marcadores `[[Pág. N]]`, espaços finais, linhas excessivas em branco,
bullets inconsistentes e separadores variados.

O exemplo também inclui um marcador legado `<!-- page N -->` para demonstrar
compatibilidade retroativa.

```
[[Pág. 1]]

#CERTIDÃO DE REGISTRO IMOBILIÁRIO   

Número: 9.405 — Comarca de Cerqueira César, Estado de São Paulo   
Data de emissão: 14 de fevereiro de 2024   



===========================

##2. DESCRIÇÃO DO IMÓVEL

IMÓVEL : Um imóvel residencial e comercial, situado nesta cidade,   
à Rua J.J. Esteves, n. 117, construído de tijolos e coberto de telhas,   
com seis cômodos.   


* Frente: 12,00 metros para a referida rua   
+ Profundidade: 30,00 metros da frente aos fundos   
* Área total: 360,00 m²   


<!-- page 2 -->

##3. PROPRIETÁRIO

JURACI PIRES PAVAN, viúva, do lar, portadora da cédula de identidade   
RG n.4.294.873-SSP/SP, inscrita no CPF/MF sob n. 793.933.908-78.   



===========================

[[Pág. 3]]

##4. HISTÓRICO DE AVERBAÇÕES

Av.1 — Hipoteca Cedular (14/06/1999)   
Av.2 — Cancelamento de Hipoteca (26/07/2002)   
Av.3 — Incorporação Imobiliária (18/01/2002)   
Av.4 — Bloqueio Judicial de Bens (29/03/2018)   


```

---

## Problemas de formatação presentes

1. `[[Pág. 1]]` e `[[Pág. 3]]` — marcadores primários (devem ser preservados intactos)
2. `<!-- page 2 -->` — marcador legado (deve ser preservado intacto)
3. `#CERTIDÃO` e `##2.` — headings sem espaço após `#`
4. `* Item` e `+ Item` — bullets não normalizados
5. `===========================` — separador não-padrão (deve virar `---`)
6. Trailing whitespace em múltiplas linhas
7. Três ou mais linhas em branco consecutivas
