import unittest
from pathlib import Path
from src.pdf_processor import PDFProcessor

class TestPDFProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = PDFProcessor()
        self.test_data_dir = Path('tests/test_data')
        self.test_data_dir.mkdir(exist_ok=True)

    def test_extract_text_from_searchable_pdf(self):
        # TODO: Add a sample searchable PDF to test_data directory
        pdf_path = self.test_data_dir / 'sample_searchable.pdf'
        if pdf_path.exists():
            result = self.processor.extract_text_from_pdf(str(pdf_path))
            self.assertIsInstance(result, str)
            self.assertNotEqual(result.strip(), '')

    def test_extract_text_from_scanned_pdf(self):
        # TODO: Add a sample scanned PDF to test_data directory
        pdf_path = self.test_data_dir / 'sample_scanned.pdf'
        if pdf_path.exists():
            result = self.processor.extract_text_from_pdf(str(pdf_path))
            self.assertIsInstance(result, str)

    def test_extract_invoice_data(self):
        # TODO: Add a sample invoice PDF to test_data directory
        pdf_path = self.test_data_dir / 'sample_invoice.pdf'
        if pdf_path.exists():
            result = self.processor.extract_invoice_data(str(pdf_path))
            self.assertIsInstance(result, dict)
            self.assertIn('text', result)
            self.assertIn('invoice_number', result)
            self.assertIn('date', result)
            self.assertIn('amount', result)
            self.assertIn('vendor', result)

    def test_process_batch(self):
        # Create test PDFs in the test_data directory
        if self.test_data_dir.exists():
            results = self.processor.process_batch(str(self.test_data_dir))
            self.assertIsInstance(results, list)
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertIn('filename', result)

if __name__ == '__main__':
    unittest.main()

