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
        self.logger = logging.getLogger(__name__)
        self.text_extractor = TextExtractor()
        self.metadata_extractor = MetadataExtractor()
        self.classifier = DocumentClassifier()
        
        # Define category-specific keywords
        self.categories = {
            'invoice': ['invoice', 'bill', 'payment', 'amount due'],
            'receipt': ['receipt', 'paid', 'payment received'],
            'contract': ['agreement', 'contract', 'terms', 'conditions'],
            'report': ['report', 'analysis', 'summary', 'findings']
        }

    def categorize(self, file_path: Path, metadata: Optional[Dict] = None) -> Dict:
        """Categorize a document based on its content and metadata"""
        try:
            # Use the text from metadata if provided
            text_content = metadata.get('text', '') if metadata else ''
            
            # Simple keyword-based classification
            text_lower = text_content.lower()
            
            # Check for invoice-specific keywords
            if any(keyword in text_lower for keyword in self.categories['invoice']):
                return {
                    'categories': ['invoice'],
                    'confidence': 0.95,
                    'metadata': metadata or {},
                    'file_path': str(file_path),
                    'status': 'processed'
                }
            
            # Check other categories
            for category, keywords in self.categories.items():
                if any(keyword in text_lower for keyword in keywords):
                    return {
                        'categories': [category],
                        'confidence': 0.8,
                        'metadata': metadata or {},
                        'file_path': str(file_path),
                        'status': 'processed'
                    }
            
            # Default category if no matches found
            return {
                'categories': ['other'],
                'confidence': 0.5,
                'metadata': metadata or {},
                'file_path': str(file_path),
                'status': 'processed'
            }
            
        except Exception as e:
            self.logger.error(f"Categorization failed: {str(e)}")
            return {
                'categories': ['unknown'],
                'confidence': 0,
                'error': str(e),
                'metadata': metadata or {},
                'file_path': str(file_path),
                'status': 'error'
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

    def _extract_category_specific_data(self, text_content: str, category: str) -> Dict:
        """Extract data specific to document category"""
        extracted_data = {}
        
        if category == 'invoice':
            extracted_data.update(self._extract_invoice_data(text_content))
        elif category == 'receipt':
            extracted_data.update(self._extract_receipt_data(text_content))
        elif category == 'contract':
            extracted_data.update(self._extract_contract_data(text_content))
        elif category == 'report':
            extracted_data.update(self._extract_report_data(text_content))
        
        return extracted_data

    def _extract_invoice_data(self, text_content: str) -> Dict:
        """Extract invoice-specific data using advanced regex patterns and NLP
        
        Args:
            text_content: Raw text extracted from invoice document
        
        Returns:
            Dictionary containing extracted invoice fields with confidence scores
        """
        import re
        from datetime import datetime
        import spacy
        from price_parser import Price
        
        # Initialize spaCy for better entity recognition
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text_content)
        
        # Initialize results with confidence scores
        results = {
            'invoice_number': {'value': None, 'confidence': 0.0},
            'total_amount': {'value': None, 'confidence': 0.0},
            'due_date': {'value': None, 'confidence': 0.0},
            'issue_date': {'value': None, 'confidence': 0.0},
            'vendor_name': {'value': None, 'confidence': 0.0},
            'billing_address': {'value': None, 'confidence': 0.0},
            'line_items': [],
            'tax_amount': {'value': None, 'confidence': 0.0},
            'currency': {'value': None, 'confidence': 0.0},
            'payment_terms': {'value': None, 'confidence': 0.0}
        }
        
        # Enhanced regex patterns
        patterns = {
            'invoice_number': [
                r'(?i)invoice\s*(?:#|number|num|no)?[:.\s]*([A-Z0-9][-A-Z0-9]*)',
                r'(?i)inv\s*#\s*([A-Z0-9][-A-Z0-9]*)',
                r'(?i)bill\s*number[:.\s]*([A-Z0-9][-A-Z0-9]*)'
            ],
            'total_amount': [
                r'(?i)(?:total|amount|sum|balance)(?:\s*due)?[:.\s]*[$€£¥]?\s*([\d,]+\.?\d*)',
                r'(?i)grand\s+total[:.\s]*[$€£¥]?\s*([\d,]+\.?\d*)',
                r'(?i)amount\s+payable[:.\s]*[$€£¥]?\s*([\d,]+\.?\d*)'
            ],
            'due_date': [
                r'(?i)(?:due|payment)\s*date[:.\s]*((?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}))',
                r'(?i)pay\s*by[:.\s]*((?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}))'
            ],
            'currency': [
                r'(?i)currency[:.\s]*([A-Z]{3})',
                r'([€$£¥])'
            ]
        }
        
        # Extract using multiple patterns
        for field, field_patterns in patterns.items():
            confidence = 0.0
            for pattern in field_patterns:
                match = re.search(pattern, text_content)
                if match:
                    value = match.group(1).strip()
                    current_confidence = self._calculate_confidence(match, text_content)
                    
                    if current_confidence > confidence:
                        confidence = current_confidence
                        
                        # Field-specific processing
                        if field == 'total_amount':
                            price = Price.fromstring(value)
                            results[field] = {
                                'value': price.amount_float,
                                'confidence': confidence
                            }
                            if price.currency:
                                results['currency'] = {
                                    'value': price.currency,
                                    'confidence': confidence
                                }
                        elif field == 'due_date':
                            try:
                                parsed_date = self._parse_date(value)
                                if parsed_date:
                                    results[field] = {
                                        'value': parsed_date,
                                        'confidence': confidence
                                    }
                            except ValueError:
                                continue
                        else:
                            results[field] = {
                                'value': value,
                                'confidence': confidence
                            }
        
        # Extract line items
        results['line_items'] = self._extract_line_items(text_content)
        
        # Extract vendor information using NLP
        for ent in doc.ents:
            if ent.label_ == "ORG" and not results['vendor_name']['value']:
                results['vendor_name'] = {
                    'value': ent.text,
                    'confidence': 0.8
                }
            elif ent.label_ == "GPE" and not results['billing_address']['value']:
                results['billing_address'] = {
                    'value': ent.text,
                    'confidence': 0.7
                }
        
        return results

    def _calculate_confidence(self, match: re.Match, text_content: str) -> float:
        """Calculate confidence score for extracted field"""
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on match position
        if match.start() < len(text_content) / 2:
            confidence += 0.1
            
        # Increase confidence based on surrounding context
        context = text_content[max(0, match.start()-20):min(len(text_content), match.end()+20)]
        if any(keyword in context.lower() for keyword in ['total', 'amount', 'invoice', 'payment']):
            confidence += 0.2
            
        # Increase confidence for well-formatted values
        if match.group(1) and len(match.group(1)) >= 3:
            confidence += 0.1
            
        return min(confidence, 1.0)

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string into standardized format"""
        date_formats = [
            '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d',
            '%d-%m-%y', '%y-%m-%d', '%d/%m/%y', '%y/%m/%d',
            '%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None

    def _extract_line_items(self, text_content: str) -> List[Dict]:
        """Extract line items from invoice text"""
        items = []
        
        # Look for common line item patterns
        line_pattern = r'(?im)^(.*?)\s*(\d+)\s*(?:x|\@)?\s*([\d,]+\.?\d*)\s*([\d,]+\.?\d*)$'
        
        for match in re.finditer(line_pattern, text_content):
            description, quantity, unit_price, total = match.groups()
            
            items.append({
                'description': description.strip(),
                'quantity': float(quantity),
                'unit_price': float(unit_price.replace(',', '')),
                'total': float(total.replace(',', '')),
                'confidence': 0.7
            })
        
        return items

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
