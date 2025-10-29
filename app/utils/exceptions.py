from typing import Optional

class CustomException(Exception):
    """Base custom exception class"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class DocumentParsingError(CustomException):
    """Exception raised when document parsing fails"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=422, details=details)

class LLMServiceError(CustomException):
    """Exception raised when LLM service fails"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=503, details=details)

class DatabaseError(CustomException):
    """Exception raised when database operations fail"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=500, details=details)

class ValidationError(CustomException):
    """Exception raised when validation fails"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=400, details=details)
