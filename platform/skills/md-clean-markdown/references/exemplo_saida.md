# Exemplo de Saída — md-clean-markdown

Markdown limpo esperado após processamento de `registro_imovel_bruto.md`
(ver `exemplo_entrada.md`).

---

## Metadados do exemplo

| Campo         | Valor                                                   |
|---------------|---------------------------------------------------------|
| Nome fictício | `registro_imovel_limpo.md`                              |
| Tipo          | Saída de md-clean-markdown sobre certidão imobiliária   |
| Garantias     | Marcadores [[Pág. N]] e <!-- page N --> preservados     |

---

## Conteúdo limpo

```
[[Pág. 1]]

# CERTIDÃO DE REGISTRO IMOBILIÁRIO

Número: 9.405 — Comarca de Cerqueira César, Estado de São Paulo
Data de emissão: 14 de fevereiro de 2024

---

## 2. DESCRIÇÃO DO IMÓVEL

IMÓVEL : Um imóvel residencial e comercial, situado nesta cidade,
à Rua J.J. Esteves, n. 117, construído de tijolos e coberto de telhas,
com seis cômodos.

- Frente: 12,00 metros para a referida rua
- Profundidade: 30,00 metros da frente aos fundos
- Área total: 360,00 m²

<!-- page 2 -->

## 3. PROPRIETÁRIO

JURACI PIRES PAVAN, viúva, do lar, portadora da cédula de identidade
RG n.4.294.873-SSP/SP, inscrita no CPF/MF sob n. 793.933.908-78.

---

[[Pág. 3]]

## 4. HISTÓRICO DE AVERBAÇÕES

Av.1 — Hipoteca Cedular (14/06/1999)
Av.2 — Cancelamento de Hipoteca (26/07/2002)
Av.3 — Incorporação Imobiliária (18/01/2002)
Av.4 — Bloqueio Judicial de Bens (29/03/2018)
```

---

## Transformações aplicadas

| Problema na entrada                       | Resultado na saída                        |
|-------------------------------------------|-------------------------------------------|
| `[[Pág. 1]]` e `[[Pág. 3]]`             | Preservados **intactos** (marcador primário) |
| `<!-- page 2 -->`                         | Preservado **intacto** (marcador legado)  |
| `#CERTIDÃO` (sem espaço)                 | `# CERTIDÃO` (espaço normalizado)         |
| `##2.` e `##3.` e `##4.` (sem espaço)   | `## 2.` / `## 3.` / `## 4.`             |
| `* Item` e `+ Item`                       | `- Item` (bullets normalizados)           |
| `===========================`             | `---` (separador normalizado)             |
| Trailing whitespace nas linhas            | Removido                                  |
| 3+ linhas em branco consecutivas          | Colapsado para máximo de 2                |

---

## Invariante de marcadores

Todos os marcadores de página presentes na entrada aparecem inalterados na saída:

- `[[Pág. 1]]` ✓ preservado na linha 1
- `<!-- page 2 -->` ✓ preservado
- `[[Pág. 3]]` ✓ preservado
