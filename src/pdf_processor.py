import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import re
from .validators.invoice_validator import InvoiceValidator
from .categorizer import DocumentCategorizer as Categorizer

class PDFProcessor:
    """Processes PDF invoices and extracts structured data"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.validator = InvoiceValidator()
        self.categorizer = Categorizer()
        
        # Configure tesseract path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path or r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def extract_invoice_data(self, file_path: str) -> Dict:
        """
        Extract and validate data from invoice PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary containing validated invoice data or validation results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
            
        try:
            # Extract text from PDF
            text = self._extract_text(file_path)
            
            # Debug: Print raw text
            print("\nRaw text from PDF:")
            print("-" * 40)
            print(text)
            print("-" * 40)
            
            # Categorize document to ensure it's an invoice
            categorization = self.categorizer.categorize(Path(file_path), {'text': text})
            if categorization['categories'][0] != 'invoice':
                self.logger.warning(f"Document appears to be {categorization['categories'][0]}, not an invoice")
                return {
                    'is_valid': False,
                    'errors': [f"Document type mismatch: expected invoice, got {categorization['categories'][0]}"],
                    'categorization': categorization
                }
            
            # Extract structured data
            extracted_data = self._extract_invoice_data(text)
            
            # Validate extracted data
            validation_results = self.validator.validate(extracted_data)
            
            if validation_results['is_valid']:
                self.logger.info(f"Successfully processed invoice: {file_path}")
                return validation_results['cleaned_data']
            else:
                self.logger.warning(
                    f"Validation errors in {file_path}: {validation_results['errors']}"
                )
                return validation_results
                
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            raise

    def _extract_invoice_data(self, text: str) -> Dict:
        """
        Extract structured data from invoice text
        
        Args:
            text: Extracted text content from PDF
        
        Returns:
            Dictionary containing extracted invoice fields
        """
        def clean_amount(amount_str: str) -> str:
            """Clean and standardize amount strings"""
            amount = amount_str.strip()
            for symbol in ['€', '$', '£', ' ']:
                amount = amount.replace(symbol, '')
            if ',' in amount:
                amount = amount.replace('.', '').replace(',', '.')
            return amount.strip()

        extracted_data = {
            'invoice_number': '',
            'date': '',
            'total_amount': '',
            'vendor': '',
            'description': ''
        }
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract vendor (first line)
        extracted_data['vendor'] = lines[0] if lines else ''
        
        # Extract invoice number and date
        for i, line in enumerate(lines):
            if 'Invoice No' in line and 'Invoice Period' in line:
                try:
                    data_line = lines[i + 1]
                    parts = data_line.split()
                    extracted_data['invoice_number'] = parts[0]
                    # Get the full date from the end
                    extracted_data['date'] = parts[-2] + ' ' + parts[-1]
                    break
                except (IndexError, ValueError):
                    continue
        
        # Extract total amount - specifically look for "Gross Amount incl. VAT"
        for i, line in enumerate(lines):
            if 'Gross Amount incl. VAT' in line:
                try:
                    amount = line.split('VAT')[-1].strip()
                    extracted_data['total_amount'] = clean_amount(amount)
                    break
                except (IndexError, ValueError):
                    continue
        
        # Build description
        description_parts = []
        
        # Add invoice type
        for line in lines:
            if 'Invoice WMACCESS' in line:
                description_parts.append(f"Type: {line.strip()}")
                break
        
        # Add customer info
        for i, line in enumerate(lines):
            if 'Musterkunde AG' in line:
                try:
                    customer_info = [
                        lines[i].strip(),      # Company name
                        lines[i + 1].strip(),  # Contact person
                        lines[i + 2].strip(),  # Street
                        lines[i + 3].strip()   # City
                    ]
                    description_parts.append("Customer: " + " | ".join(filter(None, customer_info)))
                    break
                except IndexError:
                    pass
        
        # Add invoice period
        for i, line in enumerate(lines):
            if 'Invoice Period' in line:
                try:
                    next_line = lines[i + 1]
                    period = next_line.split('Date')[0].strip()
                    description_parts.append(f"Period: {period}")
                    break
                except (IndexError, ValueError):
                    continue
        
        # Add financial summary
        net_amount = None
        vat_amount = None
        
        for line in lines:
            if 'Total' in line and 'VAT' not in line and '€' in line:
                net_amount = clean_amount(line.split()[-1])
            elif 'VAT 19 %' in line:
                vat_amount = clean_amount(line.split()[-1])
        
        if net_amount:
            description_parts.append(f"Net Amount: {net_amount}€")
        if vat_amount:
            description_parts.append(f"VAT Amount: {vat_amount}€")
        
        extracted_data['description'] = ' | '.join(filter(None, description_parts))
        
        return extracted_data

    def process_batch(self, directory: str) -> List[Dict]:
        """
        Process multiple PDFs in a directory
        
        Args:
            directory: Path to directory containing PDF files
            
        Returns:
            List of processing results for each PDF
        """
        results = []
        for file in Path(directory).glob('*.pdf'):
            try:
                result = self.extract_invoice_data(str(file))
                result['filename'] = file.name
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing {file}: {str(e)}")
                results.append({
                    'filename': file.name,
                    'is_valid': False,
                    'errors': [str(e)]
                })
        return results

    def _extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF using both pdfplumber and OCR
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        
        # Try pdfplumber first
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                
        # If no text found, try OCR
        if not text.strip():
            self.logger.info(f"No text extracted with pdfplumber, trying OCR: {file_path}")
            images = convert_from_path(file_path)
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
                
        return text
