import unittest
from unittest.mock import patch, MagicMock
from src.email_fetcher import EmailFetcher

class TestEmailFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = EmailFetcher(
            host='imap.example.com',
            username='test@example.com',
            password='password123'
        )

    @patch('imaplib.IMAP4_SSL')
    def test_connection(self, mock_imap):
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        
        self.fetcher.connect()
        
        mock_imap.assert_called_once_with('imap.example.com')
        mock_connection.login.assert_called_once_with('test@example.com', 'password123')

    @patch('imaplib.IMAP4_SSL')
    def test_fetch_attachments(self, mock_imap):
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        mock_connection.search.return_value = ('OK', [b'1 2 3'])
        
        attachments = self.fetcher.fetch_attachments()
        
        self.assertIsInstance(attachments, list)
        mock_connection.select.assert_called_once_with('INBOX')

if __name__ == '__main__':
    unittest.main()
