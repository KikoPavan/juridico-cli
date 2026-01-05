import os

from dotenv import load_dotenv

# 1. Tenta carregar
print(f"Diretório atual de execução: {os.getcwd()}")
print(f"Existe .env aqui? {os.path.exists('.env')}")

# Força o carregamento e mostra o resultado (True/False)
sucesso = load_dotenv(override=True)
print(f"load_dotenv retornou: {sucesso}")

# 2. Tenta ler a chave
chave = os.getenv("GOOGLE_API_KEY")

if chave:
    print(f"✅ SUCESSO! Chave lida: {chave[:5]}... (ocultado)")
    print(f"Tamanho da chave: {len(chave)} caracteres")
else:
    print("❌ FALHA: A variável GOOGLE_API_KEY é None.")

    # Debug profundo: O que foi carregado?
    # (Isso ajuda a ver se tem espaços no nome, ex: 'GOOGLE_API_KEY ')
    print("\n--- Variáveis carregadas no ambiente que contêm 'GOOGLE' ---")
    for k, v in os.environ.items():
        if "GOOGLE" in k:
            print(f"'{k}': '{v[:5]}...'")
