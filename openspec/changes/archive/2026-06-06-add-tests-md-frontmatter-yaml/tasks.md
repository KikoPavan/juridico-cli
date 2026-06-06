## 1. Setup e Estrutura Inicial do Teste

- [ ] 1.1 Criar o arquivo de teste `platform/skills/md-frontmatter-yaml/scripts/test_frontmatter_yaml.py`
- [ ] 1.2 Configurar os imports e o path setup necessários para carregar `apply_frontmatter.py` e `validate_output.py` no pytest

## 2. Implementação das Asserções e Cenários de Teste

- [ ] 2.1 Criar caso de teste para garantir a preservação do corpo do Markdown byte a byte após aplicar frontmatter
- [ ] 2.2 Criar caso de teste para garantir a preservação de marcadores de página `[[Pág. N]]` e `<!-- page N -->` no corpo final
- [ ] 2.3 Criar caso de teste para verificar que `_detect_title()` funciona e ignora marcadores de página na mesma linha do H1 (ex: `[[Pág. 1]] # Título`)
- [ ] 2.4 Criar casos de teste para verificar a detecção de datas nos múltiplos formatos aceitos (DD/MM/YYYY, YYYY-MM-DD, DD de Mês de YYYY, Mês YYYY)
- [ ] 2.5 Criar casos de teste para verificar a detecção de autores por rótulos (Responsável, Autor, Elaborado por, Autora)
- [ ] 2.6 Criar caso de teste para garantir que a execução aborta com código de saída 2 se o arquivo Markdown de entrada já contiver frontmatter
- [ ] 2.7 Criar caso de teste para asseverar a validade da sintaxe do bloco YAML gerado no arquivo de saída
- [ ] 2.8 Criar caso de teste de integração que invoca `validate_output.py` em modo `--strict` no arquivo gerado e valida se o retorno é 0

## 3. Execução e Validação

- [ ] 3.1 Executar a nova suíte de testes usando `uv run pytest platform/skills/md-frontmatter-yaml/` e garantir que todos passem
- [ ] 3.2 Executar a suíte de testes global `uv run pytest` e certificar-se de que nenhuma regressão foi introduzida no projeto
