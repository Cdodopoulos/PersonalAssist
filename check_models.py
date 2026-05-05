import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("AVISO: GEMINI_API_KEY não encontrada no .env")
    api_key = input("Por favor, cole sua GEMINI_API_KEY aqui: ").strip()

if not api_key:
    print("ERRO: Nenhuma chave fornecida.")
else:
    genai.configure(api_key=api_key)
    print(f"--- Modelos disponíveis para sua chave ---")
    try:
        models = genai.list_models()
        found = False
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found = True
        if not found:
            print("Nenhum modelo compatível encontrado.")
    except Exception as e:
        print(f"Erro ao conectar com a API: {e}")
