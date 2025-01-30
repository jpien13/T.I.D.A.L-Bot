import os
import imaplib
import email
import logging
from datetime import datetime
import pytz

import os
import imaplib
import email
import logging
from datetime import datetime
import pytz

# Configuration
IMAP_SERVER = 'imap.gmail.com'
EMAIL_FOLDER = 'INBOX'

# Get credentials from environment variables
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    logging.error("Email credentials not found in environment variables!")
    raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment variables")

# Setup basic logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def connect_to_email_server():
    """Establishes connection to the IMAP server and logs in."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        logging.info(f"Connecting to {IMAP_SERVER}...")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        logging.info("Successfully logged in")
        mail.select(EMAIL_FOLDER)
        return mail
    except Exception as e:
        logging.error(f"Failed to connect to the email server: {e}")
        raise

def search_for_unread_emails(mail, sender_email):
    """Searches for unread emails from a specific sender, received on the current date."""
    try:
        # Get the local timezone
        local_tz = pytz.timezone('America/New_York')  # Assuming you're in EST/EDT
        
        # Get today's date in your local timezone
        local_today = datetime.now(local_tz)
        search_date = local_today.strftime('%d-%b-%Y')
        
        # Add UNSEEN flag to search criteria
        search_criteria = f'(FROM "{sender_email}" SINCE "{search_date}" UNSEEN)'
        
        logging.info(f"Local timezone: {local_tz}")
        logging.info(f"Local time: {local_today}")
        logging.info(f"Searching for emails from {sender_email} on {search_date}")
        logging.info(f"Using search criteria: {search_criteria}")
        
        status, email_ids = mail.search(None, search_criteria)
        
        if status != 'OK':
            logging.error(f"Search failed with status: {status}")
            return []
            
        email_ids = email_ids[0].split()
        logging.info(f"Found {len(email_ids)} matching emails from today")
        return email_ids
        
    except Exception as e:
        logging.error(f"Error searching for emails: {e}")
        raise

def fetch_email_body(mail, email_id):
    """Fetches the body content of a single email and returns it as a string."""
    try:
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            logging.error(f"Failed to fetch email with ID {email_id}")
            return None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                if msg.is_multipart():
                    # Extract plain text part from multipart email
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            return part.get_payload(decode=True).decode()
                else:
                    # If the email is not multipart, return the body directly
                    return msg.get_payload(decode=True).decode()
        return None
    except Exception as e:
        logging.error(f"Error fetching email body: {e}")
        raise