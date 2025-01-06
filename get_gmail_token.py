from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json
import os

# If modifying these scopes, delete any existing token
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_new_token():
    """Gets a new Gmail token through OAuth2 flow."""
    try:
        # Load client secrets from the downloaded JSON file
        # Make sure you've downloaded this from Google Cloud Console
        client_secrets_file = "client_secret_893578123856-brrk9u10t25u2dmd2j9jooqqmj47e941.apps.googleusercontent.com.json"
        
        # Create flow instance
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file,
            SCOPES
        )

        # Run the OAuth flow
        creds = flow.run_local_server(port=0)

        # Get token info as dictionary
        token_info = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }

        # Save token info to a file
        with open('new_gmail_token.json', 'w') as token_file:
            json.dump(token_info, token_file)

        print("\nNew token has been generated and saved to 'new_gmail_token.json'")
        print("\nToken information to add to Streamlit secrets:")
        print("-" * 50)
        print(f'GMAIL_TOKEN = \'{json.dumps(token_info)}\'')
        print("-" * 50)
        print("\nCopy the above line (including the GMAIL_TOKEN part) into your Streamlit secrets.")

    except Exception as e:
        print(f"Error getting new token: {e}")

if __name__ == "__main__":
    get_new_token() 