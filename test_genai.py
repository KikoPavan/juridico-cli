import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERRO: GOOGLE_API_KEY não encontrada no .env")
    exit(1)

try:
    print("1. Inicializando cliente com google-genai...")
    client = genai.Client(api_key=api_key)

    print("2. Testando conexão simples...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Diga 'Olá, Jurídico CLI' se você estiver funcionando.",
    )
    print(f"SUCESSO: {response.text}")

except Exception as e:
    print(f"FALHA: {e}")
    print("Verifique se sua API Key tem acesso ao modelo 'gemini-2.0-flash-exp'.")
