from typing import Dict

class DocumentClassifier:
    def classify(self, text_content: str) -> Dict:
        """Classify document based on text content"""
        # Simple keyword-based classification
        text_lower = text_content.lower()
        
        if any(word in text_lower for word in ['invoice', 'bill', 'amount due']):
            return {'category': 'invoice', 'confidence': 0.95}
        elif any(word in text_lower for word in ['receipt', 'paid']):
            return {'category': 'receipt', 'confidence': 0.95}
        else:
            return {'category': 'other', 'confidence': 0.5}