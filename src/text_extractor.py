from pathlib import Path
import PyPDF2

class TextExtractor:
    def extract(self, file_path: Path) -> str:
        """Extract text content from a document"""
        if file_path.suffix.lower() == '.pdf':
            return self._extract_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
