import os
import pickle
import logging
import json
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def is_streamlit_cloud():
    """Check if we're running on Streamlit Cloud"""
    return st.runtime.exists() and not os.path.exists('.streamlit/secrets.toml')

def get_gmail_service():
    """Get Gmail API service instance."""
    try:
        creds = None
        # Load existing credentials from token.pickle if it exists
        if os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    logger.info("Found existing token.pickle file")
                    creds = pickle.load(token)
                    logger.info("Loaded credentials from token.pickle")
            except Exception as e:
                logger.info(f"Error loading token.pickle: {e}")
                if os.path.exists('token.pickle'):
                    os.remove('token.pickle')

        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Starting new OAuth2 flow")
                # Parse the client config from secrets
                client_config = json.loads(st.secrets["GOOGLE_CLIENT_CONFIG"])
                
                if is_streamlit_cloud():
                    # Use manual flow for Streamlit Cloud
                    flow = Flow.from_client_config(
                        client_config,
                        scopes=SCOPES,
                        redirect_uri=st.secrets.get("OAUTH_REDIRECT_URI", "https://kunalscareerama.streamlit.app/")
                    )
                    
                    auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
                    
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
                            st.success("Successfully authenticated with Gmail!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error during authorization: {e}")
                            logger.error(f"Authorization error: {e}")
                            return None
                else:
                    # Use local server flow for development
                    flow = InstalledAppFlow.from_client_config(
                        client_config,
                        SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("OAuth2 flow completed successfully")
                
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    logger.info("Saving new credentials to token.pickle")
                    pickle.dump(creds, token)

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