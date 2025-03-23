from typing import Dict, Optional
import logging

class BaseExtractor:
    """Base class for document data extractors"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, text_content: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Base extraction method
        
        Args:
            text_content: Text content to extract data from
            metadata: Optional metadata to aid extraction
            
        Returns:
            Dictionary containing extracted fields
        """
        self.logger.warning("Using base extractor - no extraction logic implemented")
        return {
            "raw_text": text_content,
            "metadata": metadata or {}
        }

    def validate_extracted_data(self, data: Dict) -> bool:
        """
        Validate extracted data
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        return isinstance(data, dict) and "raw_text" in data


