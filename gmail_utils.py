import os
import pickle
import logging
import json
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Get Gmail API service instance."""
    try:
        creds = None
        # Try to load credentials from Streamlit secrets first
        if "GMAIL_TOKEN" in st.secrets:
            try:
                logger.info("Found token in Streamlit secrets")
                token_info = json.loads(st.secrets["GMAIL_TOKEN"])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            except Exception as e:
                logger.error(f"Error loading token from secrets: {e}")
        
        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Starting new OAuth2 flow")
                # Parse the client config from secrets
                client_config = json.loads(st.secrets["GOOGLE_CLIENT_CONFIG"])
                
                # Create the flow using the client config
                flow = Flow.from_client_config(
                    client_config,
                    scopes=SCOPES,
                    redirect_uri=st.secrets.get("OAUTH_REDIRECT_URI", "https://kunalscareerama.streamlit.app/")
                )
                
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
                
                st.markdown("""
                ### Gmail Authorization Required
                1. Click the link below to authorize the application
                2. Select your Google account and grant permission
                3. Copy the authorization code from the redirect page
                4. Paste the code in the text box below
                """)
                
                st.markdown(f"[Click here to authorize the application]({auth_url})")
                
                code = st.text_input("Enter the authorization code:")
                if code:
                    try:
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                        
                        # Save credentials info for admin to update secrets
                        token_info = {
                            'token': creds.token,
                            'refresh_token': creds.refresh_token,
                            'token_uri': creds.token_uri,
                            'client_id': creds.client_id,
                            'client_secret': creds.client_secret,
                            'scopes': creds.scopes
                        }
                        
                        st.code(json.dumps(token_info, indent=2), language='json')
                        st.info("Copy this token information and add it to your Streamlit secrets as GMAIL_TOKEN")
                        st.success("Successfully generated Gmail token!")
                        return None
                        
                    except Exception as e:
                        st.error(f"Error during authorization: {e}")
                        logger.error(f"Authorization error: {e}")
                        return None
                return None

        # Build and return the Gmail service
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully built Gmail service")
        return service

    except Exception as e:
        logger.error(f"Error in get_gmail_service: {e}")
        raise Exception(f"Error initializing Gmail service: {e}")

def send_email(service, to, subject, body):
    """Send an email using the Gmail API."""
    try:
        logger.info(f"Attempting to send email to {to}")
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        message['from'] = "me"
        
        # Create the raw email message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the email
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        logger.info("Email sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise Exception(f"Failed to send email: {e}") 