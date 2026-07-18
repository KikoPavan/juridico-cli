## Why

Em documentos jurídicos reais (ex.: contestação, evento 43, processo
4000153-37.2026.8.26.0136/SP), a skill `md-frontmatter-yaml` gera `title` e
`author` de baixa qualidade: o `title` captura uma linha longa e truncada de
descrição da ação (heading H1 espúrio produzido pela conversão PDF→Markdown),
e o `author` fica `null` mesmo quando a parte apresentante da peça está
claramente identificada no início do corpo. Isso reduz a utilidade dos
metadados para indexação e busca posterior.

## What Changes

- Adicionar heurística de detecção de `title` para tipos de peça jurídica
  conhecidos: quando `document_type` indicar uma peça processual (iniciando
  por `contestacao_processo`) e existir uma linha explícita e curta com o
  nome do tipo de peça (ex.: linha isolada `CONTESTAÇÃO`), essa linha deve
  prevalecer como `title` sobre um H1 capturado no corpo que seja
  claramente um trecho de texto corrido (heading longo/truncado de conversão
  PDF, não um título de peça).
- Adicionar heurística de detecção de `author` a partir do padrão de abertura
  típico de petições brasileiras: nome da parte em caixa alta (com sufixo
  societário como `S.A.`, `LTDA`, etc.) seguido de qualificação e verbo de
  protocolo (`vem ... apresentar`), usada apenas quando não houver rótulo
  explícito (`Autor:`, `Responsável:` etc.) nem dado de locator judicial.
- Manter todas as garantias existentes: o corpo do Markdown não é alterado
  (preservação byte-a-byte ao remover o frontmatter), `document_date`
  permanece `null` na ausência de data confiável, e nenhuma heurística usa
  LLM.
- Adicionar testes cobrindo o caso real de contestação (título "CONTESTAÇÃO"
  e autor "BANCO DO BRASIL S.A.") e um teste de preservação de corpo
  baseado no par de arquivos `clean/` vs `frontmatter/` do caso real.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `md-frontmatter-yaml`: os requisitos de detecção de `title` e `author`
  passam a incluir heurísticas específicas para peças jurídicas
  (contestação), aplicadas antes do fallback genérico existente (H1 puro /
  rótulo explícito / `null`).

## Impact

- `platform/skills/md-frontmatter-yaml/scripts/apply_frontmatter.py`
  (funções `_detect_title` e/ou `_detect_author`, ou nova função auxiliar
  específica para peças jurídicas)
- `platform/skills/md-frontmatter-yaml/scripts/test_frontmatter_yaml.py`
  (novos testes unitários e de preservação de corpo)
- Não afeta `pdf-to-md`, `md-clean-markdown`, OCR, ou integração
  Gemini/JSON.
