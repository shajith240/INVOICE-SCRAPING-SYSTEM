from typing import Dict, List
import logging
from pathlib import Path
from src.exceptions import CategoryError

class DocumentClassifier:
    """Classifies documents based on their content and metadata"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Updated keyword weights with more precise indicators
        self.invoice_indicators = {
            'invoice': 1.0,
            'bill': 0.8,
            'amount due': 0.8,
            'total due': 0.8,
            'payment': 0.6,
            'invoice number': 0.9,
            'invoice date': 0.9,
            'due date': 0.8
        }
        
        self.currency_symbols = ['$', '€', '£']
        self.currency_codes = ['usd', 'eur', 'gbp']

    def classify(self, text_content: str) -> Dict:
        """Classify document based on text content"""
        if not text_content:
            return {'category': 'other', 'confidence': 0.5}
        
        text_lower = text_content.lower()
        
        # Check for invoice-specific patterns
        has_invoice_word = 'invoice' in text_lower
        has_currency = any(symbol in text_content for symbol in self.currency_symbols) or \
                      any(code in text_lower for code in self.currency_codes)
        
        # Count matching keywords
        matched_keywords = sum(1 for keyword in self.invoice_indicators.keys() 
                             if keyword in text_lower)
        
        # Calculate weighted confidence
        matched_weight = sum(weight for keyword, weight in self.invoice_indicators.items() 
                           if keyword in text_lower)
        base_confidence = matched_weight / sum(self.invoice_indicators.values())
        
        # Determine category and confidence
        if has_invoice_word and has_currency:
            return {'category': 'invoice', 'confidence': min(0.95, base_confidence * 1.5)}
        elif has_invoice_word and matched_keywords >= 2:
            return {'category': 'invoice', 'confidence': min(0.92, base_confidence * 1.3)}
        elif matched_keywords >= 3:
            return {'category': 'invoice', 'confidence': min(0.90, base_confidence * 1.2)}
        elif matched_keywords <= 1 and not has_currency:
            return {'category': 'other', 'confidence': 0.7}
        else:
            return {'category': 'other', 'confidence': 0.7}
    
    def get_categories(self) -> List[str]:
        """Get list of supported categories"""
        return list(self.category_keywords.keys()) + ['other']

    def get_target_path(self, categorization_result: Dict) -> Path:
        """
        Determine target path for document based on classification result
        
        Args:
            categorization_result: Classification result dictionary
        
        Returns:
            Path: Target path for document
        """
        category = categorization_result.get('category', 'other')
        base_path = Path('processed_documents')
        return base_path / category







