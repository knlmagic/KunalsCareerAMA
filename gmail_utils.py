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
from urllib.parse import urlparse, parse_qs

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow OAuth over HTTP for localhost
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def initialize_session_state():
    """Initialize session state variables."""
    if 'oauth_flow_started' not in st.session_state:
        st.session_state.oauth_flow_started = False
    if 'auth_url' not in st.session_state:
        st.session_state.auth_url = None
    if 'oauth_state' not in st.session_state:
        st.session_state.oauth_state = None

def extract_auth_code_from_url(redirect_url):
    """Extract authorization code and state from redirect URL."""
    try:
        # Parse the URL
        parsed = urlparse(redirect_url)
        # Get the query parameters
        params = parse_qs(parsed.query)
        
        # Extract code and state
        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        
        return code, state
    except Exception as e:
        logger.error(f"Error parsing redirect URL: {e}")
        return None, None

def get_gmail_service():
    """Get Gmail API service instance."""
    try:
        initialize_session_state()
        creds = None
        
        # Try to load credentials from Streamlit secrets first
        if "GMAIL_TOKEN" in st.secrets:
            try:
                logger.info("Found token in Streamlit secrets")
                token_info = json.loads(st.secrets["GMAIL_TOKEN"])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                if creds and creds.valid:
                    service = build('gmail', 'v1', credentials=creds)
                    logger.info("Successfully built Gmail service from secrets")
                    return service
            except Exception as e:
                logger.error(f"Error loading token from secrets: {e}")
        
        # If we reach here, we need to start the OAuth flow
        if not st.session_state.oauth_flow_started:
            logger.info("Starting new OAuth2 flow")
            st.session_state.oauth_flow_started = True
            
            # Parse the client config from secrets
            client_config = json.loads(st.secrets["GOOGLE_CLIENT_CONFIG"])
            
            # Create the flow using the client config
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri="http://localhost"
            )
            
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            st.session_state.auth_url = auth_url
            st.session_state.oauth_state = state
            st.session_state.flow = flow
        
        # Display OAuth instructions
        st.markdown("""
        ### Gmail Authorization Required
        1. Click the link below to authorize the application
        2. Select your Google account and grant permission
        3. You will be redirected to localhost (which may show an error - this is expected)
        4. Copy the entire URL from your browser's address bar after being redirected
        5. Paste the complete URL in the text box below
        """)
        
        st.markdown(f"[Click here to authorize the application]({st.session_state.auth_url})")
        
        redirect_response = st.text_input("Enter the complete redirect URL:")
        if redirect_response:
            try:
                # Extract code and state from redirect URL
                code, returned_state = extract_auth_code_from_url(redirect_response)
                
                # Verify state matches
                if returned_state != st.session_state.oauth_state:
                    st.error("State mismatch! Please try the authorization process again.")
                    # Reset the OAuth flow
                    st.session_state.oauth_flow_started = False
                    st.session_state.auth_url = None
                    st.session_state.oauth_state = None
                    if 'flow' in st.session_state:
                        del st.session_state.flow
                    return None
                
                flow = st.session_state.flow
                flow.fetch_token(authorization_response=redirect_response)
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
                
                # Clear the OAuth flow state
                st.session_state.oauth_flow_started = False
                st.session_state.auth_url = None
                st.session_state.oauth_state = None
                if 'flow' in st.session_state:
                    del st.session_state.flow
                    
                return None
                
            except Exception as e:
                st.error(f"Error during authorization: {e}")
                logger.error(f"Authorization error: {e}")
                return None
        return None

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