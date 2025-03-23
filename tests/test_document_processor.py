import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.document_processor import DocumentProcessor
from src.exceptions import ProcessingError

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary test file with valid PDF content
        self.test_dir = Path(tempfile.mkdtemp())
        self.processed_dir = self.test_dir / "processed_documents"
        self.error_dir = self.test_dir / "errors"
        self.records_dir = self.test_dir / "records"
        
        # Create necessary directories
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.error_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test file
        self.test_file = self.test_dir / "test_document.pdf"
        c = canvas.Canvas(str(self.test_file))
        c.drawString(100, 750, "Test Invoice")
        c.drawString(100, 700, "Invoice #: 12345")
        c.save()
        
        # Initialize processor with config
        self.config = {
            "supported_extensions": [".pdf"],
            "processing_directory": str(self.processed_dir),
            "error_directory": str(self.error_dir),
            "processing_records_path": str(self.records_dir / "processing_records.json"),
            "max_file_size_mb": 10
        }
        self.processor = DocumentProcessor(self.config)

    def tearDown(self):
        # Clean up test directory
        shutil.rmtree(self.test_dir)

    @patch('src.document_processor.DocumentCategorizer')
    def test_process_document(self, mock_categorizer):
        # Create necessary directories
        today = datetime.now().strftime('%Y-%m-%d')
        target_dir = self.processed_dir / "invoice" / today
        target_dir.mkdir(parents=True, exist_ok=True)
        self.error_dir.mkdir(parents=True, exist_ok=True)

        # Mock categorizer response
        mock_response = {
            'categories': ['invoice'],
            'confidence': 0.9,
            'extracted_data': {
                'invoice_number': 'INV-2023-001'
            }
        }
        mock_categorizer.return_value.categorize.return_value = mock_response
        mock_categorizer.return_value.get_target_path.return_value = target_dir

        # Process test document
        result = self.processor.process_document(self.test_file)
        
        # Verify results
        self.assertIn('categories', result)
        self.assertEqual(result['categories'], ['invoice'])
        self.assertIn('final_path', result)
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
        # Create test files directory
        test_files_dir = self.test_dir / "input"
        test_files_dir.mkdir(parents=True, exist_ok=True)

        # Create necessary directories
        today = datetime.now().strftime('%Y-%m-%d')
        target_dir = self.processed_dir / "invoice" / today
        target_dir.mkdir(parents=True, exist_ok=True)
        self.error_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple test files with valid PDF content
        test_files = []
        for i in range(3):
            file_path = test_files_dir / f'test_document_{i}.pdf'
            with open(file_path, 'wb') as f:
                c = canvas.Canvas(f)
                c.drawString(100, 750, f"Test Document {i}")
                c.drawString(100, 700, f"Invoice #: {i}")
                c.save()
            test_files.append(file_path)

        # Mock categorizer response
        mock_response = {
            'categories': ['invoice'],
            'confidence': 0.9,
            'extracted_data': {
                'invoice_number': 'INV-2023-001'
            },
            'metadata': {}
        }
        mock_instance = mock_categorizer.return_value
        mock_instance.categorize.return_value = mock_response
        mock_instance.get_target_path.return_value = target_dir

        # Process batch
        results = self.processor.process_batch(test_files_dir)

        # Verify results
        self.assertEqual(len(results), 3)
        
        # Verify each result
        for result in results:
            self.assertIn('categories', result)
            self.assertEqual(result['categories'], ['invoice'])
            self.assertIn('final_path', result)
            self.assertTrue(Path(result['final_path']).exists())

    def test_error_handling(self):
        # Test error handling
        error_message = "Test error"
        self.processor._handle_processing_error(self.test_file, error_message)

        # Verify error log
        error_log = Path(self.config['error_directory']) / 'processing_errors.log'
        
        # Check if error log exists and contains the error message
        self.assertTrue(error_log.exists())
        with open(error_log, 'r') as f:
            log_content = f.read()
            self.assertIn(error_message, log_content)
            self.assertIn(str(self.test_file), log_content)

if __name__ == '__main__':
    unittest.main()



























