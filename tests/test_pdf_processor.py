import unittest
from pathlib import Path
import tempfile
import os
from src.pdf_processor import PDFProcessor

class TestPDFProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = PDFProcessor()
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test if PDFProcessor initializes correctly"""
        self.assertIsNotNone(self.processor)
        self.assertIsNotNone(self.processor.tesseract_path)

    def test_extract_invoice_data_with_invalid_path(self):
        """Test handling of invalid PDF path"""
        invalid_path = str(self.test_dir / "nonexistent.pdf")
        with self.assertRaises(Exception):
            self.processor.extract_invoice_data(invalid_path)

    def test_process_batch_with_empty_directory(self):
        """Test batch processing with empty directory"""
        results = self.processor.process_batch(str(self.test_dir))
        self.assertEqual(len(results), 0)

    # Add this test only if you have a sample PDF file
    def test_extract_invoice_data_with_sample(self):
        """Test extraction with a sample PDF"""
        # Create a sample directory in tests folder
        sample_dir = Path(__file__).parent / "samples"
        sample_dir.mkdir(exist_ok=True)
        
        # Skip if no sample file exists
        sample_path = sample_dir / "sample_invoice.pdf"
        if not sample_path.exists():
            self.skipTest("Sample invoice PDF not found")
            
        result = self.processor.extract_invoice_data(str(sample_path))
        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertIn('invoice_number', result)
        self.assertIn('date', result)
        self.assertIn('amount', result)
        self.assertIn('vendor', result)

if __name__ == '__main__':
    unittest.main()


