# Plano de Validação — Outlines

## Objetivo

Validar se o Outlines consegue ajudar a gerar uma saída JSON seguindo um schema simples.

## O que será testado

Será feito um teste mínimo com um JSON de metadados de documento.

O teste ainda não altera o projeto, não altera o runtime e não cria skill nova.

## Schema mínimo do teste

O JSON de saída deverá ter estes campos:

- document_type: texto
- language: texto
- has_legal_content: verdadeiro ou falso
- summary: texto

## Exemplo de saída correta

{
  "document_type": "petition",
  "language": "pt-BR",
  "has_legal_content": true,
  "summary": "Documento jurídico com conteúdo processual."
}

## Exemplo de saída errada

{
  "document_type": 123,
  "language": "pt-BR",
  "has_legal_content": "yes"
}

## Regra da validação

O Outlines só será aceito se ajudar a produzir JSON compatível com schema.

Outlines não substitui o schema.

Outlines não substitui o runtime de skills.

Outlines não será integrado ao projeto antes do teste mínimo funcionar.
