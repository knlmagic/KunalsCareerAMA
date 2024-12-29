import os
import logging
import json
import streamlit as st
from google.oauth2.credentials import Credentials
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
        # Try to load credentials from Streamlit secrets
        if "GMAIL_TOKEN" in st.secrets:
            try:
                logger.info("Found token in Streamlit secrets")
                token_info = json.loads(st.secrets["GMAIL_TOKEN"])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                
                # Build and return the Gmail service
                service = build('gmail', 'v1', credentials=creds)
                logger.info("Successfully built Gmail service")
                return service
                
            except Exception as e:
                logger.error(f"Error loading token from secrets: {e}")
                raise Exception(f"Error initializing Gmail service: {e}")
        else:
            logger.error("No Gmail token found in secrets")
            raise Exception("Gmail token not configured. Please contact the administrator.")

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