from pathlib import Path
import loggingfrom typing import Dict, Optional, List
import jsonfrom datetime import datetime
from .exceptions import CategoryError
from .extractors import TextExtractor, MetadataExtractorfrom .classifiers import DocumentClassifier
class DocumentCategorizer:
    """Handles document classification and data extraction"""    
    def __init__(self):        self._setup_logging()
        self.text_extractor = TextExtractor()        self.metadata_extractor = MetadataExtractor()
        self.classifier = DocumentClassifier()        
    def _setup_logging(self):        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
    def categorize(self, file_path: Path, metadata: Optional[Dict] = None) -> Dict:        """
        Categorize document and extract relevant data        
        Args:            file_path: Path to the document file
            metadata: Optional metadata from email or other sources            
        Returns:            Dictionary containing categorization results and extracted data
        """        try:
            self.logger.info(f"Categorizing document: {file_path}")            
            # Extract text content            text_content = self.text_extractor.extract(file_path)
                        # Extract document metadata
            doc_metadata = self.metadata_extractor.extract(file_path)            
            # Combine with provided metadata            if metadata:
                doc_metadata.update(metadata)            
            # Classify document            classification = self.classifier.classify(text_content, doc_metadata)
                        # Extract data based on document type
            extracted_data = self._extract_type_specific_data(                text_content, 
                classification['category'],                doc_metadata
            )            
            result = {                'categories': [classification['category']],
                'confidence': classification['confidence'],                'metadata': doc_metadata,
                'extracted_data': extracted_data,                'processing_date': datetime.now().isoformat()
            }            
            self.logger.info(f"Document categorized as {classification['category']} "                           f"with confidence {classification['confidence']}")
                        return result
                    except Exception as e:
            self.logger.error(f"Error categorizing document {file_path}: {str(e)}")            raise CategoryError(f"Failed to categorize document: {str(e)}")
    def _extract_type_specific_data(
        self,         text_content: str, 
        category: str,        metadata: Dict
    ) -> Dict:        """
        Extract data specific to document category        
        Args:            text_content: Extracted text from document
            category: Document category            metadata: Document metadata
                    Returns:
            Dictionary containing extracted data fields        """
        try:            # Get extractor for document category
            extractor = self._get_category_extractor(category)            
            # Extract data using appropriate extractor            extracted_data = extractor.extract(text_content, metadata)
                        # Validate extracted data
            self._validate_extracted_data(extracted_data, category)            
            return extracted_data            
        except Exception as e:            self.logger.error(f"Error extracting data for category {category}: {str(e)}")
            return {}
    def _get_category_extractor(self, category: str):        """Get appropriate data extractor for document category"""
        # Import extractors dynamically based on category        try:
            extractor_module = __import__(                f'src.extractors.{category}_extractor',
                fromlist=['Extractor']            )
            return extractor_module.Extractor()        except ImportError:
            self.logger.warning(f"No specific extractor found for category: {category}")            # Return default extractor
            from .extractors.base_extractor import BaseExtractor            return BaseExtractor()
    def _validate_extracted_data(self, data: Dict, category: str):
        """Validate extracted data against category schema"""        try:
            # Load schema for category            schema_path = Path(f'schemas/{category}_schema.json')
            if not schema_path.exists():                self.logger.warning(f"No validation schema found for category: {category}")
                return                
            with open(schema_path) as f:                schema = json.load(f)
                            # TODO: Implement schema validation
            # For now, just log the validation attempt            self.logger.debug(f"Validated data against schema for category: {category}")
                    except Exception as e:
            self.logger.error(f"Error validating extracted data: {str(e)}")
    def get_target_path(self, categorization_result: Dict) -> Path:        """
        Determine target path for document based on categorization        
        Args:            categorization_result: Result from categorize() method
                    Returns:
            Path where document should be stored        """
        try:            category = categorization_result['categories'][0]
            date = datetime.now().strftime("%Y/%m/%d")            
            # Build path based on category and date            base_path = Path('data/processed')
            target_path = base_path / category / date            
            # Add subcategory if available            if len(categorization_result['categories']) > 1:
                target_path = target_path / categorization_result['categories'][1]            
            return target_path            
        except Exception as e:            self.logger.error(f"Error determining target path: {str(e)}")
            # Return default path
            return Path('data/processed/uncategorized')





















































































