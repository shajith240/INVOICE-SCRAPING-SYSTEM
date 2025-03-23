class ProcessingError(Exception):
    """Base exception for document processing errors"""
    def __init__(self, message: str, document_id: str = None):
        self.message = message
        self.document_id = document_id
        super().__init__(self.message)

class ValidationError(ProcessingError):
    """Raised when document validation fails"""
    pass

class ExtractionError(ProcessingError):
    """Raised when data extraction fails"""
    pass

class ClassificationError(ProcessingError):
    """Raised when document classification fails"""
    pass

class CategoryError(ProcessingError):
    """Raised when there's an error in document categorization"""
    pass

class ConfigurationError(Exception):
    """Raised when there's an issue with configuration"""
    pass

class EmailFetchError(Exception):
    """Raised when there's an error fetching emails"""
    pass

class PDFProcessingError(ProcessingError):
    """Raised when there's an error processing PDF documents"""
    pass

__all__ = ['ProcessingError', 'ValidationError', 'ExtractionError', 
           'ClassificationError', 'CategoryError', 'ConfigurationError',
           'EmailFetchError', 'PDFProcessingError']

