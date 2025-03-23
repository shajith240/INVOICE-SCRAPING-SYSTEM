class ProcessingError(Exception):
    """Base exception for document processing errors"""
    pass

class ValidationError(ProcessingError):
    """Raised when document validation fails"""
    pass

class CategoryError(ProcessingError):
    """Raised when document categorization fails"""
    pass

class StorageError(ProcessingError):
    """Raised when file storage operations fail"""
    pass

class ConfigurationError(ProcessingError):
    """Raised when configuration is invalid or missing"""
    pass