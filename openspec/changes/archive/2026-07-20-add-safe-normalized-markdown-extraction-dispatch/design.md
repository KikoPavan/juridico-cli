## Context

`run_collect_stage()` encontra os Markdown normalizados no staging, mas hoje combina três políticas incompatíveis com a nova esteira: consulta mapas legados, infere um bundle a partir de `document_type` e chama `DataExtractorApp.run_extraction()` apenas com o nome do arquivo. O extrator volta a procurar esse nome em diretórios fixos, resolve a skill pelo dispatcher e persiste diretamente o retorno de `generate_structured()`.

A fronteira segura precisa abranger o adaptador da etapa e o extrator, sem duplicar `SkillDispatcher`, sem tornar mapas de collectors canônicos e sem romper consumidores legados. A implementação deve consultar o Documento Mestre, o Runbook Operacional Mínimo e a Matriz de Versões antes de introduzir qualquer dependência; a preferência é reutilizar o validador JSON Schema já presente no ambiente do projeto.

## Goals / Non-Goals

**Goals:**

- Filtrar os arquivos antes do LLM por `status`, `review_status` e `skill_key` do frontmatter.
- Aceitar somente `skill_key` explícito no formato `extr-*` e resolvê-lo pelo `SkillDispatcher` canônico.
- Tornar recusas auditáveis e não fatais para o lote.
- Encaminhar ao extrator o `Path` exato encontrado no staging.
- Validar a resposta do LLM pelo `schema_ref` resolvido antes da gravação e da sinalização de sucesso.
- Preservar a forma legada `run_extraction(bundle_id, input_filename)`.
- Cobrir o fluxo com doubles determinísticos e sem rede.

**Non-Goals:**

- Adotar Outlines ou trocar o cliente LLM.
- Criar outro dispatcher, registry ou runtime de skills.
- Migrar diretórios, módulos funcionais ou a arquitetura transitória de `apps/data-processing`.
- Remover fallbacks de localização usados por chamadas legadas.
- Tornar mapas antigos dos collectors fonte de verdade para a nova esteira.

## Decisions

### 1. Aplicar um gate explícito no adaptador de coleta

Para cada Markdown descoberto, `run_collect_stage()` fará parse defensivo do frontmatter e somente seguirá quando `status == "ready"`, `review_status == "approved"` e `skill_key` for uma string iniciada por `extr-`. `REVISAR_MANUAL`, `needs_review`, `unroutable`, metadados ausentes ou malformados e qualquer outro estado não aprovado produzirão log com arquivo e motivo, continuarão o lote e não instanciarão/chamarão o cliente LLM.

O `skill_key` será usado literalmente como `bundle_id`. Não haverá consulta a `routing.map`, conversão de underscores nem derivação por `document_type` nesse caminho. Isso mantém o frontmatter do `yaml-normalizador-juridico` como única decisão de rota da nova esteira. Alternativa rejeitada: manter a inferência como conveniência, pois ela transforma classificação documental em autorização para executar uma skill que pode não existir.

### 2. Usar o dispatcher canônico como validação de registro

A existência e a configuração da skill serão comprovadas por `SkillDispatcher.dispatch(skill_key)`. Uma skill ausente será rejeitada de forma controlada, registrada e isolada ao arquivo atual. O fluxo não lerá diretamente mapas de collectors para suprir ou corrigir o identificador.

Para evitar resolução duplicada, `DataExtractorApp` continuará responsável pelo dispatch que fornece prompt, perfil e `schema_ref`; o adaptador apenas fornecerá a rota explícita e tratará a falha controlada devolvida/lançada pelo extrator. Testes poderão injetar um fake dispatcher e um fake client por seams mínimos de construção, sem criar abstração de runtime paralela.

### 3. Adicionar caminho explícito sem quebrar a assinatura legada

`run_extraction()` ganhará um parâmetro opcional por palavra-chave para o caminho de entrada (por exemplo, `input_path`). Quando presente, esse caminho será usado diretamente e deverá apontar para arquivo legível. Quando ausente, a busca atual por `input_filename` em `md-frontmatter-yaml`, `processed` e `processed_fm` será preservada na mesma precedência.

`run_collect_stage()` passará tanto o `input_filename` compatível quanto o caminho explícito do `md_file`. Alternativa rejeitada: copiar o staging para um diretório fixo, pois cria I/O e estado intermediário desnecessários e pode extrair uma cópia obsoleta.

### 4. Validar uma cópia estável da resposta antes de persistir

Após `generate_structured()`, o extrator validará o objeto contra o JSON Schema carregado do `schema_ref` retornado pelo dispatcher. Campos auxiliares internos, como `_failed_blocks`, poderão ser separados sem mutar inadvertidamente o objeto do fake/cliente; o payload destinado à persistência é o mesmo payload validado.

Falha de validação produzirá log com erros úteis, não criará/substituirá o arquivo de resultado válido, não emitirá mensagem de conclusão bem-sucedida e será representada por exceção específica/controlada ou retorno inequívoco que `run_collect_stage()` capture por arquivo. A validação ocorrerá antes de abrir o destino para escrita, evitando truncar um resultado válido anterior. Alternativa rejeitada: confiar apenas em `generate_structured(schema=...)`, pois a implementação do provedor não constitui validação local explícita nem garante comportamento uniforme entre clientes.

### 5. Testar contratos observáveis com doubles

Os testes usarão diretórios temporários, fake dispatcher e fake LLM client. As asserções observarão chamadas (ou ausência delas), bundle recebido, caminho efetivamente lido, arquivo persistido, conteúdo validado, logs/resultado controlado e compatibilidade posicional legada. Nenhum teste dependerá de Gemini, credenciais ou rede.

## Risks / Trade-offs

- [Frontmatter antigo sem os novos estados deixa de extrair na nova esteira] → restringir o gate ao fluxo de Markdown normalizado e manter a API/localização legada do extrator.
- [Captura ampla pode esconder defeitos reais] → capturar no lote apenas falhas esperadas de rota, arquivo e schema, com motivo auditável; erros inesperados permanecem visíveis.
- [Schema com referência ou dialeto específico pode exigir configuração adicional] → reutilizar a biblioteca e o comportamento JSON Schema já adotados no repositório e testar schemas reais representativos.
- [Arquivo de saída pré-existente pode ser confundido com novo sucesso] → validar antes da escrita e não tocar no arquivo em caso de resposta inválida; logs devem identificar claramente a tentativa rejeitada.
- [Alterar parâmetros pode quebrar mocks ou consumidores] → adicionar somente parâmetro opcional keyword, preservando os dois argumentos posicionais atuais.

## Migration Plan

1. Introduzir testes do gate e da compatibilidade legada.
2. Adicionar o caminho explícito opcional e manter a resolução legada como fallback.
3. Remover somente do fluxo novo a inferência de extrator e passar o caminho de staging.
4. Adicionar validação pré-persistência e tratamento controlado por arquivo.
5. Executar validações OpenSpec e a suíte completa de `apps/data-processing/tests`.

Rollback consiste em reverter as alterações de aplicação e testes; não há migração de dados, registro ou diretório. Resultados já válidos permanecem no lugar.

## Open Questions

Nenhuma decisão bloqueante. Durante a implementação, o nome exato da exceção/resultado controlado e o seam de injeção dos doubles devem seguir os padrões já existentes no módulo, sem ampliar a API além do necessário.
