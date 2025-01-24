# email_reader.py
from bs4 import BeautifulSoup
import imaplib
import email
import logging
import datetime
import os

# Setup basic logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

# Configuration
IMAP_SERVER = 'imap.gmail.com'
EMAIL_FOLDER = 'INBOX'

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
        today_date = datetime.datetime.today().strftime('%d-%b-%Y')
        # Combine FROM, SINCE, and ON criteria to get today's emails from the sender
        search_criteria = f'(FROM "{sender_email}" SINCE "{today_date}")'
        
        logging.info(f"Searching for emails from {sender_email} on {today_date}")
        logging.info(f"Using search criteria: {search_criteria}")
        
        status, email_ids = mail.search(None, search_criteria)
        
        if status != 'OK':
            logging.error("No emails found.")
            return []
            
        email_ids = email_ids[0].split()
        logging.info(f"Found {len(email_ids)} matching emails from today")
        return email_ids
    except Exception as e:
        logging.error(f"Error searching for emails: {e}")
        raise

def fetch_and_process_emails(mail, email_ids):
    """Fetches emails by ID and extracts all URLs from them."""
    links = []
    processed_count = 0
    
    for e_id in email_ids:
        try:
            logging.info(f"Processing email ID: {e_id}")
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            
            # Process the email content
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg.get('subject', 'No Subject')
                    sender = msg.get('from', 'No Sender')
                    logging.info(f"Processing email - Subject: {subject}, From: {sender}")
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/html":
                                body = part.get_payload(decode=True).decode()
                                new_links = extract_links(body)
                                links.extend(new_links)
                    else:
                        body = msg.get_payload(decode=True).decode()
                        new_links = extract_links(body)
                        links.extend(new_links)
            
            # After successfully processing the email, mark it as read
            try:
                mail.store(e_id, '+FLAGS', '\\Seen')
                # Verify the email was marked as read
                _, flag_data = mail.fetch(e_id, '(FLAGS)')
                if '\\Seen' in str(flag_data[0]):
                    logging.info(f"Successfully marked email {e_id} as read")
                else:
                    logging.warning(f"Failed to verify email {e_id} was marked as read")
            except Exception as mark_error:
                logging.error(f"Error marking email {e_id} as read: {mark_error}")
                # Continue processing other emails even if marking as read fails
            
            processed_count += 1
            logging.info(f"Successfully processed email {processed_count}/{len(email_ids)}")
            
        except Exception as e:
            logging.error(f"Error processing email {e_id}: {e}")
            # Try to mark as read even if processing failed
            try:
                mail.store(e_id, '+FLAGS', '\\Seen')
                logging.info(f"Marked failed email {e_id} as read")
            except Exception as mark_error:
                logging.error(f"Error marking failed email {e_id} as read: {mark_error}")
            continue
    
    return links

def extract_links(html_content):
    """Extracts URLs from the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    link_count = 0
    
    for a_tag in soup.find_all('a'):
        link = a_tag.get('href')
        text = a_tag.text.strip()
        if 'minute read)' in text and link:
            links.append(link)
            link_count += 1
            logging.info(f"Found link {link_count}: {link}")
    
    return links

def get_article_links(sender_email):
    """Orchestrates the process to connect, search, fetch, and process emails"""
    try:
        mail = connect_to_email_server()
        email_ids = search_for_unread_emails(mail, sender_email)
        
        if email_ids:
            links = fetch_and_process_emails(mail, email_ids)
            logging.info(f"Total links found: {len(links)}")
            return links
        else:
            logging.info("No unread emails from the specified sender.")
            return []
            
    except Exception as e:
        logging.error(f"Error in get_article_links: {e}")
        return []
    finally:
        try:
            mail.logout()
            logging.info("Successfully logged out from email server")
        except:
            pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test email processing functionality')
    parser.add_argument('--sender', default='dan@tldrnewsletter.com',
                      help='Email address to search for (default: dan@tldrnewsletter.com)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\nEmail Processor Test Script")
    print("="*50)
    print(f"Testing with sender: {args.sender}")
    print("="*50)
    
    # Test connection
    try:
        mail = connect_to_email_server()
        print("\n✓ Successfully connected to email server")
    except Exception as e:
        print(f"\n✗ Failed to connect to email server: {e}")
        exit(1)
    
    # Test search
    try:
        email_ids = search_for_unread_emails(mail, args.sender)
        print(f"\n✓ Found {len(email_ids)} emails from {args.sender}")
    except Exception as e:
        print(f"\n✗ Failed to search emails: {e}")
        exit(1)
    
    # Test processing
    if email_ids:
        try:
            links = fetch_and_process_emails(mail, email_ids)
            print("\nFound Links:")
            print("-"*50)
            for i, link in enumerate(links, 1):
                print(f"{i}. {link}")
        except Exception as e:
            print(f"\n✗ Failed to process emails: {e}")
    
    # Test complete flow
    print("\nTesting complete flow with get_article_links():")
    print("-"*50)
    links = get_article_links(args.sender)
    print(f"\nTotal links found: {len(links)}")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link}")

    print("\nTest complete!")