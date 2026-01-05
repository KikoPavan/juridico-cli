import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def teste_rapido():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERRO: Sem API Key no .env")
        return

    # 1. Ler o arquivo problemático
    arquivo_alvo = "data/cad-obr/escritura_matricula_7.546.md"
    if not os.path.exists(arquivo_alvo):
        print(f"❌ ERRO: Arquivo não encontrado: {arquivo_alvo}")
        return

    with open(arquivo_alvo, "r", encoding="utf-8") as f:
        conteudo = f.read()
        print(f"✅ Arquivo lido. Tamanho: {len(conteudo)} caracteres.")
        if len(conteudo) < 10:
            print("⚠️ AVISO: O arquivo parece estar vazio!")
            return

    print("\n--- Enviando para o Gemini (Teste de Segurança) ---")

    client = genai.Client(api_key=api_key)

    # Configuração permissiva máxima
    config = types.GenerateContentConfig(
        temperature=0.0,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ],
    )

    try:
        # Trocando para o modelo estável 1.5 para teste (o 2.5 pode ser instável)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Resuma este documento jurídico em uma frase: \n\n {conteudo}",
            config=config,
        )

        print(
            f"Status da Resposta: {response.candidates[0].finish_reason if response.candidates else 'SEM CANDIDATOS'}"
        )

        if response.text:
            print(f"✅ Sucesso! Resposta: {response.text[:100]}...")
        else:
            print("❌ Resposta vazia (Bloqueio confirmado).")
            # Tenta imprimir os ratings de segurança
            if response.candidates:
                print("Detalhes de segurança:", response.candidates[0].safety_ratings)

    except Exception as e:
        print(f"❌ Erro de API: {e}")


if __name__ == "__main__":
    teste_rapido()
