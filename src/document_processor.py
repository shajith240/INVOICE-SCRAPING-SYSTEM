from pathlib import Path
import shutil
import logging
from typing import Dict, Optional, List
from datetime import datetime
import json

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




