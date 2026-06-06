## Why

A skill `md-frontmatter-yaml` possui implementação funcional e teste de fumaça local (`run_example.sh`), mas carece de cobertura de testes automatizados dentro do framework principal de testes do projeto (`pytest`). Esta change visa garantir a robustez da skill contra regressões de marcadores de página e inferência de metadados, integrando-a formalmente à suíte de testes do repositório.

## What Changes

- **Novo arquivo de testes**: Criação do arquivo de testes unitários `platform/skills/md-frontmatter-yaml/scripts/test_frontmatter_yaml.py`.
- **Casos de teste cobertos**:
  - Preservação estrita do corpo do Markdown byte a byte.
  - Preservação de marcadores de página primários `[[Pág. N]]` e legados `<!-- page N -->` no corpo de saída.
  - Detecção correta de heading H1 mesmo quando precedido por marcadores na mesma linha.
  - Detecção correta de datas em múltiplos formatos comuns (como `DD/MM/YYYY`, `YYYY-MM-DD`, `DD de Mês de YYYY`, `Mês YYYY`).
  - Detecção correta de autor por rótulos (labels) comuns (ex: `Responsável`, `Autor`, `Elaborado por`).
  - Lançamento de erro (exit code 2) quando o arquivo de entrada já possui frontmatter.
  - Validação da sintaxe e estrutura do YAML final gerado.
  - Validação estrita por meio do validador integrado `validate_output.py`.

## Capabilities

### New Capabilities

*(Nenhuma capacidade nova de negócio está sendo introduzida, apenas cobertura de testes para a capacidade existente).*

### Modified Capabilities

- `md-frontmatter-yaml`: Sem alterações de requisitos, mas garante a conformidade com a especificação existente através de testes integrados ao `pytest`.

## Impact

- **Afetados**: `platform/skills/md-frontmatter-yaml/`.
- **Fora de impacto**: Nenhuma API pública, CLI, orquestrador (`stage_router.py`) ou outros componentes do monorepo serão alterados.
