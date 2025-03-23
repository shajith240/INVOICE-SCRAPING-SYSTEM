import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.email_fetcher import EmailFetcher

class TestEmailFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = EmailFetcher()
        self.test_output_dir = Path('tests/test_data/attachments')
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    @patch('imaplib.IMAP4_SSL')
    def test_connection(self, mock_imap):
        # Setup mock
        mock_imap.return_value = MagicMock()
        
        # Test successful connection
        self.assertTrue(self.fetcher.connect())
        mock_imap.return_value.login.assert_called_once()

        # Test failed connection
        mock_imap.return_value.login.side_effect = Exception("Login failed")
        self.assertFalse(self.fetcher.connect())

    @patch('imaplib.IMAP4_SSL')
    def test_fetch_attachments(self, mock_imap):
        # Setup mock
        mock_imap.return_value = MagicMock()
        mock_imap.return_value.search.return_value = (None, [b'1 2 3'])
        
        # Mock email fetch response
        mock_email_data = self._create_mock_email_data()
        mock_imap.return_value.fetch.return_value = (None, [mock_email_data])

        # Test attachment fetching
        results = self.fetcher.fetch_attachments(str(self.test_output_dir), days=1)
        
        self.assertIsInstance(results, list)
        mock_imap.return_value.select.assert_called_once()
        mock_imap.return_value.search.assert_called_once()

    def _create_mock_email_data(self):
        # Create a mock email with attachment for testing
        with open('tests/test_data/mock_email.txt', 'w') as f:
            f.write('''
From: sender@example.com
Subject: Test Invoice
Date: Thu, 1 Jan 2023 00:00:00 +0000
Content-Type: multipart/mixed; boundary="boundary"

--boundary
Content-Type: text/plain

Test email body
--boundary
Content-Type: application/pdf
Content-Disposition: attachment; filename="test.pdf"

Mock PDF content
--boundary--
            ''')
        
        with open('tests/test_data/mock_email.txt', 'rb') as f:
            return (b'1', f.read())

    def tearDown(self):
        # Clean up test files
        if self.test_output_dir.exists():
            for file in self.test_output_dir.glob('*'):
                file.unlink()
            self.test_output_dir.rmdir()

if __name__ == '__main__':
    unittest.main()