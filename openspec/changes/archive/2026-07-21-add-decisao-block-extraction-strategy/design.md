## Context

O runtime já resolve estratégias de Extração por Blocos por `bundle_id` em `packages/shared-llm/block_strategies.py`. Petição e contestação possuem estratégias isoladas; bundles não registrados levantam `BlockExtractionStrategyUnavailableError` antes de uma chamada de bloco. `extr-decisao-processo` está registrado no runtime e recebe, conforme `routing_map.yaml`, `decisao`, `decisao_interlocutoria`, `sentenca` e `despacho`, porém ainda não consta no registro de estratégias.

O contrato de saída 1:1 de decisão aceita apenas `document_type`, `process_number`, `decision_type`, `decision_date`, `decisor`, `relatorio`, `fundamentacao`, `dispositivo`, `outcome`, `determinacoes` e `anchors`. O schema não possui propriedades independentes para partes, prazos, obrigações ou referências documentais. Portanto, a preservação dessas informações deve ocorrer como texto literal ancorado dentro da seção decisória apropriada, nunca pela introdução de chaves extras.

## Goals / Non-Goals

**Goals:**

- Selecionar uma estratégia exclusiva de decisão para `bundle_id="extr-decisao-processo"`.
- Extrair e consolidar somente propriedades do schema 1:1 canônico da skill.
- Preservar texto probatório e rastreabilidade, priorizando `judicial_locator` e marcadores reais do documento.
- Validar blocos quando aplicável e sempre validar o objeto final antes que ele possa alcançar a persistência.
- Degradar por bloco com fallback local explícito e conservador.
- Preservar sem alteração funcional petição, contestação, preflight Gemini e falha segura de bundles desconhecidos.

**Non-Goals:**

- Alterar qualquer `*.schema.json`, o registro de tipos documentais ou o preflight Gemini.
- Criar campos raiz para partes, prazos, obrigações ou referências documentais.
- Suportar procuração, mandato, cabeçalho, acórdão como tipo roteado novo ou qualquer bundle além de `extr-decisao-processo`.
- Alterar chamadas Gemini, parâmetros já validados ou introduzir uma chamada capaz de reproduzir `400 INVALID_ARGUMENT`.
- Executar, arquivar, commitar ou publicar a mudança nesta fase de proposta.

## Decisions

### 1. Estratégia única e registro explícito por bundle

Criar `DecisaoBlockStrategy` no módulo existente e associá-la somente à chave `extr-decisao-processo` em `BLOCK_STRATEGIES`. A estratégia reutiliza apenas helpers genéricos comprovadamente neutros (resolução local de schema, leitura do Markdown e parsing de marcadores), não blocos, prompts, defaults ou fallbacks das outras skills.

Alternativa rejeitada: parametrizar `PeticaoBlockStrategy` ou `ContestacaoBlockStrategy`. Isso aumenta o risco de chaves incompatíveis e viola o isolamento atual por skill.

### 2. Cinco blocos alinhados ao schema e à semântica da skill

Cada schema parcial inclui `document_type` e apenas as propriedades do bloco:

1. **Identificação**: `process_number`, `decision_type`, `decision_date`, `decisor`, `anchors`.
2. **Relatório**: `relatorio`.
3. **Fundamentação**: `fundamentacao`.
4. **Conclusão decisória**: `dispositivo`, `outcome`.
5. **Cumprimento**: `determinacoes` — inclui apenas trechos explícitos de intimações, prazos, obrigações, expedições, perícias e remessas.

Partes e referências documentais são preservadas quando aparecem literalmente no relatório, fundamentação, dispositivo ou determinações. Elas não geram propriedades próprias. O prompt de cada bloco explicita o subconjunto permitido e a exigência de omitir dados não evidenciados.

Alternativa rejeitada: um bloco por campo. Isso fragmenta contexto jurídico correlacionado (especialmente dispositivo/outcome e determinações/prazos) e multiplica chamadas sem ganho de contrato.

### 3. Tipos de entrada separados do `document_type` de saída

A elegibilidade operacional é limitada aos quatro tipos do `routing_map.yaml`: `decisao`, `decisao_interlocutoria`, `sentenca` e `despacho`. O payload final continua usando `document_type: "decisao_processo"`, conforme `const` do schema. A estratégia não amplia o mapa; apenas processa o bundle já resolvido pelo pipeline.

### 4. Validação em duas camadas e consolidação allowlist

Cada resposta de bloco é parseada, higienizada e validada contra seu schema parcial normalizado antes do merge. Respostas parciais incompatíveis acionam fallback daquele bloco e são registradas em log. A consolidação copia somente chaves presentes em `schema.properties`, ignora metadados internos e valida o objeto inteiro pelo resolvedor/validador local oficial antes de retornar.

Como o `anyOf` raiz atravessa blocos, ele é aplicado na validação final; schemas parciais aplicam tipos, propriedades, requireds locais e defs relevantes, sem exigir que um bloco isolado satisfaça o `anyOf` global. Resultado final inválido levanta erro e nunca é retornado ao `DataExtractorApp`, portanto não é persistido.

### 5. Fallback literal, localizado e sem páginas inventadas

O fallback procura somente evidência literal: identificadores explícitos e seções reconhecíveis por cabeçalhos/verbos decisórios. Ele pode omitir o campo ou produzir lista vazia quando o schema permitir. Não resume nem cria fundamentos, dispositivo, determinações, prazos ou obrigações. Cada ativação registra o nome do bloco e a causa.

Uma âncora só é criada quando houver simultaneamente quote literal e marcador real aplicável. O `page_marker` preserva o marcador encontrado (`[[judicial_locator: ...]]`, `[[Pág. N]]`, comentário legado ou folha literal compatível); se não houver marcador confiável, o fallback omite o item/campo que exigiria anchor em vez de usar `"1"`, `"[]"` ou outro valor fabricado. Marcadores válidos recebidos do modelo são preservados; marcadores inválidos tornam a resposta parcial inválida e acionam fallback seguro.

Alternativa rejeitada: usar página `1` como default. Embora seja simples, cria rastreabilidade falsa e contraria o requisito operacional.

### 6. Testes com fake client e teste operacional separado

Os testes automatizados exercitam seleção, schemas parciais, merge, fallback e validação com fake client, sem rede. O caso real localizado para a etapa operacional pós-implementação é `var/output/processed/DESPACHO-DECISÃO_evento_32.md`, que contém três `judicial_locator` e está disponível pelo caminho esperado pelo CLI.

Após toda a suíte automatizada passar e com `GEMINI_API_KEY` configurada, o comando operacional exato será:

```bash
PYTHONPATH=apps/data-processing/src:packages/shared-llm uv run python -m data_processing.cli extract --bundle extr-decisao-processo --input 'DESPACHO-DECISÃO_evento_32.md'
```

O resultado produzido deverá então ser validado com `platform/skills/extr-decisao-processo/scripts/validate_output.py`. A mudança não será arquivada antes desse teste real.

## Risks / Trade-offs

- [O schema não modela partes, prazos, obrigações e referências como campos dedicados] → preservar somente os trechos literais nas propriedades permitidas e documentar que a mudança não pode criar semântica inexistente sem alteração futura do schema.
- [Schemas parciais podem perder restrições globais como `anyOf`] → validar restrições locais por bloco e obrigatoriamente validar o payload consolidado completo.
- [Fallback por cabeçalhos pode não reconhecer decisões sem estrutura editorial] → omitir dados não comprovados e deixar a validação final falhar com segurança se o mínimo do schema não puder ser satisfeito.
- [Sanitização genérica atual aceita substituir marcador inválido por página estimada] → a estratégia de decisão deve adotar política mais estrita, baseada em marcador real, sem mudar o comportamento legado das estratégias existentes.
- [Prompts muito extensos podem reencontrar limites do Gemini] → usar schemas parciais mínimos e o fluxo de chamada já existente, sem modificar preflight, configuração ou parâmetros.
- [Mudanças no módulo compartilhado podem afetar estratégias existentes] → limitar o diff ao acréscimo da classe/registro e executar testes direcionados e a suíte completa exigida.
