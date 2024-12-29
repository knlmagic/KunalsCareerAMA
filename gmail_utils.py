import os
import pickle
import logging
import json
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_client_secrets():
    """Get client secrets either from file or Streamlit secrets."""
    if 'GOOGLE_CLIENT_CONFIG' in st.secrets:
        logger.info("Using client secrets from Streamlit secrets")
        return json.loads(st.secrets['GOOGLE_CLIENT_CONFIG'])
    else:
        logger.info("Using client secrets from local file")
        secrets_file = 'client_secret_893578123856-brrk9u10t25u2dmd2j9jooqqmj47e941.apps.googleusercontent.com.json'
        if not os.path.exists(secrets_file):
            raise Exception("Client secrets file not found and GOOGLE_CLIENT_CONFIG not in Streamlit secrets")
        with open(secrets_file) as f:
            return json.load(f)

def get_gmail_service():
    """Get Gmail API service instance."""
    creds = None
    
    try:
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            logger.info("Found existing token.pickle file")
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                logger.info("Loaded credentials from token.pickle")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Starting new OAuth2 flow")
                client_secrets = get_client_secrets()
                flow = InstalledAppFlow.from_client_secrets_dict(
                    client_secrets,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("OAuth2 flow completed successfully")
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                logger.info("Saved new credentials to token.pickle")

        service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully built Gmail service")
        return service
    except Exception as e:
        logger.error(f"Error in get_gmail_service: {str(e)}")
        raise

def send_email(service, to_email, subject, body):
    """Send an email using the Gmail API."""
    try:
        logger.info(f"Attempting to send email to {to_email}")
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        
        # Create the raw email message
        raw = base64.urlsafe_b64encode(message.as_bytes())
        raw = raw.decode()
        
        # Send the email
        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        
        logger.info("Email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False 