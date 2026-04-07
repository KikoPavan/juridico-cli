import os
import sys

# Adiciona o diretório atual ao path para resolver os pacotes internos corretamente
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.data_processing.cli import app

if __name__ == "__main__":
    # Launch thin wrapper para a CLI Canônica Typer do domínio
    app()
