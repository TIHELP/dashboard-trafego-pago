"""Gera o refresh_token do Google Ads API (rodar UMA VEZ, manualmente).

Pré-requisitos:
  - client_id e client_secret já criados no Google Cloud Console
    (APIs e Serviços > Credenciais > OAuth Client ID > tipo "App para computador")
  - Defina GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET como variáveis de ambiente antes de rodar
    (nunca cole esses valores direto no código — o GitHub bloqueia o push se detectar segredos)

Uso (PowerShell):
    pip install google-auth-oauthlib
    $env:GOOGLE_CLIENT_ID="SEU_CLIENT_ID.apps.googleusercontent.com"
    $env:GOOGLE_CLIENT_SECRET="SEU_CLIENT_SECRET"
    python gerar_refresh_token_google.py

O script abre o navegador, você faz login com a conta Google que tem acesso
à conta MCC do Google Ads, autoriza, e o refresh_token aparece no terminal.
Copie esse valor para o campo "Refresh Token" no painel de admin (não precisa editar código).
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Defina as variáveis de ambiente GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET antes de rodar.")
        print('Ex: $env:GOOGLE_CLIENT_ID="..." ; $env:GOOGLE_CLIENT_SECRET="..."')
        return

    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    # abre o navegador local, você loga com a conta Google que administra a MCC
    credentials = flow.run_local_server(port=0)

    print("\n--- Copie o valor abaixo para o campo 'Refresh Token' no painel de admin ---\n")
    print(credentials.refresh_token)
    print("\n-------------------------------------------------------------------------------\n")


if __name__ == "__main__":
    main()
