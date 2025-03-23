import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import tempfile
import json

from src.document_processor import DocumentProcessor
from src.exceptions import ProcessingError

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_path = self.test_dir / 'config.json'
        
        # Create test configuration
        self.test_config = {
            "supported_extensions": [".pdf"],
            "max_file_size_mb": 10,
            "processing_records_path": str(self.test_dir / "records"),
            "error_directory": str(self.test_dir / "errors"),
            "backup_directory": str(self.test_dir / "backups"),
            "processing_options": {
                "create_backup": True,
                "validate_content": True
            }
        }
        
        # Write test configuration
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
            
        # Create test files
        self.test_file = self.test_dir / 'test_document.pdf'
        self.test_file.touch()
        
        # Initialize processor
        self.processor = DocumentProcessor(self.config_path)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    @patch('src.document_processor.DocumentCategorizer')
    def test_process_document(self, mock_categorizer):
        # Mock categorizer response
        mock_categorizer.return_value.categorize.return_value = {
            'categories': ['invoice'],
            'confidence': 0.9,
            'extracted_data': {
                'invoice_number': 'INV-2023-001'
            }
        }
        
        # Process test document
        result = self.processor.process_document(self.test_file)
        
        # Verify results
        self.assertIn('categories', result)
        self.assertEqual(result['categories'], ['invoice'])
        self.assertIn('final_path', result)
        
        # Verify file was moved
        self.assertFalse(self.test_file.exists())
        self.assertTrue(Path(result['final_path']).exists())

    def test_invalid_file(self):
        # Test with non-existent file
        invalid_file = self.test_dir / 'nonexistent.pdf'
        with self.assertRaises(ProcessingError):
            self.processor.process_document(invalid_file)

    def test_unsupported_extension(self):
        # Test with unsupported file type
        unsupported_file = self.test_dir / 'test.txt'
        unsupported_file.touch()
        self.assertFalse(self.processor._validate_file(unsupported_file))

    @patch('src.document_processor.DocumentCategorizer')
    def test_process_batch(self, mock_categorizer):
        # Create multiple test files
        test_files = []
        for i in range(3):
            file_path = self.test_dir / f'test_document_{i}.pdf'
            file_path.touch()
            test_files.append(file_path)
        
        # Mock categorizer response
        mock_categorizer.return_value.categorize.return_value = {
            'categories': ['invoice'],
            'confidence': 0.9,
            'extracted_data': {}
        }
        
        # Process batch
        results = self.processor.process_batch(self.test_dir)
        
        # Verify results
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('categories', result)
            self.assertIn('final_path', result)

    def test_error_handling(self):
        # Test error handling
        error_message = "Test error"
        self.processor._handle_processing_error(self.test_file, error_message)
        
        # Verify error log
        error_log = Path(self.test_config['error_directory']) / 'processing_errors.log'
        self.assertTrue(error_log.exists())
        
        # Verify file moved to error directory
        error_file = Path(self.test_config['error_directory']) / self.test_file.name
        self.assertTrue(error_file.exists())

if __name__ == '__main__':
    unittest.main()