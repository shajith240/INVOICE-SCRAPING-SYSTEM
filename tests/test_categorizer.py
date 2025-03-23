import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
from src.categorizer import DocumentCategorizer
from src.exceptions import CategoryError

class TestDocumentCategorizer(unittest.TestCase):
    def setUp(self):
        self.categorizer = DocumentCategorizer()
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create a sample invoice PDF
        self.test_file = self.test_dir / "test_invoice.pdf"
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(self.test_file))
        c.drawString(100, 750, "INVOICE")
        c.drawString(100, 700, "Invoice #: 12345")
        c.drawString(100, 650, "Amount: $1,000.00")
        c.save()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_successful_categorization(self):
        """Test successful document categorization"""
        result = self.categorizer.categorize(self.test_file)
        self.assertEqual(result['categories'], ['invoice'])
        self.assertGreater(result['confidence'], 0.8)

    def test_invalid_file(self):
        """Test handling of invalid file"""
        invalid_file = self.test_dir / "nonexistent.pdf"
        with self.assertRaises(CategoryError):
            self.categorizer.categorize(invalid_file)

    def test_extraction_error_handling(self):
        """Test handling of extraction errors"""
        # Create an invalid PDF file
        invalid_pdf = self.test_dir / "invalid.pdf"
        invalid_pdf.write_text("This is not a PDF file")
        
        with self.assertRaises(CategoryError):
            self.categorizer.categorize(invalid_pdf)

    def test_categorize_with_metadata(self):
        """Test categorization using provided metadata"""
        metadata = {
            'text': 'This is an invoice for $100',
            'date': '2024-03-15'
        }
        
        # Create a dummy file
        test_file = self.test_dir / "test_doc.pdf"
        test_file.touch()
        
        result = self.categorizer.categorize(test_file, metadata)
        
        self.assertEqual(result['categories'], ['invoice'])
        self.assertGreater(result['confidence'], 0.9)
        self.assertEqual(result['metadata'], metadata)
        self.assertEqual(result['status'], 'processed')

    def test_categorize_other_document(self):
        """Test categorization of non-invoice document"""
        metadata = {
            'text': 'This is a regular document with no invoice-related content',
            'date': '2024-03-15'
        }
        
        test_file = self.test_dir / "test_doc.pdf"
        test_file.touch()
        
        result = self.categorizer.categorize(test_file, metadata)
        
        self.assertEqual(result['categories'], ['other'])
        self.assertLess(result['confidence'], 0.9)
        self.assertEqual(result['metadata'], metadata)
        self.assertEqual(result['status'], 'processed')

    def test_categorize_empty_text(self):
        """Test handling of empty text content"""
        test_file = self.test_dir / "empty.pdf"
        test_file.touch()
        
        with self.assertRaises(CategoryError):
            self.categorizer.categorize(test_file, {'text': ''})

if __name__ == '__main__':
    unittest.main()



