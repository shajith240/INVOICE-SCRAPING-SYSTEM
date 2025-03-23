import logging
from pathlib import Path
from typing import Dict
from datetime import datetime

class MetadataExtractor:
    """Extracts metadata from documents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, file_path: Path) -> Dict:
        """
        Extract metadata from document
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dict: Extracted metadata
        """
        file_path = Path(file_path)
        
        metadata = {
            'filename': file_path.name,
            'file_type': file_path.suffix.lower()[1:],
            'file_size': file_path.stat().st_size,
            'created_date': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
            'modified_date': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        if metadata['file_type'] == 'pdf':
            pdf_metadata = self._extract_pdf_metadata(file_path)
            metadata.update(pdf_metadata)
            
        return metadata
        
    def _extract_pdf_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from PDF file"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                info = reader.metadata
                return {
                    'page_count': len(reader.pages),
                    'author': info.get('/Author', ''),
                    'creator': info.get('/Creator', ''),
                    'producer': info.get('/Producer', ''),
                    'subject': info.get('/Subject', ''),
                    'title': info.get('/Title', '')
                }
        except Exception as e:
            self.logger.error(f"Error extracting PDF metadata from {file_path}: {str(e)}")
            return {}