"""
Script para autenticação inicial do Google Calendar.
Execute este script LOCALMENTE para gerar o arquivo 'token.json'.
"""
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Se modificar estes escopos, delete o arquivo token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    creds = None
    # O arquivo token.json armazena os tokens de acesso e atualização do usuário.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Se não houver credenciais válidas, peça ao usuário para fazer login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("ERRO: Arquivo 'credentials.json' não encontrado!")
                print("Por favor, baixe o JSON do Google Cloud e renomeie para 'credentials.json'.")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Salva as credenciais para a próxima execução
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("\nSUCESSO! O arquivo 'token.json' foi gerado.")
        print("Agora você deve subir os arquivos 'credentials.json' e 'token.json' para o GitHub.")

if __name__ == '__main__':
    main()
