import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from src.categorizer import DocumentCategorizer
from src.exceptions import CategoryError

class TestDocumentCategorizer(unittest.TestCase):
    def setUp(self):
        self.categorizer = DocumentCategorizer()
        # Create a temporary test file with valid PDF content
        self.test_file = Path(tempfile.mktemp(suffix='.pdf'))
        
        # Create a simple PDF with some content
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(self.test_file))
        c.drawString(100, 750, "Test Invoice")
        c.drawString(100, 700, "Invoice #: 12345")
        c.save()

    def tearDown(self):
        # Clean up test file
        if self.test_file.exists():
            self.test_file.unlink()

    @patch('src.categorizer.DocumentClassifier')
    @patch('src.categorizer.MetadataExtractor')
    @patch('src.categorizer.TextExtractor')
    def test_successful_categorization(self, mock_text, mock_metadata, mock_classifier):
        # Configure mocks
        mock_text_instance = mock_text.return_value
        mock_text_instance.extract.return_value = "Test content"
        
        mock_metadata_instance = mock_metadata.return_value
        mock_metadata_instance.extract.return_value = {"date": "2024-03-20"}
        
        mock_classifier_instance = mock_classifier.return_value
        mock_classifier_instance.classify.return_value = {
            "category": "invoice",
            "confidence": 0.95
        }

        # Test categorization
        result = self.categorizer.categorize(self.test_file)

        # Verify results
        self.assertIn('categories', result)
        self.assertEqual(result['categories'], ['invoice'])
        self.assertIn('confidence', result)
        self.assertGreater(result['confidence'], 0.9)
        self.assertIn('metadata', result)
        self.assertIn('extracted_data', result)

    def test_invalid_file(self):
        invalid_file = Path('nonexistent.pdf')
        with self.assertRaises(CategoryError):
            self.categorizer.categorize(invalid_file)

    @patch('src.categorizer.TextExtractor')
    def test_extraction_error_handling(self, mock_text):
        # Configure the mock to raise an exception
        mock_text_instance = mock_text.return_value
        mock_text_instance.extract.side_effect = Exception("Extraction failed")
        
        # Create categorizer with the mocked TextExtractor
        self.categorizer.text_extractor = mock_text_instance
        
        # Test that CategoryError is raised
        with self.assertRaises(CategoryError):
            self.categorizer.categorize(self.test_file)

if __name__ == '__main__':
    unittest.main()

