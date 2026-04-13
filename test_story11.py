import os
import sys
import traceback

from data_processing.extractor import DataExtractorApp

try:
    app = DataExtractorApp()
    print("Iniciando extracao de teste...")
    result_path = app.run_extraction("extr-peticao-processo", "test_input.md")
    print(f"SUCESSO. Arquivo salvo em: {result_path}")
    
    with open(result_path, "r", encoding="utf-8") as f:
        print("RESULTADO:", f.read())
except Exception as e:
    traceback.print_exc()
    print(f"FALHA: {e}")
