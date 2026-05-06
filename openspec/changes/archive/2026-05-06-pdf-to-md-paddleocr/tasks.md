# Tasks: PDF to Markdown com PaddleOCR

## 1. Implementar o Serviço Base `pdf-to-md`
- [x] Confirmar ou criar a estrutura da skill `pdf-to-md` em `platform/skills/pdf-to-md/`, mantendo `platform/skill-runtime/` apenas como runtime canônico.
- [x] Implementar leitura de um arquivo PDF via `PyMuPDF` sem processamento de OCR.
- [x] Configurar para salvar o arquivo `.md` bruto concatenado em disco (`var/`).
- **Critério de conclusão**: A skill consegue receber um PDF digital simples via runtime canônico, extrair seu texto base iterativamente pelo PyMuPDF e salvar no arquivo Markdown de saída.

## 2. Injeção de Anchors e Preservação de Ordem
- [x] Modificar o laço de iteração de páginas no PyMuPDF para emitir e anexar uma âncora delimitadora de formato `[[Pág. N]]` a cada virada de página.
- **Critério de conclusão**: Todo output Markdown gerado pelo pipeline possui as âncoras exatas de página, ordenadas corretamente de 1 até a página final do documento original.

## 3. Implementar Heurística de Densidade Textual
- [x] Criar função de avaliação de página que calcula a proporção/quantidade de caracteres de texto útil extraídos na leitura direta.
- [x] Definir o threshold limitante de fallback para decidir dinamicamente se a página será tratada como texto validado ou será enviada para OCR.
- **Critério de conclusão**: A função classifica corretamente e de forma determinística quais páginas possuem texto nativo suficiente e quais exigem OCR em um documento híbrido de teste.

## 4. Integração do OCR Fallback com PaddleOCR
- [x] Quando uma página for reprovada na heurística, invocar rotina de conversão dessa página do PDF para imagem isolada.
- [x] Enviar a imagem gerada ao PaddleOCR (versão: **A definir**) para extração do texto bruto pela imagem.
- [x] Capturar a resposta textual do OCR e concatená-la ao documento final, logo após sua respectiva âncora de página.
- **Critério de conclusão**: Uma página completamente escaneada ou imagem que seria tratada como "vazia", resulta em um Markdown contendo o respectivo texto detectado pelo PaddleOCR abaixo de sua âncora `[[Pág. N]]`.

## 5. Validação E2E no Runtime
- [x] Orquestrar o processamento híbrido (texto nativo + imagens escaneadas no mesmo PDF) com a skill.
- [x] Verificar o armazenamento correto na pasta operante.
- **Critério de conclusão**: Execução livre de erros capaz de converter um PDF híbrido completo resultando em um MD puramente textual com todas as páginas preservadas, prontas para as etapas subsequentes do projeto, mas isento de processamento extra de outlines ou RAG.
