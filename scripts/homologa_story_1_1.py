import os
import sys
from pathlib import Path

# Adiciona ao PYTHONPATH automaticamente garantindo a injeção do baseline novo
project_root = Path(__file__).resolve().parent.parent
apps_path = project_root / "apps" / "data-processing" / "src"
sys.path.insert(0, str(apps_path))

from data_processing.extractor import DataExtractorApp

def executar_homologacao():
    print("=====================================================")
    print("  HOMOLOGAÇÃO OFICIAL STORY 1.1 - Gemini Baseline")
    print("=====================================================")
    
    # 1. Verifica pré-requisitos essenciais
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERRO FATAL] GEMINI_API_KEY não foi encontrada no ambiente.")
        print("Adicione no seu arquivo .env ou exporte no terminal para prosseguir.")
        sys.exit(1)
        
    print("[MOCK] Criando input massivo de testes em var/input/md/test_input.md")
    input_dir = project_root / "var" / "input" / "md"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_file = input_dir / "test_input.md"
    
    input_file.write_text(
        "PROCESSO Nº 1000234-56.2023.8.26.0100\n"
        "REQUERENTE: João da Silva ME.\n"
        "O exequente postula a citação da empresa devedora para pagamento do valor de R$ 56.000,00.",
        encoding="utf-8"
    )

    try:
        # Configurando o orquestrador para consumir o baseline da CLI
        app = DataExtractorApp()
        
        # Validando Skill real
        skill_id = "extr-peticao-processo" 
        
        print(f"\n[EXECUÇÃO] Disparando LLM (Gemini) sobre a skill: {skill_id}...")
        
        result_path = app.run_extraction(bundle_id=skill_id, input_filename=input_file.name)
        
        print(f"\n[SUCESSO] Processamento Real concluído!")
        print(f"[EVIDÊNCIA] Contrato salvo fisicamente em: {result_path}")
        
        with open(result_path, "r", encoding="utf-8") as f:
            print("\n>> OUTPUT FORMAL GERADO <<")
            print(f.read()[:500] + "\n...[truncado]")
            
    except Exception as e:
        import traceback
        print("\n[FALHA NA HOMOLOGAÇÃO] Ocorreu um erro estrutural:")
        traceback.print_exc()
        print("\nRevise a chave, o rate limit, ou logs detalhados do baseline.")
        sys.exit(1)

if __name__ == "__main__":
    executar_homologacao()
