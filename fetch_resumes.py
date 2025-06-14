import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

#Gmail Mail IMAP settings
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993

def connect_to_gmail():
    """Connect to GMAIL Mail using IMAP"""
    
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    # print(EMAIL, PASSWORD)
    
    if not EMAIL or not PASSWORD:
        print("Please set EMAIL and EMAIL_PASSWORD in your .env file")
        print("Example .env file:")
        print("EMAIL=your-email@gmail.com")
        print("EMAIL_PASSWORD=your-password")
        return None
    
    try:
        print("Connecting to Gmail Mail...")
        imap = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER, GMAIL_IMAP_PORT)
        imap.login(EMAIL, PASSWORD)
        print("Successfully connected to Gmail Mail!")
        return imap
        
    except imaplib.IMAP4.error as e:
        print(f"Authentication failed: {e}")
        print("Please check your email and password in the .env file")
        print("Make sure IMAP is enabled in your Gmail Mail settings")
        return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def decode_mime_words(s):
    """Decode MIME encoded words in headers"""
    if not s:
        return "No Subject"
    
    decoded_parts = decode_header(s)
    decoded_string = ""
    
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            decoded_string += str(part)
    
    return decoded_string

def is_resume_file(filename):
    """Check if file is likely a resume based on extension"""
    if not filename:
        return False
    
    resume_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    file_ext = os.path.splitext(filename.lower())[1]
    return file_ext in resume_extensions

def save_attachment(part, filename, folder='resumes'):
    """Save email attachment to specified folder"""
    
    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")
    
    # Create unique filename to avoid conflicts
    base_name, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    
    while os.path.exists(os.path.join(folder, unique_filename)):
        unique_filename = f"{base_name}_{counter}{ext}"
        counter += 1
    
    filepath = os.path.join(folder, unique_filename)
    
    try:
        with open(filepath, 'wb') as f:
            f.write(part.get_payload(decode=True))
        
        print(f"✓ Saved: {filepath}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to save {filename}: {e}")
        return False

def fetch_resumes_from_gmail():
    """Main function to fetch resumes from Gmail Mail"""
    
    imap = connect_to_gmail()
    if not imap:
        return
    
    try:
        # Select inbox
        print("\nSelecting INBOX...")
        imap.select("INBOX")
        
        # Search for unread emails
        print("Searching for unread emails...")
        status, messages = imap.search(None, '(UNSEEN)')
        
        if status != 'OK':
            print("Failed to search emails")
            return
        
        mail_ids = messages[0].split() if messages[0] else []
        print(f"Found {len(mail_ids)} unread emails")
        
        if not mail_ids:
            print("No unread emails found")
            return
        
        resume_count = 0
        processed_emails = 0
        
        # Process each email
        for mail_id in mail_ids:
            try:
                # Fetch email
                status, msg_data = imap.fetch(mail_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                processed_emails += 1
                
                # Get email details
                subject = decode_mime_words(msg.get("Subject"))
                sender = decode_mime_words(msg.get("From"))
                
                print(f"\n--- Email {processed_emails}/{len(mail_ids)} ---")
                print(f"From: {sender}")
                print(f"Subject: {subject}")
                
                # Check for attachments
                has_attachments = False
                
                for part in msg.walk():
                    # Skip multipart containers
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    # Check if it's an attachment
                    content_disposition = part.get("Content-Disposition")
                    if content_disposition and 'attachment' in content_disposition:
                        has_attachments = True
                        
                        # Get filename
                        filename = part.get_filename()
                        if filename:
                            filename = decode_mime_words(filename)
                            
                            print(f"  Attachment found: {filename}")
                            
                            # Check if it's a resume file
                            if is_resume_file(filename):
                                print(f"  → Resume detected!")
                                
                                if save_attachment(part, filename):
                                    resume_count += 1
                            else:
                                print(f"  → Not a resume file (skipped)")
                        else:
                            print(f"  → Attachment without filename (skipped)")
                
                if not has_attachments:
                    print("  No attachments found")
            
            except Exception as e:
                print(f"Error processing email {mail_id}: {e}")
                continue
        
        print(f"\n=== Summary ===")
        print(f"Processed emails: {processed_emails}")
        print(f"Resumes downloaded: {resume_count}")
        
        if resume_count > 0:
            print(f"Resumes saved to: ./resumes/")
        
    except Exception as e:
        print(f"Error during email processing: {e}")
    
    finally:
        try:
            imap.close()
            imap.logout()
            print("\nDisconnected from Gmail Mail")
        except:
            pass

def enable_imap_instructions():
    """Print instructions for enabling IMAP in Gmail Mail"""
    print("\n" + "="*50)
    print("IMPORTANT: Enable IMAP in Gmail Mail")
    print("="*50)
    print("1. Login to your Gmail Mail account")
    print("2. Go to Settings → Mail Accounts")
    print("3. Click on your email account")
    print("4. Go to 'Access Details' tab")
    print("5. Enable 'IMAP Access'") 
    print("6. Note the IMAP settings:")
    print("   - Server: imap.gmail.com")
    print("   - Port: 993")
    print("   - Security: SSL")
    print("="*50)

def main():
    """Main function with setup instructions"""
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠ .env file not found!")
        print("\nCreate a .env file with:")
        print("EMAIL=your-email@gmail.com")
        print("EMAIL_PASSWORD=your-password")
        return
    
    # Check environment variables
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    if not EMAIL or not PASSWORD:
        print("⚠ Missing credentials in .env file!")
        print("\nMake sure your .env file contains:")
        print("EMAIL=your-email@gmail.com") 
        print("EMAIL_PASSWORD=your-password")
        return
    
    print("Gmail Mail Resume Fetcher")
    print(f"Email: {EMAIL}")
    
    # Show IMAP instructions
    enable_imap_instructions()
    
    input("\nPress Enter to continue after enabling IMAP...")
    
    # Fetch resumes
    fetch_resumes_from_gmail()

if __name__ == "__main__":
    main()