from typing import Dict, Optional
import logging

class BaseClassifier:
    """Base class for document classifiers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def classify(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Base classification method
        
        Args:
            text: Document text content
            metadata: Document metadata (optional)
            
        Returns:
            Dictionary containing:
                - category: Predicted document category
                - confidence: Classification confidence score
                - metadata: Additional classification metadata
        """
        self.logger.warning("Using base classifier - no classification logic implemented")
        return {
            "category": "unknown",
            "confidence": 0.0,
            "metadata": metadata or {}
        }

    def validate_result(self, result: Dict) -> bool:
        """
        Validate classification result
        
        Args:
            result: Classification result dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = {"category", "confidence"}
        return all(field in result for field in required_fields)
