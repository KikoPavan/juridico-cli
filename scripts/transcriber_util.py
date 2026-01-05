import logging
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [TRANSCRIBER] %(message)s"
)
logger = logging.getLogger(__name__)


class PDFTranscriber:
    def __init__(self, output_dir: str = "data/anexos"):
        """
        Utilitário para converter PDFs em Markdown com paginação explícita.

        Args:
            output_dir: Pasta onde os arquivos .md serão salvos.
        """
        self.output_path = Path(output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def convert(self, pdf_path: str, filename_output: Optional[str] = None) -> str:
        """
        Converte um PDF para Markdown inserindo marcadores de folha.

        Args:
            pdf_path: Caminho do arquivo PDF original.
            filename_output: Nome do arquivo de saída (opcional).

        Returns:
            Caminho do arquivo .md gerado.
        """
        input_file = Path(pdf_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

        # Define nome de saída
        if not filename_output:
            filename_output = input_file.stem + ".md"

        target_file = self.output_path / filename_output

        logger.info(f"Iniciando conversão de '{input_file.name}'...")

        try:
            # Abre o PDF
            doc = fitz.open(input_file)
            markdown_content = []

            # Cabeçalho do Documento
            markdown_content.append(f"# Documento: {input_file.name}")
            markdown_content.append(f"**Total de Páginas:** {len(doc)}\n")
            markdown_content.append("---\n")

            # Itera sobre as páginas para extrair texto mantendo a referência da folha
            for page_number in range(len(doc)):
                page = doc[page_number]
                text = page.get_text()

                # --- O PULO DO GATO DA ANCORAGEM ---
                # Inserimos um marcador claro antes do texto da página
                header = f"\n\n## [[Folha {page_number}]]\n"

                markdown_content.append(header)
                markdown_content.append(text)
                markdown_content.append("\n---")  # Separador visual

            # Salva o arquivo
            with open(target_file, "w", encoding="utf-8") as f:
                f.write("".join(markdown_content))

            logger.info(f"Sucesso! Salvo em: {target_file}")
            return str(target_file)

        except Exception as e:
            logger.error(f"Erro ao converter {input_file.name}: {e}")
            raise e
        finally:
            if "doc" in locals():
                doc.close()

    def batch_convert(self, input_folder: str):
        """Converte todos os PDFs de uma pasta."""
        p = Path(input_folder)
        pdfs = list(p.glob("*.pdf"))
        logger.info(f"Encontrados {len(pdfs)} PDFs para processar em {input_folder}.")

        for pdf in pdfs:
            self.convert(str(pdf))


# Teste rápido
if __name__ == "__main__":
    # Exemplo de uso
    transcriber = PDFTranscriber(output_dir="data/anexos")

    # Se houver algum PDF na raiz para testar:
    # transcriber.convert("exemplo_processo.pdf")

    print("Transcriber utilitário pronto. Importe a classe PDFTranscriber para usar.")
