## Context

A skill `md-frontmatter-yaml` está localizada em `platform/skills/md-frontmatter-yaml/` e é estruturada de forma modular, contendo o script de aplicação `apply_frontmatter.py` e o de validação `validate_output.py`. Atualmente, a skill só possui verificação ponta a ponta manual através do script `run_example.sh`. Não há testes automatizados integrados com `pytest`, o que impossibilita a detecção automatizada de regressões em nível de CI.

## Goals / Non-Goals

**Goals:**
- Criar a suíte de testes unitários e de integração baseada em `pytest` no arquivo `platform/skills/md-frontmatter-yaml/scripts/test_frontmatter_yaml.py`.
- Garantir 100% de cobertura dos cenários críticos de negócio descritos na especificação `spec.md`.
- Executar os testes automaticamente sob o comando global `uv run pytest`.

**Non-Goals:**
- Alterar o comportamento ou a lógica de outras skills (como `pdf-to-md` ou `md-clean-markdown`).
- Modificar o orquestrador `stage_router.py` ou qualquer fluxo de execução em `apps/data-processing/`.
- Reescrever a lógica interna de `apply_frontmatter.py` ou `validate_output.py`, a menos que um bug crítico seja identificado pelos novos testes.

## Decisions

### Decisão 1: Abordagem de Testes com Pytest
**Escolha:** Utilizar chamadas de funções diretas e simulação de CLI via invocação programática do `main()` em pytest, combinando com a fixture `tmp_path` nativa para isolamento de arquivos de teste de entrada/saída.

**Alternativas consideradas:**
1. *Executar como subprocesso*: Usar `subprocess.run` para chamar os scripts python.
   *Raciocínio de descarte*: Execuções como subprocesso são mais lentas e tornam a checagem de erros e mocks de imports mais complexos. A importação direta e a simulação usando mocks ou parametrização de argumentos são mais limpas e performáticas.

### Decisão 2: Cobertura de Testes
Os testes cobrirão os seguintes cenários estruturais:
1. **Preservação do Corpo**: Gravar arquivo com corpo arbitrário, rodar o apply e atestar que o corpo do arquivo final coincide byte a byte com o original.
2. **Preservação de Marcadores de Página**: Incluir marcadores `[[Pág. N]]` e `<!-- page N -->` no corpo e atestar que ambos constam intactos no arquivo de saída.
3. **Detecção de H1 com Marcadores**: Testar a função `_detect_title()` isoladamente e via CLI informando títulos precedidos por marcadores de página (ex: `[[Pág. 1]] # Título`) e validar se a detecção ignora os marcadores de forma limpa.
4. **Detecção de Datas**: Validar os 4 padrões descritos em `regras_frontmatter.md` (como `15/03/2024`, `2024-03-15`, `15 de março de 2024`, `março de 2024`).
5. **Detecção de Autor**: Testar a regex de detecção de autor para labels como `Responsável`, `Autor`, `Elaborado por`, `Autora`.
6. **Rejeição de Frontmatter Existente**: Tentar rodar o apply em arquivo que já inicia com `---` e certificar que o script aborta com código de saída 2 (`EXIT_ALREADY_HAS_FM`).
7. **YAML Válido**: Validar que o YAML gerado pode ser carregado sem erros por `yaml.safe_load`.
8. **Strict Mode do Validador**: Invocar a rotina de validação de `validate_output.py` no modo `--strict` e asseverar que ela retorna código 0.

## Risks / Trade-offs

- **[Risco] Setup de imports de dependências** → O pytest executado na raiz do projeto pode ter problemas de path se as skills importarem módulos de forma relativa não configurada.
  *Mitigação*: Os scripts usam importações padrão da biblioteca nativa e `yaml`, e não dependem do runtime global. A adição do diretório da skill ou scripts ao `sys.path` durante o teste garante resoluções corretas.
