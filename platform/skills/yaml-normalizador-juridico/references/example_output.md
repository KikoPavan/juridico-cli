---
piece_id: peca_001
document_type: peticao_inicial
skill_key: extr-peticao-processo
source_file: processo_1234567-89_2024_SP.pdf
source_path: /data/processos/2024/sp/processo_1234567-89_2024_SP.pdf
source_sha256: a3f5e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3
pages_start: 3
pages_end: 4
process_group_id: proc-2024-0042
origin_piece_index: 0
acao_curatorial: manter
priority: 1
impacto_processual: nuclear
impacto_sentenca_confirmado: true
review_status: approved
status: ready
language: pt-BR
created_by_skill: yaml-normalizador-juridico
normalized_at: '2026-04-11T18:19:15-03:00'
title: Petição Inicial — Ação de Cobrança
document_date: '2024-08-15'
parties_normalized:
- JOAO DA SILVA
- EMPRESA XYZ LTDA
court: Vara Cível da Comarca de São Paulo
judge: null
tags:
- impacto_sentenca
- prioridade_alta
notes: Peça fundamental — contém causa de pedir e pedidos constitutivos do processo.
audit_trail:
- stage: segmentador-juridico
  timestamp: '2024-08-15T10:00:00Z'
  action: segmento_classificado
  notes: 'Confiança: 0.99; tipo: peticao_inicial'
- stage: curador-relevancia
  timestamp: '2024-08-15T10:05:32Z'
  action: decisao_curatorial_aplicada
  notes: acao=manter; impacto=nuclear; prioridade=1
- stage: yaml-normalizador-juridico
  timestamp: '2026-04-11T18:19:15-03:00'
  action: frontmatter_gerado
  notes: skill_key=extr-peticao-processo; review_status=approved
---

EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ___ VARA CÍVEL DA COMARCA DE SÃO PAULO

JOÃO DA SILVA, brasileiro, casado, empresário, portador do CPF nº 000.000.000-00, residente e domiciliado na Rua das Flores, nº 100, Bairro Jardim América, São Paulo/SP, CEP 01000-000, por intermédio de seus advogados abaixo assinados, vem à presença de Vossa Excelência propor a presente

AÇÃO DE COBRANÇA

EM FACE DE

EMPRESA XYZ LTDA., pessoa jurídica de direito privado, inscrita no CNPJ sob o nº 00.000.000/0001-00, com sede na Av. Paulista, nº 1000, São Paulo/SP, CEP 01310-100, pelos fatos e fundamentos a seguir expostos.

I — DOS FATOS

O Autor celebrou contrato de prestação de serviços com a Ré em 01 de março de 2024, pelo valor total de R$ 50.000,00 (cinquenta mil reais), conforme instrumento anexo (doc. 01).

Apesar da entrega integral dos serviços contratados em 30 de abril de 2024, a Ré deixou de efetuar o pagamento na data avençada de 05 de maio de 2024.

II — DO DIREITO

O inadimplemento da Ré configura infração contratual, ensejando a cobrança judicial nos termos dos arts. 389, 395 e 396 do Código Civil.

III — DOS PEDIDOS

Ante o exposto, requer:
a) a citação da Ré;
b) a procedência do pedido para condenação ao pagamento de R$ 50.000,00, acrescidos de correção monetária, juros moratórios de 1% ao mês desde o vencimento e honorários advocatícios;
c) a condenação nas custas processuais.

Dá-se à causa o valor de R$ 50.000,00.

São Paulo, 15 de agosto de 2024.

[Assinatura]
Dr. Carlos Mendes
OAB/SP 123.456
