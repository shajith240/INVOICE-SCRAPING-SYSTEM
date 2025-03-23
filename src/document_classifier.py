from typing import Dict
import re
import logging
from pathlib import Path
import json

class DocumentClassifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Load classification rules from config
        self.rules = self._load_classification_rules()
        
    def _load_classification_rules(self) -> Dict:
        """Load classification rules from configuration"""
        rules_path = Path("config/categorization_rules.json")
        try:
            with open(rules_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load rules from {rules_path}: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        """Default classification patterns"""
        return {
            "invoice": {
                "required_patterns": [
                    r"(?i)invoice\s*(?:no|number|#|ref)",  # Invoice reference
                    r"(?i)(?:total|amount|sum|balance).*?(?:\d[\d,.]*)",  # Amount
                ],
                "supporting_patterns": [
                    r"(?i)(?:bill\s*to|billing\s*address)",  # Billing info
                    r"(?i)(?:payment\s*terms|due\s*date)",   # Payment details
                    r"(?i)(?:tax\s*(?:id|number)|vat\s*(?:id|number))",  # Tax references
                    r"(?i)(?:purchase\s*order|po\s*number)",  # PO references
                ],
                "date_patterns": [
                    r"(?i)(?:date|issued|created).*?(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})",
                    r"(?i)(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"
                ]
            }
        }

    def classify(self, text_content: str) -> Dict:
        """
        Classify document based on content analysis
        
        Args:
            text_content: Extracted text from document
            
        Returns:
            Dict containing classification results with confidence scores
        """
        if not text_content or not text_content.strip():
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'indicators': []
            }

        # Normalize text for consistent matching
        normalized_text = ' '.join(text_content.split())
        
        results = []
        for doc_type, patterns in self.rules.items():
            score = self._calculate_match_score(normalized_text, patterns)
            results.append((doc_type, score))
        
        # Sort by confidence score
        results.sort(key=lambda x: x[1]['confidence'], reverse=True)
        best_match = results[0]
        
        return {
            'category': best_match[0],
            'confidence': best_match[1]['confidence'],
            'indicators': best_match[1]['indicators']
        }

    def _calculate_match_score(self, text: str, patterns: Dict) -> Dict:
        """
        Calculate confidence score based on pattern matches
        
        Args:
            text: Normalized document text
            patterns: Dictionary of patterns to match
            
        Returns:
            Dict with confidence score and matched indicators
        """
        required_matches = []
        supporting_matches = []
        
        # Check required patterns
        for pattern in patterns.get('required_patterns', []):
            match = re.search(pattern, text)
            if match:
                required_matches.append({
                    'pattern': pattern,
                    'matched_text': match.group(0)
                })
        
        # Check supporting patterns
        for pattern in patterns.get('supporting_patterns', []):
            match = re.search(pattern, text)
            if match:
                supporting_matches.append({
                    'pattern': pattern,
                    'matched_text': match.group(0)
                })
        
        # Calculate confidence score
        required_weight = 0.6
        supporting_weight = 0.4
        
        if not required_matches:
            return {'confidence': 0.0, 'indicators': []}
        
        required_score = len(required_matches) / len(patterns['required_patterns'])
        supporting_score = (len(supporting_matches) / 
                          len(patterns['supporting_patterns']) if patterns['supporting_patterns'] 
                          else 0)
        
        confidence = (required_score * required_weight + 
                     supporting_score * supporting_weight)
        
        return {
            'confidence': min(confidence, 0.95),  # Cap at 0.95
            'indicators': required_matches + supporting_matches
        }


