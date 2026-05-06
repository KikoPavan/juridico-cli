# Design: PDF to Markdown com PaddleOCR

## Arquitetura do Pipeline

A capacidade canônica `pdf-to-md` deve residir em `platform/skills/pdf-to-md/` e ser resolvida pelo runtime canônico em `platform/skill-runtime/`. O pipeline recebe um documento PDF digital, escaneado ou híbrido, processa-o de forma iterativa e gera um arquivo Markdown bruto e rastreável. A saída final será armazenada nos diretórios operacionais padrão (ex: `var/`).

O fluxo obedece estritamente ao princípio de isolamento: o pipeline foca exclusivamente na conversão dos dados visuais/binários para texto. Ele não possui responsabilidades de estruturação em schemas, extração jurídica (legal-knowledge) ou RAG, atuando apenas como a camada inicial que viabilizará tais etapas posteriores.

## Fluxo Página a Página

1. **Leitura**: O pipeline utiliza a biblioteca **PyMuPDF** para abrir o arquivo de origem.
2. **Iteração Sequencial**: O documento é percorrido sequencialmente, mantendo a ordem original, página a página.
3. **Avaliação da Densidade Textual**:
   - O sistema tenta extrair o texto nativo diretamente via `PyMuPDF`.
   - É aplicada uma heurística de densidade textual que compara a quantidade de caracteres legíveis extraídos com os limites esperados de uma página válida.
4. **Execução da Extração**:
   - Se o texto ultrapassar o limite da heurística: o texto nativo é aceito como saída da página (conversão direta).
   - Se o texto falhar na heurística (texto muito curto, nulo, ou ilegível, indicativo de documento escaneado): a página específica é isolada, convertida para imagem (renderizada), e enviada ao motor OCR.
5. **Concatenação Final**: O conteúdo de cada página, independentemente do fluxo que tomou, é consolidado em um único documento final.

## Uso do PaddleOCR

O **PaddleOCR** é instituído apenas como mecanismo de fallback para OCR. Em vez de processar o PDF integralmente através do OCR (o que seria custoso e sujeito a erros), ele atua apenas sobre as páginas escaneadas/ilegíveis previamente marcadas pela heurística de baixa densidade textual.
*Nota*: A versão do PaddleOCR fica designada como **"A definir"** até validação na matriz de versões do projeto.

## Geração de Anchors

Para que etapas avançadas do sistema consigam auditar, vincular recortes ou justificar análises baseadas em páginas precisas do processo judicial:
- Uma âncora estruturada (anchor) é gerada automaticamente ao início da extração de cada página. Exemplo: `[[Pág. N]]`
- Estas âncoras funcionam como "save points" de rastreabilidade, embutidos discretamente no Markdown bruto resultante.
