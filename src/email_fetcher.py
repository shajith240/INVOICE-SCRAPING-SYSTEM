import email
import imaplib
from typing import List, Dict
import os
from pathlib import Path

class EmailFetcher:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.mail = None

    def connect(self):
        """Establish connection to email server"""
        self.mail = imaplib.IMAP4_SSL(self.host)
        self.mail.login(self.username, self.password)

    def fetch_attachments(self, folder: str = "INBOX", save_dir: str = "attachments") -> List[Dict]:
        """Fetch email attachments and save them"""
        if not self.mail:
            self.connect()

        save_path = Path(save_dir)
        save_path.mkdir(exist_ok=True)
        
        results = []
        self.mail.select(folder)
        
        # Search for emails with attachments
        _, messages = self.mail.search(None, 'ALL')
        
        for msg_num in messages[0].split():
            try:
                _, msg_data = self.mail.fetch(msg_num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                if email_message.get_content_maintype() != 'multipart':
                    continue
                    
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                        
                    filename = part.get_filename()
                    if filename:
                        filepath = save_path / filename
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        results.append({
                            'filename': filename,
                            'path': str(filepath),
                            'subject': email_message['subject'],
                            'from': email_message['from']
                        })
                        
            except Exception as e:
                print(f"Error processing email {msg_num}: {str(e)}")
                
        return results

    def disconnect(self):
        """Close email connection"""
        if self.mail:
            self.mail.close()

