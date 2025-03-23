from typing import Dict, List
import logging
from pathlib import Path
from src.exceptions import CategoryError

class DocumentClassifier:
    """Classifies documents based on their content and metadata"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.categories = {
            'invoice': ['invoice', 'bill', 'receipt'],
            'contract': ['contract', 'agreement', 'terms'],
            'report': ['report', 'analysis', 'summary']
        }
    
    def classify(self, text: str, metadata: Dict = None) -> Dict:
        """
        Classify a document based on its content and metadata
        
        Args:
            text: Document text content
            metadata: Document metadata (optional)
            
        Returns:
            Dict: Classification result with category and confidence
        """
        try:
            text = text.lower()
            
            # Check for category-specific keywords
            for category, keywords in self.categories.items():
                if any(keyword in text for keyword in keywords):
                    return {
                        'category': category,
                        'confidence': 0.95
                    }
                    
            # Default category if no matches found
            return {
                'category': 'other',
                'confidence': 0.5
            }
        except Exception as e:
            raise CategoryError(f"Classification failed: {str(e)}")
    
    def get_categories(self) -> List[str]:
        """Get list of supported categories"""
        return list(self.categories.keys()) + ['other']

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



