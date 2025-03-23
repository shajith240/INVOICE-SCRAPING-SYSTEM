import os
import emailimport imaplib
from pathlib import Pathfrom typing import List, Dict, Optional
from datetime import datetimeimport json
from dotenv import load_dotenv
class EmailFetcher:    def __init__(self):
        load_dotenv()        self._load_config()
        self.imap_server = None
    def _load_config(self):        """Load email configuration from config/email_config.json"""
        config_path = Path('config/email_config.json')        try:
            with open(config_path) as f:                config = json.load(f)
                self.email = config.get('email')                self.password = os.getenv('EMAIL_PASSWORD')
                self.imap_server = config.get('imap_server')                self.folder = config.get('folder', 'INBOX')
                self.attachment_types = config.get('attachment_types', ['.pdf'])        except Exception as e:
            raise Exception(f"Failed to load email configuration: {str(e)}")
    def connect(self) -> bool:        """Establish connection to the IMAP server"""
        try:            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email, self.password)            return True
        except Exception as e:            print(f"Failed to connect to email server: {str(e)}")
            return False
    def disconnect(self):        """Close the IMAP connection"""
        if hasattr(self, 'mail'):            try:
                self.mail.close()                self.mail.logout()
            except:                pass
    def fetch_attachments(self, 
                         output_dir: str,                          days: int = 7, 
                         mark_as_read: bool = True) -> List[Dict]:        """
        Fetch email attachments from the last n days        
        Args:            output_dir: Directory to save attachments
            days: Number of days to look back            mark_as_read: Whether to mark processed emails as read
                Returns:
            List of dictionaries containing attachment info        """
        if not self.connect():            return []
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)        
        results = []        try:
            # Select the email folder            self.mail.select(self.folder)
            # Search for emails from the last n days
            date = (datetime.now() - datetime.timedelta(days=days)).strftime("%d--%b--%Y")            _, messages = self.mail.search(None, f'(SINCE {date})')
            for msg_num in messages[0].split():
                try:                    _, msg_data = self.mail.fetch(msg_num, '(RFC822)')
                    email_body = msg_data[0][1]                    email_msg = email.message_from_bytes(email_body)
                    subject = email_msg["subject"]
                    from_addr = email_msg["from"]                    date = email_msg["date"]
                    # Process attachments
                    attachments = self._process_attachments(email_msg, output_path)                    
                    if attachments:                        results.extend([{
                            'filename': att['filename'],                            'path': att['path'],
                            'subject': subject,                            'from': from_addr,
                            'date': date                        } for att in attachments])
                        # Mark email as read if requested
                        if mark_as_read:                            self.mail.store(msg_num, '+FLAGS', '\\Seen')
                except Exception as e:
                    print(f"Error processing email {msg_num}: {str(e)}")                    continue
        finally:
            self.disconnect()
        return results
    def _process_attachments(self,                            msg: email.message.Message, 
                           output_dir: Path) -> List[Dict]:        """Process and save email attachments"""
        attachments = []        
        for part in msg.walk():            if part.get_content_maintype() == 'multipart':
                continue            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()            if not filename:
                continue
            # Check if attachment type is allowed            if not any(filename.lower().endswith(ext) for ext in self.attachment_types):
                continue
            # Generate unique filename if file exists            filepath = output_dir / filename
            counter = 1            while filepath.exists():
                name, ext = os.path.splitext(filename)                filepath = output_dir / f"{name}_{counter}{ext}"
                counter += 1
            # Save attachment            try:
                with open(filepath, 'wb') as f:                    f.write(part.get_payload(decode=True))
                attachments.append({                    'filename': filepath.name,
                    'path': str(filepath)                })
            except Exception as e:                print(f"Error saving attachment {filename}: {str(e)}")

        return attachments













































































