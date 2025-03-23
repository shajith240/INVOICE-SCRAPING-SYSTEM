from pathlib import Path
from typing import Dict, List, Optional
from copy import deepcopy
import logging
from datetime import datetime
import json
from pathlib import Path
import shutil
import logging
from typing import Dict, Optional, List
from datetime import datetime
import json
from copy import deepcopy

from .categorizer import DocumentCategorizer
from .exceptions import ProcessingError

class DocumentProcessor:
    def __init__(self, config: Optional[Dict] = None, config_path: Optional[Path] = None, base_dir: Optional[Path] = None):
        """
        Initialize DocumentProcessor
        
        Args:
            config: Optional configuration dictionary
            config_path: Optional path to configuration file
            base_dir: Optional base directory for processed documents and errors
        """
        if config:
            self.config = config
        else:
            self._load_config(config_path)
        
        self.logger = logging.getLogger(__name__)
        self.categorizer = DocumentCategorizer()
        # Use provided base_dir or default to current directory
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        # Initialize directories as absolute paths
        self.processed_dir = self.base_dir / "processed_documents"
        self.error_dir = self.base_dir / "errors"
        # Create necessary directories
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.error_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/document_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path: Optional[Path] = None):
        """Load processor configuration"""
        if config_path is None:
            config_path = Path('config/processor_config.json')

        try:
            with open(config_path) as f:
                self.config = json.load(f)
        except Exception as e:
            raise ProcessingError(f"Failed to load processor configuration: {str(e)}")

    def process_document(self, file_path: Path, metadata: Optional[Dict] = None) -> Dict:
        """
        Process a single document
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata from email or other sources
            
        Returns:
            Dictionary containing processing results
        """
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            # Validate file
            if not self._validate_file(file_path):
                raise ProcessingError(f"Invalid file: {file_path}")

            # Categorize document
            categorization_result = self.categorizer.categorize(file_path, metadata)
            
            # Determine target location
            target_path = self.get_target_path(categorization_result)
            
            # Create target directory if it doesn't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            final_path = self._generate_unique_path(target_path, file_path)
            
            # Move file to target location
            self._move_file(file_path, final_path)
            
            # Update result with final path
            categorization_result['final_path'] = str(final_path)
            
            # Save processing record
            self._save_processing_record(categorization_result)
            
            self.logger.info(f"Document processed successfully: {final_path}")
            return categorization_result

        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {str(e)}")
            self._handle_processing_error(file_path, str(e))
            raise

    def process_batch(self, directory: Path) -> List[Dict]:
        """Process all documents in a directory"""
        results = []
        for file_path in self._get_processable_files(directory):
            try:
                result = self.process_document(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {str(e)}")
                self._handle_processing_error(file_path, str(e))
                continue
        return results

    def _validate_file(self, file_path: Path) -> bool:
        """
        Validate file before processing
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        # Check if file exists
        if not file_path.exists():
            return False
            
        # Check file extension
        if file_path.suffix.lower() not in self.config['supported_extensions']:
            return False
            
        # Check file size
        max_size = self.config['max_file_size_mb'] * 1024 * 1024  # Convert to bytes
        if file_path.stat().st_size > max_size:
            return False
            
        return True

    def _generate_unique_path(self, target_dir: Path, original_file: Path) -> Path:
        """Generate unique file path in target directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{original_file.stem}_{timestamp}{original_file.suffix}"
        return target_dir / new_filename

    def _move_file(self, source: Path, destination: Path):
        """Move file to target location"""
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
        except Exception as e:
            raise ProcessingError(f"Failed to move file to {destination}: {str(e)}")

    def _save_processing_record(self, result: Dict):
        """Save processing record to database or file"""
        record_path = Path(self.config['processing_records_path'])
        record_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        record_file = record_path / f"processing_record_{timestamp}.json"
        
        try:
            # Load existing records
            if record_file.exists():
                with open(record_file) as f:
                    records = json.load(f)
            else:
                records = []
            
            # Add new record
            records.append({
                'timestamp': datetime.now().isoformat(),
                **result
            })
            
            # Save updated records
            with open(record_file, 'w') as f:
                json.dump(records, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save processing record: {str(e)}")

    def _handle_processing_error(self, file_path: Path, error_message: str):
        """Handle processing errors"""
        error_dir = Path(self.config['error_directory'])
        error_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file to error directory
        error_path = error_dir / file_path.name
        try:
            shutil.move(str(file_path), str(error_path))
        except Exception as e:
            self.logger.error(f"Failed to move file to error directory: {str(e)}")
        
        # Log error details
        error_log = error_dir / 'processing_errors.log'
        try:
            with open(error_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()}: {file_path} - {error_message}\n")
        except Exception as e:
            self.logger.error(f"Failed to write to error log: {str(e)}")

    def _get_processable_files(self, directory: Path) -> List[Path]:
        """Get list of processable files in directory"""
        files = []
        for ext in self.config['supported_extensions']:
            files.extend(directory.glob(f"*{ext}"))
        return files

    def get_target_path(self, categorization_result: Dict) -> Path:
        """Determine target path based on categorization result"""
        category = categorization_result['categories'][0]
        date = datetime.now().strftime('%Y-%m-%d')
        # Use absolute path
        return self.processed_dir / category / date

    def apply(self, file_path: Path, metadata: Optional[Dict] = None) -> Dict:
        """
        Apply document processing while preserving all indicators and metadata
        
        Args:
            file_path: Path to the document
            metadata: Optional metadata dictionary
            
        Returns:
            Dict containing processed results with all indicators preserved
        """
        try:
            # Load and validate document
            doc = self._load_document(file_path)
            
            # Create deep copy of original metadata to preserve all indicators
            preserved_metadata = deepcopy(metadata) if metadata else {}
            
            # Extract text while preserving formatting and structure
            extracted_text = self._extract_text_with_formatting(doc)
            
            # Process document while maintaining all indicators
            processed_result = {
                'text': extracted_text,
                'original_metadata': preserved_metadata,
                'indicators': self._extract_indicators(doc),
                'file_path': str(file_path),
                'status': 'processed',
                'modifications': []
            }
            
            # Apply necessary transformations while preserving context
            processed_result.update(self._apply_transformations(doc))
            
            # Validate the processed result maintains all required information
            self._validate_processed_result(processed_result)
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Processing failed for {file_path}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'file_path': str(file_path)
            }

    def _extract_indicators(self, doc) -> Dict:
        """Extract all relevant indicators from the document"""
        indicators = {
            'invoice_related': [],
            'dates': [],
            'amounts': [],
            'reference_numbers': [],
            'custom_fields': []
        }
        
        # Extract and preserve all indicators
        for page in doc.pages:
            page_content = page.extract_text()
            
            # Preserve invoice-related indicators
            indicators['invoice_related'].extend(
                self._find_invoice_indicators(page_content)
            )
            
            # Preserve dates
            indicators['dates'].extend(
                self._extract_dates(page_content)
            )
            
            # Preserve amounts and currency information
            indicators['amounts'].extend(
                self._extract_amounts(page_content)
            )
            
            # Preserve reference numbers
            indicators['reference_numbers'].extend(
                self._extract_references(page_content)
            )
            
            # Preserve any custom fields
            indicators['custom_fields'].extend(
                self._extract_custom_fields(page_content)
            )
            
        return indicators

    def _validate_processed_result(self, result: Dict) -> None:
        """Ensure all important indicators are preserved in the result"""
        required_keys = {'text', 'indicators', 'status'}
        if not all(key in result for key in required_keys):
            raise ValueError("Processed result missing required information")
            
        if not result['indicators']:
            self.logger.warning("No indicators found in processed document")

    def _extract_text_with_formatting(self, doc) -> str:
        """Extract text while preserving formatting and structure"""
        formatted_text = []
        for page in doc.pages:
            # Extract text with position information
            elements = page.extract_text_with_formatting()
            
            # Preserve layout and structure
            formatted_text.extend(self._preserve_layout(elements))
            
        return '\n'.join(formatted_text)

    def _preserve_layout(self, elements: List) -> List[str]:
        """Preserve document layout and structure"""
        # Sort elements by position to maintain layout
        sorted_elements = sorted(elements, key=lambda x: (-x['top'], x['left']))
        
        # Group elements by lines while preserving structure
        lines = self._group_elements_by_line(sorted_elements)
        
        return [' '.join(line) for line in lines]






