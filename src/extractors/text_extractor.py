import logging
from pathlib import Path
from typing import Optional
import PyPDF2
from ..exceptions import CategoryError

class TextExtractor:
    """Extracts text content from documents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, file_path: Path) -> str:
        """Extract text from document"""
        try:
            # Replace the placeholder with actual PDF text extraction
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise CategoryError(f"Text extraction failed: {str(e)}")

