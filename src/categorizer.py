import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import spacy
from price_parser import Price

from .exceptions import CategoryError
from .text_extractor import TextExtractor
from .metadata_extractor import MetadataExtractor
from .document_classifier import DocumentClassifier

class DocumentCategorizer:
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.text_extractor = TextExtractor()
        self.logger = logging.getLogger(__name__)

    def categorize(self, file_path: Path, metadata: Optional[Dict] = None) -> Dict:
        """
        Categorize a document and extract relevant data
        
        Args:
            file_path: Path to document file
            metadata: Optional pre-extracted metadata
            
        Returns:
            Dict containing categorization results and extracted data
        """
        try:
            # Extract text content
            text_content = (metadata.get('text') if metadata 
                          else self.text_extractor.extract(file_path))
            
            if not text_content:
                return {
                    'categories': ['unknown'],
                    'confidence': 0.0,
                    'status': 'error',
                    'error': 'No text content extracted'
                }

            # Classify document
            classification = self.classifier.classify(text_content)
            
            result = {
                'categories': [classification['category']],
                'confidence': classification['confidence'],
                'indicators': classification['indicators'],
                'file_path': str(file_path),
                'status': 'processed'
            }

            # Extract additional data if document is an invoice
            if classification['category'] == 'invoice' and classification['confidence'] > 0.5:
                result['extracted_data'] = self._extract_invoice_data(text_content)

            return result

        except Exception as e:
            self.logger.error(f"Categorization failed for {file_path}: {str(e)}")
            return {
                'categories': ['unknown'],
                'confidence': 0.0,
                'status': 'error',
                'error': str(e)
            }

    def get_target_path(self, categorization_result: Dict) -> Path:
        """Determine target path based on categorization result"""
        base_path = Path('processed_documents')
        category = categorization_result['categories'][0]
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Create a more detailed path structure
        target_path = base_path / category / date
        
        # Ensure the directory exists
        target_path.mkdir(parents=True, exist_ok=True)
        
        return target_path

    def _extract_invoice_data(self, text_content: str) -> Dict:
        """
        Extract structured data from invoice text
        
        Args:
            text_content: Extracted text from document
            
        Returns:
            Dict containing extracted invoice fields
        """
        # Load extraction patterns from rules
        patterns = self.classifier.rules.get('invoice', {}).get('data_extraction', {})
        
        extracted_data = {
            'invoice_number': None,
            'date': None,
            'total_amount': None,
            'vendor': None
        }
        
        # Extract data using patterns
        for field, pattern in patterns.items():
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                extracted_data[field] = match.group(1).strip()
        
        # Clean and validate extracted data
        if extracted_data['total_amount']:
            extracted_data['total_amount'] = self._clean_amount(
                extracted_data['total_amount']
            )
        
        return extracted_data

    def _clean_amount(self, amount: str) -> str:
        """Clean and standardize amount strings"""
        amount = re.sub(r'[^\d.,]', '', amount)
        if ',' in amount and '.' in amount:
            if amount.find(',') > amount.find('.'):
                amount = amount.replace('.', '')
                amount = amount.replace(',', '.')
            else:
                amount = amount.replace(',', '')
        elif ',' in amount:
            amount = amount.replace(',', '.')
        return amount

    def _extract_receipt_data(self, text_content: str) -> Dict:
        """Extract receipt-specific data"""
        return {
            'transaction_date': None,
            'total_amount': None,
            'merchant': None,
            'payment_method': None,
            'items': []
        }

    def _extract_contract_data(self, text_content: str) -> Dict:
        """Extract contract-specific data"""
        return {
            'contract_date': None,
            'parties_involved': [],
            'contract_type': None,
            'expiration_date': None
        }

    def _extract_report_data(self, text_content: str) -> Dict:
        """Extract report-specific data"""
        return {
            'report_date': None,
            'report_type': None,
            'author': None,
            'key_findings': []
        }
