import os
from pathlib import Pathfrom typing import List, Dict, Optional
import pytesseractfrom pdf2image import convert_from_path
import pdfplumberfrom dotenv import load_dotenv
class PDFProcessor:
    def __init__(self):        load_dotenv()
        self.tesseract_path = os.getenv('TESSERACT_PATH')        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
    def extract_text_from_pdf(self, pdf_path: str) -> str:        """Extract text from PDF using pdfplumber for searchable PDFs
        and OCR for scanned documents."""        try:
            # First try with pdfplumber for searchable PDFs            with pdfplumber.open(pdf_path) as pdf:
                text = ''                for page in pdf.pages:
                    text += page.extract_text() or ''                
                # If no text was extracted, document might be scanned                if not text.strip():
                    return self._process_scanned_pdf(pdf_path)                return text
        except Exception as e:            print(f"Error processing PDF {pdf_path}: {str(e)}")
            return ""
    def _process_scanned_pdf(self, pdf_path: str) -> str:        """Process scanned PDF using OCR."""
        try:            # Convert PDF to images
            images = convert_from_path(pdf_path)            text = ''
                        # Process each page with OCR
            for image in images:                text += pytesseract.image_to_string(image) + '\n'
                        return text
        except Exception as e:            print(f"Error processing scanned PDF {pdf_path}: {str(e)}")
            return ""
    def extract_invoice_data(self, pdf_path: str) -> Dict:        """Extract relevant invoice information from the PDF."""
        text = self.extract_text_from_pdf(pdf_path)        # TODO: Implement invoice data extraction logic
        # This would include finding invoice number, date, amount, etc.        return {
            'text': text,            'invoice_number': None,
            'date': None,            'amount': None,
            'vendor': None        }
    def process_batch(self, input_dir: str) -> List[Dict]:
        """Process all PDFs in the input directory."""        results = []
        input_path = Path(input_dir)        
        for pdf_file in input_path.glob('*.pdf'):            try:
                result = self.extract_invoice_data(str(pdf_file))                result['filename'] = pdf_file.name
                results.append(result)            except Exception as e:
                print(f"Error processing {pdf_file}: {str(e)}")
        
        return results






































