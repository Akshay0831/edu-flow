from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(HTTPException):
    """Custom validation error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(HTTPException):
    """Custom not found error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedError(HTTPException):
    """Custom unauthorized error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(HTTPException):
    """Custom validation error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(HTTPException):
    """Custom not found error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code=status_code, detail=detail)


class ForbiddenError(HTTPException):
    """Custom forbidden error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=status_code, detail=detail)


class ConflictError(HTTPException):
    """Custom conflict error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code=status_code, detail=detail)


class InternalServerError(HTTPException):
    """Custom internal server error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class DatabaseError(Exception):
    """Database operation error"""
    pass


class ExternalServiceError(Exception):
    """External service integration error"""
    pass


class ConfigurationError(Exception):
    """Configuration error"""
    pass


class RateLimitError(HTTPException):
    """Rate limiting error"""
    
    def __init__(self, detail: str = "Rate limit exceeded", status_code: int = status.HTTP_429_TOO_MANY_REQUESTS):
        super().__init__(status_code=status_code, detail=detail)


class ProcessingError(Exception):
    """Data processing error"""
    pass


class FileProcessingError(ProcessingError):
    """File processing error"""
    pass


class CalculationError(Exception):
    """Calculation error"""
    pass


class DataValidationError(Exception):
    """Data validation error"""
    pass