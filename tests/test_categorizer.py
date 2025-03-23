import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.categorizer import DocumentCategorizer
from src.exceptions import CategoryError

class TestDocumentCategorizer(unittest.TestCase):
    def setUp(self):
        self.categorizer = DocumentCategorizer()
        self.test_file = Path(tempfile.mktemp(suffix='.pdf'))
        self.test_file.touch()

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    @patch('src.categorizer.TextExtractor')
    @patch('src.categorizer.MetadataExtractor')
    @patch('src.categorizer.DocumentClassifier')
    def test_categorize_document(self, mock_classifier, mock_metadata, mock_text):
        # Setup mock responses
        mock_text.return_value.extract.return_value = "Test document content"
        mock_metadata.return_value.extract.return_value = {"created": "2023-01-01"}
        mock_classifier.return_value.classify.return_value = {
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
        mock_text.return_value.extract.side_effect = Exception("Extraction failed")
        
        with self.assertRaises(CategoryError):
            self.categorizer.categorize(self.test_file)

    def test_get_target_path(self):
        # Test with single category
        result = {
            'categories': ['invoice'],
            'confidence': 0.9,
            'metadata': {}
        }
        path = self.categorizer.get_target_path(result)
        self.assertIn('invoice', str(path))

        # Test with subcategory
        result['categories'] = ['invoice', 'utilities']
        path = self.categorizer.get_target_path(result)
        self.assertIn('utilities', str(path))

    @patch('src.categorizer.TextExtractor')
    @patch('src.categorizer.DocumentClassifier')
    def test_category_specific_extraction(self, mock_classifier, mock_text):
        mock_text.return_value.extract.return_value = "Invoice #12345"
        mock_classifier.return_value.classify.return_value = {
            "category": "invoice",
            "confidence": 0.95
        }

        result = self.categorizer.categorize(self.test_file)
        self.assertIn('extracted_data', result)

    def test_metadata_handling(self):
        # Test with additional metadata
        metadata = {
            'source': 'email',
            'sender': 'test@example.com'
        }
        
        with patch('src.categorizer.TextExtractor') as mock_text, \
             patch('src.categorizer.MetadataExtractor') as mock_metadata, \
             patch('src.categorizer.DocumentClassifier') as mock_classifier:
            
            mock_text.return_value.extract.return_value = "Test content"
            mock_metadata.return_value.extract.return_value = {"created": "2023-01-01"}
            mock_classifier.return_value.classify.return_value = {
                "category": "invoice",
                "confidence": 0.95
            }

            result = self.categorizer.categorize(self.test_file, metadata)
            
            self.assertIn('metadata', result)
            self.assertEqual(result['metadata']['source'], 'email')
            self.assertEqual(result['metadata']['sender'], 'test@example.com')

if __name__ == '__main__':
    unittest.main()
